from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import os
from datetime import datetime, timedelta
import json
import logging
import hashlib
import secrets
import re
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立FastAPI應用程式
app = FastAPI(
    title="微藻養殖Excel資料收集API (安全版)",
    description="用於收集和管理Excel檔案資料的安全API系統",
    version="2.0.0"
)

# 安全設定
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))  # 每小時請求數
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1小時

# 添加安全中介軟體
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS
)

# CORS設定（限制來源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# 資料庫設定
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./microalgae_data.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 資料庫模型
class ExcelData(Base):
    __tablename__ = "excel_data"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    sheet_name = Column(String)
    row_number = Column(Integer)
    column_name = Column(String)
    cell_value = Column(Text)
    data_type = Column(String)
    upload_time = Column(DateTime, default=datetime.utcnow)
    file_hash = Column(String, index=True)
    user_ip = Column(String)  # 記錄用戶IP

class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_size = Column(Integer)
    upload_time = Column(DateTime, default=datetime.utcnow)
    file_hash = Column(String, unique=True, index=True)
    status = Column(String, default="uploaded")
    error_message = Column(Text, nullable=True)
    user_ip = Column(String)  # 記錄用戶IP

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String, unique=True, index=True)
    user_ip = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    request_count = Column(Integer, default=0)
    is_active = Column(String, default="active")

# 建立資料表
Base.metadata.create_all(bind=engine)

# Pydantic模型
class ExcelDataResponse(BaseModel):
    id: int
    filename: str
    sheet_name: str
    row_number: int
    column_name: str
    cell_value: str
    data_type: str
    upload_time: datetime
    
    model_config = {"from_attributes": True}

class FileUploadResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    upload_time: datetime
    file_hash: str
    status: str
    error_message: Optional[str] = None
    
    model_config = {"from_attributes": True}

class DataQuery(BaseModel):
    filename: Optional[str] = None
    sheet_name: Optional[str] = None
    column_name: Optional[str] = None
    data_type: Optional[str] = None
    limit: int = 100
    offset: int = 0

# 依賴注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 安全設定
security = HTTPBearer()

# 速率限制檢查
def check_rate_limit(request: Request, db: Session):
    client_ip = request.client.host
    current_time = datetime.utcnow()
    
    # 檢查或建立會話
    session = db.query(UserSession).filter(
        UserSession.user_ip == client_ip,
        UserSession.is_active == "active"
    ).first()
    
    if not session:
        # 建立新會話
        session_token = secrets.token_urlsafe(32)
        session = UserSession(
            session_token=session_token,
            user_ip=client_ip,
            created_at=current_time,
            last_activity=current_time,
            request_count=1
        )
        db.add(session)
        db.commit()
    else:
        # 檢查速率限制
        if session.request_count >= RATE_LIMIT_REQUESTS:
            time_diff = current_time - session.last_activity
            if time_diff.total_seconds() < RATE_LIMIT_WINDOW:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="請求過於頻繁，請稍後再試"
                )
            else:
                # 重置計數器
                session.request_count = 1
                session.last_activity = current_time
        else:
            session.request_count += 1
            session.last_activity = current_time
        
        db.commit()
    
    return session

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    # 從環境變數取得API金鑰
    api_key = os.getenv("API_KEY", "your-api-key-here")
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的API金鑰",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# 檔案安全檢查
def validate_file(file: UploadFile):
    # 檢查檔案名稱
    if not file.filename:
        raise HTTPException(status_code=400, detail="檔案名稱不能為空")
    
    # 檢查檔案副檔名
    allowed_extensions = ['.xlsx', '.xls']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支援的檔案格式。只支援: {', '.join(allowed_extensions)}"
        )
    
    # 檢查檔案名稱安全性
    if not re.match(r'^[a-zA-Z0-9._-]+$', file.filename):
        raise HTTPException(
            status_code=400, 
            detail="檔案名稱包含不安全的字符"
        )
    
    return True

# 工具函數
def calculate_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def sanitize_filename(filename: str) -> str:
    """清理檔案名稱，移除不安全字符"""
    # 移除路徑分隔符和特殊字符
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # 限制長度
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    return filename

def process_excel_file(file_content: bytes, filename: str, db: Session, user_ip: str) -> Dict[str, Any]:
    """處理Excel檔案並儲存到資料庫"""
    try:
        # 檢查檔案大小
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"檔案大小超過限制 ({MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
            )
        
        # 清理檔案名稱
        safe_filename = sanitize_filename(filename)
        
        # 讀取Excel檔案
        excel_file = pd.ExcelFile(io.BytesIO(file_content))
        
        # 計算檔案雜湊值
        file_hash = calculate_file_hash(file_content)
        
        # 檢查檔案是否已經上傳過
        existing_file = db.query(FileUpload).filter(FileUpload.file_hash == file_hash).first()
        if existing_file:
            return {
                "status": "duplicate",
                "message": "檔案已經上傳過",
                "file_id": existing_file.id
            }
        
        # 建立檔案上傳記錄
        file_upload = FileUpload(
            filename=safe_filename,
            file_size=len(file_content),
            file_hash=file_hash,
            status="processing",
            user_ip=user_ip
        )
        db.add(file_upload)
        db.flush()
        
        total_rows = 0
        
        # 處理每個工作表
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # 限制處理的行數（防止記憶體溢出）
                max_rows = 10000
                if len(df) > max_rows:
                    df = df.head(max_rows)
                    logger.warning(f"工作表 {sheet_name} 超過 {max_rows} 行，只處理前 {max_rows} 行")
                
                # 處理每一行資料
                for row_idx, row in df.iterrows():
                    for col_name, cell_value in row.items():
                        if pd.notna(cell_value):  # 只儲存非空值
                            # 限制儲存格值長度
                            cell_str = str(cell_value)
                            if len(cell_str) > 1000:
                                cell_str = cell_str[:1000] + "..."
                            
                            excel_data = ExcelData(
                                filename=safe_filename,
                                sheet_name=sheet_name,
                                row_number=row_idx + 1,
                                column_name=str(col_name),
                                cell_value=cell_str,
                                data_type=str(type(cell_value).__name__),
                                file_hash=file_hash,
                                user_ip=user_ip
                            )
                            db.add(excel_data)
                            total_rows += 1
                            
            except Exception as e:
                logger.error(f"處理工作表 {sheet_name} 時發生錯誤: {str(e)}")
                continue
        
        # 更新檔案狀態
        file_upload.status = "completed"
        db.commit()
        
        return {
            "status": "success",
            "message": f"成功處理檔案，共儲存 {total_rows} 筆資料",
            "file_id": file_upload.id,
            "total_rows": total_rows,
            "sheets": excel_file.sheet_names
        }
        
    except Exception as e:
        logger.error(f"處理檔案時發生錯誤: {str(e)}")
        if 'file_upload' in locals():
            file_upload.status = "error"
            file_upload.error_message = str(e)
            db.commit()
        
        raise HTTPException(
            status_code=400,
            detail=f"處理檔案時發生錯誤: {str(e)}"
        )

# API端點
@app.get("/")
async def root():
    return {
        "message": "微藻養殖Excel資料收集API (安全版)",
        "version": "2.0.0",
        "security": "enhanced",
        "endpoints": {
            "upload": "/upload/",
            "data": "/data/",
            "files": "/files/",
            "health": "/health/"
        }
    }

@app.get("/health/")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow(),
        "security": "enabled"
    }

@app.post("/upload/", response_model=Dict[str, Any])
async def upload_excel_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
    session: UserSession = Depends(check_rate_limit)
):
    """上傳Excel檔案並處理資料（安全版）"""
    
    # 檔案安全檢查
    validate_file(file)
    
    # 讀取檔案內容
    content = await file.read()
    
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="檔案為空"
        )
    
    # 取得用戶IP
    user_ip = request.client.host
    
    # 處理檔案
    result = process_excel_file(content, file.filename, db, user_ip)
    
    return result

@app.get("/data/", response_model=List[ExcelDataResponse])
async def get_data(
    request: Request,
    query: DataQuery = Depends(),
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
    session: UserSession = Depends(check_rate_limit)
):
    """查詢Excel資料（安全版）"""
    
    query_obj = db.query(ExcelData)
    
    # 應用篩選條件
    if query.filename:
        query_obj = query_obj.filter(ExcelData.filename.contains(query.filename))
    if query.sheet_name:
        query_obj = query_obj.filter(ExcelData.sheet_name.contains(query.sheet_name))
    if query.column_name:
        query_obj = query_obj.filter(ExcelData.column_name.contains(query.column_name))
    if query.data_type:
        query_obj = query_obj.filter(ExcelData.data_type == query.data_type)
    
    # 分頁
    data = query_obj.offset(query.offset).limit(query.limit).all()
    
    return data

@app.get("/data/stats/")
async def get_data_stats(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
    session: UserSession = Depends(check_rate_limit)
):
    """取得資料統計資訊（安全版）"""
    
    total_records = db.query(ExcelData).count()
    total_files = db.query(FileUpload).count()
    
    # 按檔案分組統計
    file_stats = db.query(
        ExcelData.filename,
        db.func.count(ExcelData.id).label('record_count')
    ).group_by(ExcelData.filename).all()
    
    # 按工作表分組統計
    sheet_stats = db.query(
        ExcelData.sheet_name,
        db.func.count(ExcelData.id).label('record_count')
    ).group_by(ExcelData.sheet_name).all()
    
    return {
        "total_records": total_records,
        "total_files": total_files,
        "file_statistics": [{"filename": f[0], "record_count": f[1]} for f in file_stats],
        "sheet_statistics": [{"sheet_name": s[0], "record_count": s[1]} for s in sheet_stats],
        "security_info": {
            "rate_limit": f"{RATE_LIMIT_REQUESTS} requests per hour",
            "max_file_size": f"{MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        }
    }

@app.get("/files/", response_model=List[FileUploadResponse])
async def get_uploaded_files(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
    session: UserSession = Depends(check_rate_limit)
):
    """取得已上傳的檔案列表（安全版）"""
    
    files = db.query(FileUpload).order_by(FileUpload.upload_time.desc()).all()
    return files

@app.delete("/files/{file_id}/")
async def delete_file(
    file_id: int,
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
    session: UserSession = Depends(check_rate_limit)
):
    """刪除檔案及其相關資料（安全版）"""
    
    # 刪除相關的Excel資料
    db.query(ExcelData).filter(ExcelData.file_hash == 
        db.query(FileUpload.file_hash).filter(FileUpload.id == file_id).scalar()
    ).delete()
    
    # 刪除檔案記錄
    file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
    if not file_upload:
        raise HTTPException(status_code=404, detail="檔案不存在")
    
    db.delete(file_upload)
    db.commit()
    
    return {"message": "檔案及相關資料已刪除"}

@app.get("/data/export/")
async def export_data(
    request: Request,
    filename: Optional[str] = None,
    sheet_name: Optional[str] = None,
    format: str = "json",
    db: Session = Depends(get_db),
    token: str = Depends(verify_token),
    session: UserSession = Depends(check_rate_limit)
):
    """匯出資料（安全版）"""
    
    query_obj = db.query(ExcelData)
    
    if filename:
        query_obj = query_obj.filter(ExcelData.filename.contains(filename))
    if sheet_name:
        query_obj = query_obj.filter(ExcelData.sheet_name.contains(sheet_name))
    
    data = query_obj.all()
    
    if format == "json":
        return {
            "data": [
                {
                    "filename": d.filename,
                    "sheet_name": d.sheet_name,
                    "row_number": d.row_number,
                    "column_name": d.column_name,
                    "cell_value": d.cell_value,
                    "data_type": d.data_type,
                    "upload_time": d.upload_time.isoformat()
                }
                for d in data
            ]
        }
    else:
        raise HTTPException(status_code=400, detail="不支援的匯出格式")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

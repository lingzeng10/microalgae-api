"""
Render部署用的簡化API
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
from typing import List, Optional
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建FastAPI應用程式
app = FastAPI(
    title="微藻養殖數據收集API",
    description="用於收集和處理微藻養殖相關的Excel數據",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全設定
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """簡單的API金鑰驗證"""
    api_key = os.getenv("API_KEY", "your-api-key-here")
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的API金鑰",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "微藻養殖數據收集API",
        "version": "1.0.0",
        "status": "運行中"
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "message": "API運行正常"}

@app.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    token: str = Depends(verify_token)
):
    """上傳Excel檔案"""
    try:
        # 檢查檔案類型
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="只支援Excel檔案 (.xlsx, .xls)"
            )
        
        # 讀取檔案內容
        contents = await file.read()
        
        # 使用pandas讀取Excel
        try:
            df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"無法讀取Excel檔案: {str(e)}"
            )
        
        # 處理數據
        result = {
            "filename": file.filename,
            "rows": len(df),
            "columns": list(df.columns),
            "data_preview": df.head().to_dict('records') if len(df) > 0 else []
        }
        
        logger.info(f"成功處理檔案: {file.filename}, 行數: {len(df)}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"處理檔案時發生錯誤: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"處理檔案時發生錯誤: {str(e)}"
        )

@app.get("/data")
async def get_data(token: str = Depends(verify_token)):
    """獲取數據（示例）"""
    return {
        "message": "數據獲取功能",
        "data": "這裡會顯示收集到的數據"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "simple_render_app:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

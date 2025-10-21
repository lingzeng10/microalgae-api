"""
Render部署用的簡化API
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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
    # 更寬鬆的驗證：允許預設金鑰或環境變數
    if credentials.credentials not in [api_key, "your-api-key-here"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的API金鑰",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

@app.get("/", response_class=HTMLResponse)
async def root():
    """根路徑 - 顯示上傳介面"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微藻養殖數據上傳</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        
        .header {
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 15px;
            padding: 40px;
            margin: 30px 0;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: #667eea;
            background-color: #f8f9ff;
        }
        
        .upload-area.dragover {
            border-color: #667eea;
            background-color: #f0f4ff;
        }
        
        .upload-icon {
            font-size: 3em;
            color: #667eea;
            margin-bottom: 20px;
        }
        
        .upload-text {
            font-size: 1.2em;
            color: #333;
            margin-bottom: 10px;
        }
        
        .upload-hint {
            color: #999;
            font-size: 0.9em;
        }
        
        .file-input {
            display: none;
        }
        
        .upload-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 20px 0;
        }
        
        .upload-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .upload-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .api-key-section {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .api-key-section h3 {
            color: #856404;
            margin-bottom: 10px;
        }
        
        .api-key-section input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }
        
        .result {
            margin-top: 30px;
            padding: 20px;
            border-radius: 10px;
            display: none;
        }
        
        .result.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        
        .result.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        
        .file-info {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            text-align: left;
        }
        
        .file-info h3 {
            color: #333;
            margin-bottom: 15px;
        }
        
        .file-info p {
            margin: 5px 0;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌱 微藻養殖數據上傳</h1>
            <p>請上傳您的Excel檔案進行數據處理</p>
        </div>
        
        <div class="api-key-section">
            <h3>🔑 API金鑰設定</h3>
            <input type="text" id="apiKey" placeholder="請輸入API金鑰" value="your-api-key-here">
        </div>
        
        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📁</div>
            <div class="upload-text">點擊選擇檔案或拖拽檔案到此處</div>
            <div class="upload-hint">支援 .xlsx 和 .xls 格式</div>
            <input type="file" id="fileInput" class="file-input" accept=".xlsx,.xls">
        </div>
        
        <button class="upload-btn" id="uploadBtn" disabled>上傳檔案</button>
        
        <div class="result" id="result"></div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const result = document.getElementById('result');
        const apiKeyInput = document.getElementById('apiKey');
        
        let selectedFile = null;
        
        // 點擊上傳區域選擇檔案
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        // 檔案選擇
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                selectedFile = e.target.files[0];
                updateUploadArea();
                uploadBtn.disabled = false;
            }
        });
        
        // 拖拽功能
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            if (e.dataTransfer.files.length > 0) {
                selectedFile = e.dataTransfer.files[0];
                fileInput.files = e.dataTransfer.files;
                updateUploadArea();
                uploadBtn.disabled = false;
            }
        });
        
        // 更新上傳區域顯示
        function updateUploadArea() {
            if (selectedFile) {
                uploadArea.innerHTML = `
                    <div class="upload-icon">✅</div>
                    <div class="upload-text">已選擇檔案：${selectedFile.name}</div>
                    <div class="upload-hint">點擊重新選擇</div>
                `;
            }
        }
        
        // 上傳檔案
        uploadBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            
            const apiKey = apiKeyInput.value.trim();
            if (!apiKey) {
                showResult('請輸入API金鑰', 'error');
                return;
            }
            
            uploadBtn.disabled = true;
            result.style.display = 'none';
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            try {
                const response = await fetch('/upload-excel', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${apiKey}`
                    },
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    showResult(data, 'success');
                } else {
                    const error = await response.json();
                    showResult(`上傳失敗：${error.detail || '未知錯誤'}`, 'error');
                }
            } catch (error) {
                showResult(`上傳失敗：${error.message}`, 'error');
            } finally {
                uploadBtn.disabled = false;
            }
        });
        
        // 顯示結果
        function showResult(data, type) {
            result.className = `result ${type}`;
            result.style.display = 'block';
            
            if (type === 'success') {
                let content = `
                    <h3>✅ 上傳成功！</h3>
                    <div class="file-info">
                        <h3>檔案資訊</h3>
                        <p><strong>檔案名稱：</strong>${data.filename || '未知'}</p>
                        <p><strong>檔案大小：</strong>${data.file_size || '未知'} bytes</p>
                        <p><strong>檔案類型：</strong>${data.file_type || 'Excel檔案'}</p>
                        <p><strong>狀態：</strong>${data.status || '成功'}</p>
                        <p><strong>訊息：</strong>${data.message || '檔案上傳成功'}</p>
                `;
                
                // 如果有pandas數據，顯示詳細資訊
                if (data.rows !== undefined && data.columns !== undefined) {
                    content += `
                        <p><strong>資料行數：</strong>${data.rows}</p>
                        <p><strong>欄位數量：</strong>${data.columns.length}</p>
                        <p><strong>欄位名稱：</strong>${data.columns.join(', ')}</p>
                    `;
                }
                
                // 如果有pandas錯誤，顯示錯誤
                if (data.pandas_error) {
                    content += `
                        <p><strong>Excel解析錯誤：</strong>${data.pandas_error}</p>
                    `;
                }
                
                content += `</div>`;
                
                // 如果有數據預覽，顯示預覽
                if (data.data_preview && data.data_preview.length > 0) {
                    content += `
                        <div class="file-info">
                            <h3>資料預覽</h3>
                            <pre>${JSON.stringify(data.data_preview, null, 2)}</pre>
                        </div>
                    `;
                }
                
                result.innerHTML = content;
            } else {
                result.innerHTML = `
                    <h3>❌ 上傳失敗</h3>
                    <p>${data}</p>
                `;
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

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
        
        # 返回完整檔案資訊（包含pandas處理）
        result = {
            "filename": file.filename,
            "file_size": len(contents),
            "message": "檔案上傳成功！",
            "status": "success",
            "upload_time": "2024-01-01 12:00:00",
            "file_type": "Excel檔案",
            "rows": 0,
            "columns": [],
            "data_preview": []
        }
        
        # 嘗試使用pandas讀取Excel（更穩定的方式）
        try:
            # 使用更安全的pandas設定
            df = pd.read_excel(
                io.BytesIO(contents),
                engine='openpyxl',  # 明確指定引擎
                nrows=1000,  # 限制讀取行數
                na_values=['', 'NULL', 'null', 'NaN', 'nan']  # 處理空值
            )
            
            # 安全地處理數據
            if df is not None and not df.empty:
                result.update({
                    "rows": len(df),
                    "columns": [str(col) for col in df.columns],  # 確保列名是字串
                    "data_preview": df.head(5).fillna('').to_dict('records')  # 限制預覽行數
                })
            else:
                result["pandas_error"] = "Excel檔案為空或無法讀取"
                result["message"] = "檔案上傳成功，但Excel內容為空"
                
        except Exception as e:
            # 如果pandas處理失敗，保持基本資訊
            result["pandas_error"] = f"Excel解析失敗: {str(e)}"
            result["message"] = "檔案上傳成功，但Excel解析失敗"
        
        logger.info(f"成功處理檔案: {file.filename}, 大小: {len(contents)} bytes")
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

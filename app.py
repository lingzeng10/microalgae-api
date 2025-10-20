"""
Render部署用的主應用程式檔案
"""

import os
import uvicorn
from secure_main import app

if __name__ == "__main__":
    # 從環境變數取得端口，Render會自動設定
    port = int(os.getenv("PORT", 8000))
    
    # 啟動應用程式
    uvicorn.run(
        "secure_main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

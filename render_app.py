"""
Render部署用的簡化啟動檔案
"""

import os
import uvicorn

# 直接導入並啟動應用程式
if __name__ == "__main__":
    # 從環境變數取得端口
    port = int(os.getenv("PORT", 8000))
    
    # 直接啟動FastAPI應用程式
    uvicorn.run(
        "secure_main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )

# 微藻養殖Excel資料收集API

## 🚀 快速開始

### 本地運行
```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動API
python app.py
```

### 部署到Render
1. 將此專案推送到GitHub
2. 在Render中建立Web Service
3. 設定環境變數
4. 部署

詳細說明請參考 `RENDER_DEPLOYMENT.md`

## 📋 功能特色

- ✅ Excel檔案上傳（.xlsx, .xls）
- ✅ 資料查詢和管理
- ✅ 統計資訊
- ✅ 安全認證
- ✅ 速率限制
- ✅ 網頁介面

## 🔧 API端點

- `GET /` - API基本資訊
- `POST /upload/` - 上傳Excel檔案
- `GET /data/` - 查詢資料
- `GET /stats/` - 統計資訊
- `GET /docs` - API文件

## 🛡️ 安全功能

- API金鑰認證
- 速率限制
- 檔案安全檢查
- 輸入驗證
- 安全日誌

## 📞 技術支援

如有問題，請檢查：
1. 環境變數設定
2. 依賴套件安裝
3. 檔案格式支援
4. 網路連線狀態

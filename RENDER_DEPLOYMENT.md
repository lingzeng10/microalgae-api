# 🚀 Render部署完整指南

## 📋 部署前準備

### 1. 確保檔案完整
您的專案目錄應該包含以下檔案：
- ✅ `secure_main.py` - 安全版API
- ✅ `app.py` - Render啟動檔案
- ✅ `requirements.txt` - 依賴套件
- ✅ `render.yaml` - Render配置
- ✅ `index.html` - 網頁介面

### 2. 生成安全API金鑰
```bash
python -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))"
```

## 🌐 部署到Render

### 步驟1：建立GitHub儲存庫

1. **建立新儲存庫**
   - 前往 [GitHub](https://github.com)
   - 點擊 "New repository"
   - 命名為 `microalgae-api`
   - 設為公開或私有

2. **上傳檔案**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/your-username/microalgae-api.git
   git push -u origin main
   ```

### 步驟2：在Render建立服務

1. **註冊Render帳號**
   - 前往 [render.com](https://render.com)
   - 使用GitHub帳號註冊

2. **建立Web Service**
   - 點擊 "New +" → "Web Service"
   - 連接您的GitHub儲存庫
   - 選擇 `microalgae-api` 專案

3. **設定服務參數**
   ```
   Name: microalgae-api
   Environment: Python 3
   Region: Oregon (US West)
   Branch: main
   Root Directory: (留空)
   Build Command: pip install -r requirements.txt
   Start Command: python app.py
   ```

### 步驟3：設定環境變數

在Render的Environment Variables中新增：

```bash
# 必須設定
API_KEY=your-super-secure-api-key-here
SECRET_KEY=your-secret-key-for-sessions

# 安全設定
ALLOWED_HOSTS=your-app-name.onrender.com
CORS_ORIGINS=https://your-web-domain.com
MAX_FILE_SIZE=10485760
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# 資料庫
DATABASE_URL=sqlite:///./microalgae_data.db

# 其他設定
PYTHON_VERSION=3.11.0
```

### 步驟4：部署

1. **點擊 "Create Web Service"**
2. **等待部署完成**（約5-10分鐘）
3. **檢查部署狀態**

## 🔧 部署後設定

### 1. 測試API
```bash
# 測試基本端點
curl https://your-app-name.onrender.com/

# 測試健康檢查
curl https://your-app-name.onrender.com/health/
```

### 2. 更新網頁介面
修改 `index.html` 中的API網址：
```javascript
const API_BASE_URL = 'https://your-app-name.onrender.com';
```

### 3. 部署網頁介面
- 使用Netlify、Vercel或GitHub Pages
- 上傳 `index.html`
- 獲得網頁網址

## 📱 分享給朋友

### 方法1：直接分享API
```
API網址: https://your-app-name.onrender.com
API文件: https://your-app-name.onrender.com/docs
API金鑰: your-super-secure-api-key-here
```

### 方法2：分享網頁介面
```
網頁網址: https://your-web-site.netlify.app
API網址: https://your-app-name.onrender.com
API金鑰: your-super-secure-api-key-here
```

## 🔍 故障排除

### 常見問題

1. **部署失敗**
   - 檢查 `requirements.txt` 是否正確
   - 確認Python版本設定
   - 查看Build Logs

2. **API無法訪問**
   - 檢查環境變數設定
   - 確認API金鑰正確
   - 查看Service Logs

3. **檔案上傳失敗**
   - 檢查檔案大小限制
   - 確認檔案格式支援
   - 查看錯誤日誌

### 檢查日誌
在Render Dashboard中：
1. 點擊您的服務
2. 選擇 "Logs" 標籤
3. 查看即時日誌

## 🛡️ 安全建議

### 1. 定期更新
- 更新依賴套件
- 更換API金鑰
- 檢查安全日誌

### 2. 監控使用
- 查看統計資訊
- 監控異常活動
- 設定告警

### 3. 備份資料
- 定期備份資料庫
- 匯出重要資料
- 建立恢復計畫

## 📊 使用統計

部署完成後，您可以：
- 查看上傳統計：`/data/stats/`
- 管理檔案：`/files/`
- 匯出資料：`/data/export/`

## 🎯 下一步

1. **測試完整功能**
2. **分享給朋友使用**
3. **監控使用情況**
4. **根據需求調整設定**

## 📞 技術支援

如果遇到問題：
1. 檢查Render服務狀態
2. 查看部署日誌
3. 測試API端點
4. 檢查環境變數設定

---

**恭喜！您的微藻養殖API已經成功部署到Render！** 🎉

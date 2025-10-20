# 微藻養殖API - 安全部署指南

## 🔒 Render安全性評估

### ✅ Render的安全優勢
- **HTTPS加密**：所有流量自動加密
- **容器隔離**：每個應用程式獨立運行
- **自動更新**：基礎設施安全補丁自動更新
- **DDoS保護**：內建攻擊防護
- **環境變數加密**：敏感資料安全儲存

### ⚠️ 需要注意的安全問題
- **公開API**：預設情況下API是公開的
- **簡單認證**：需要加強認證機制
- **資料庫安全**：SQLite檔案可能被直接存取
- **檔案上傳**：需要檔案類型驗證

## 🛡️ 安全改進措施

### 1. 使用安全版API
```bash
# 使用 secure_main.py 替代 main.py
py -m uvicorn secure_main:app --host 0.0.0.0 --port 8000
```

### 2. 生成安全API金鑰
```python
import secrets
secure_key = secrets.token_urlsafe(32)
print(f"安全API金鑰: {secure_key}")
```

### 3. 設定環境變數
在Render中設定以下環境變數：

```bash
# 必須更改
API_KEY=your-super-secure-api-key-here
SECRET_KEY=your-secret-key-for-sessions

# 安全設定
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-web-domain.com
MAX_FILE_SIZE=10485760
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# 資料庫
DATABASE_URL=sqlite:///./microalgae_data.db
```

## 🔐 安全功能

### 1. 速率限制
- 每小時最多100個請求
- 防止濫用和DDoS攻擊
- 自動封鎖過於頻繁的IP

### 2. 檔案安全檢查
- 檔案類型驗證（只允許.xlsx, .xls）
- 檔案大小限制（10MB）
- 檔案名稱清理
- 惡意檔案檢測

### 3. 輸入驗證
- SQL注入防護
- XSS攻擊防護
- 路徑遍歷攻擊防護

### 4. 會話管理
- 用戶會話追蹤
- IP地址記錄
- 活動日誌

## 🚀 安全部署步驟

### 步驟1：準備安全設定
```bash
# 生成安全金鑰
python -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

### 步驟2：部署到Render
1. 上傳 `secure_main.py` 到GitHub
2. 在Render中建立新服務
3. 設定環境變數
4. 部署

### 步驟3：設定網域安全
```bash
# 在Render中設定自訂網域
ALLOWED_HOSTS=your-api-domain.com
CORS_ORIGINS=https://your-web-domain.com
```

### 步驟4：啟用HTTPS
- Render自動提供HTTPS
- 設定HSTS標頭
- 強制重定向到HTTPS

## 📊 安全監控

### 1. 日誌監控
```python
# 在 secure_main.py 中已包含
- 上傳活動日誌
- 錯誤日誌
- 安全事件日誌
```

### 2. 統計資訊
```bash
# 查看安全統計
GET /data/stats/
```

### 3. 異常檢測
- 異常上傳頻率
- 大檔案上傳
- 錯誤請求模式

## 🔧 進階安全設定

### 1. 資料庫加密
```python
# 考慮使用PostgreSQL替代SQLite
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### 2. 檔案儲存安全
```python
# 使用雲端儲存
- AWS S3
- Google Cloud Storage
- Azure Blob Storage
```

### 3. 身份驗證
```python
# 實作JWT認證
- 用戶註冊/登入
- Token過期機制
- 角色權限控制
```

## 📋 安全檢查清單

### 部署前檢查
- [ ] 更改預設API金鑰
- [ ] 設定適當的CORS來源
- [ ] 限制檔案大小
- [ ] 啟用速率限制
- [ ] 設定安全標頭

### 部署後檢查
- [ ] 測試API端點
- [ ] 驗證檔案上傳限制
- [ ] 檢查速率限制
- [ ] 監控日誌
- [ ] 測試安全功能

### 定期維護
- [ ] 更新依賴套件
- [ ] 檢查安全日誌
- [ ] 更新API金鑰
- [ ] 備份資料庫
- [ ] 安全掃描

## 🚨 安全事件處理

### 1. 發現安全問題
```bash
# 立即停止服務
# 檢查日誌
# 修復問題
# 重新部署
```

### 2. 資料洩露
```bash
# 立即更改API金鑰
# 檢查資料庫
# 通知用戶
# 加強安全措施
```

### 3. DDoS攻擊
```bash
# Render自動處理
# 檢查速率限制
# 監控異常流量
```

## 📞 安全支援

### 安全問題回報
- 檢查日誌檔案
- 收集錯誤訊息
- 提供重現步驟

### 安全更新
- 定期更新依賴套件
- 關注安全公告
- 實作安全補丁

## 🎯 最佳實踐

1. **最小權限原則**：只給予必要的權限
2. **深度防禦**：多層安全防護
3. **定期審計**：檢查安全設定
4. **監控告警**：即時發現問題
5. **備份恢復**：定期備份資料

## 📈 安全等級評估

### 基本安全（使用main.py）
- ⭐⭐⭐ 中等安全
- 適合內部使用
- 需要額外安全措施

### 增強安全（使用secure_main.py）
- ⭐⭐⭐⭐ 高安全
- 適合生產環境
- 包含完整安全功能

### 企業級安全
- ⭐⭐⭐⭐⭐ 最高安全
- 需要額外實作
- 包含身份驗證、加密等

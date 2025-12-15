# 專案功能更新說明

## 已完成的功能

### 1. 截止期限支援分鐘級別設定
- **修改位置**: 專案創建表單 (`templates/partials/create_project_form.html`)
- **變更**: 將截止時間單位從「天」改為「分鐘」
- **預設值**: 10080 分鐘（= 7 天）
- **用途**: 允許委託人更精確地設定投標截止時間

### 2. 接案人提案時上傳 PDF 計畫書
- **功能**: 接案人報價時必須上傳 PDF 格式的提案計畫書
- **檔案驗證**: 系統自動驗證只接受 PDF 格式
- **檔名處理**: 使用格式 `proposal_{專案ID}_{接案人ID}_{時間戳}_{原始檔名}` 防止覆蓋
- **儲存位置**: `html/uploads/proposals/`
- **資料庫**: 在 `bids` 表新增 `proposal_file_path` 欄位
- **顯示**: 委託人可在專案詳情頁查看並下載所有投標者的提案計畫書

### 3. 檔案版本控制系統
- **新資料表**: `delivery_versions` 追蹤所有交付檔案版本
- **版本編號**: 自動從 1 開始遞增
- **檔名格式**: `delivery_{專案ID}_v{版本號}_{時間戳}_{原始檔名}`
- **儲存位置**: `html/uploads/deliveries/`
- **特性**:
  - 不同版本檔案不會互相覆蓋
  - 完整保留所有歷史版本
  - 每個版本都有狀態標記（pending/accepted/rejected）

### 4. 退回案件功能
- **功能**: 委託人可以退回接案人提交的檔案
- **流程**:
  1. 委託人審核交付檔案
  2. 點擊「退件」按鈕
  3. 系統將專案狀態改為 `rejected`
  4. 最新版本檔案標記為 `rejected`
  5. 接案人收到通知
  6. 接案人可重新上傳新版本

### 5. 重新上傳新版本
- **自動版本管理**: 每次上傳自動產生新版本號
- **不覆蓋原則**: 新版本不會取代舊版本
- **通知機制**: 上傳後自動通知委託人審核新版本

### 6. 歷史版本查看與下載
- **版本列表**: 在專案詳情頁顯示所有交付版本
- **資訊顯示**:
  - 版本號
  - 上傳時間
  - 下載連結
  - 狀態（待審核/已接受/已退回）
- **權限**: 委託人和接案人都可查看完整版本歷史

### 7. 委託人選擇接案人
- **現有功能增強**: 已有的投標接受功能
- **流程**:
  1. 委託人查看所有報價和提案計畫書
  2. 點擊「接受此報價」
  3. 系統自動:
     - 設定專案狀態為 `in_progress`
     - 拒絕其他投標
     - 通知被選中和未選中的接案人

## 資料庫變更

### 新增欄位
```sql
ALTER TABLE bids ADD COLUMN proposal_file_path VARCHAR(500);
```

### 新增資料表
```sql
CREATE TABLE delivery_versions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES posts(id),
    freelancer_id INTEGER NOT NULL REFERENCES users(id),
    file_path VARCHAR(500) NOT NULL,
    version INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending'
);
```

## 安裝與設定

### 1. 更新資料庫
```bash
# 在 PostgreSQL 資料庫中執行
psql -d your_database -f database_schema_update.sql
```

或者直接在資料庫管理工具中執行 `database_schema_update.sql` 的內容。

### 2. 創建必要的目錄
```bash
# Windows PowerShell
New-Item -ItemType Directory -Force -Path "html/uploads/proposals"
New-Item -ItemType Directory -Force -Path "html/uploads/deliveries"

# Linux/Mac
mkdir -p html/uploads/proposals
mkdir -p html/uploads/deliveries
```

### 3. 啟動伺服器
```bash
uvicorn main:app --reload
```

## 使用流程

### 委託人流程
1. 創建專案時設定截止時間（分鐘）
2. 等待接案人投標並上傳提案計畫書
3. 查看所有投標和下載提案計畫書 PDF
4. 選擇一位接案人
5. 等待接案人交付檔案
6. 審核交付檔案（可查看所有版本）
7. 選擇「接受結案」或「退件」
8. 如退件，等待接案人重新上傳新版本

### 接案人流程
1. 瀏覽開放專案
2. 選擇專案後填寫報價
3. **必須上傳 PDF 提案計畫書**
4. 等待委託人選擇
5. 如被選中，開始工作
6. 上傳結案檔案（版本 1）
7. 如被退件，修改後重新上傳（版本 2, 3...）
8. 委託人接受後專案結案

## 檔案命名規則

### 提案計畫書
```
proposal_{專案ID}_{接案人ID}_{時間戳}_{原始檔名}.pdf
範例: proposal_35_12_20231215_143022_我的提案.pdf
```

### 交付檔案
```
delivery_{專案ID}_v{版本號}_{時間戳}_{原始檔名}
範例: delivery_35_v1_20231215_150000_最終成品.zip
範例: delivery_35_v2_20231216_100000_修正版.zip
```

## 技術細節

### 新增的模型檔案
- `model/deliveries.py`: 處理交付版本的資料庫操作

### 修改的檔案
- `main.py`: 
  - 更新 `submit_bid()` 支援 PDF 上傳
  - 更新 `deliver_project()` 支援版本控制
  - 更新 `read_project()` 顯示版本歷史
  - 更新 `reject_project()` 和 `complete_project()` 標記版本狀態
  - 所有 deadline 計算從 `timedelta(days=...)` 改為 `timedelta(minutes=...)`

- `model/bids.py`:
  - `create_bid()` 新增 `proposal_file_path` 參數
  - `get_bids_for_project()` 查詢包含 `proposal_file_path`

- `templates/partials/create_project_form.html`:
  - 截止時間標籤改為「分鐘」
  - 預設值改為 10080 分鐘

- `templates/partials/read_project.html`:
  - 投標表單新增 PDF 檔案上傳欄位
  - 投標列表新增提案計畫書下載欄位
  - 新增版本歷史表格顯示

## 注意事項

1. **PDF 驗證**: 系統僅接受 `.pdf` 副檔名的檔案作為提案計畫書
2. **檔案大小**: 目前沒有限制，建議日後在 `routes/upload.py` 中設定上限
3. **權限管理**: 只有委託人能查看所有投標的提案計畫書
4. **版本管理**: 所有版本檔案永久保留，定期清理需手動處理
5. **時間單位**: 截止時間現在是分鐘，建議 UI 可以提供快速選項（如 7 天 = 10080 分鐘）

## 未來可能的改進

1. 在前端新增時間單位轉換輔助（天/小時/分鐘）
2. 自動清理過期的未接受投標的提案計畫書
3. 檔案大小限制和格式驗證增強
4. 版本比對功能
5. 下載所有版本為壓縮檔
6. 版本註解功能（委託人可對每個版本留言）

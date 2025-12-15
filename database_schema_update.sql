-- 資料庫結構更新 SQL
-- 執行此 SQL 以支援新功能

-- 1. 在 bids 表新增 proposal_file_path 欄位（如果尚未存在）
-- 用於儲存提案計畫書 PDF 的檔案路徑
ALTER TABLE bids ADD COLUMN IF NOT EXISTS proposal_file_path VARCHAR(500);

-- 2. 創建 delivery_versions 表來追蹤檔案版本歷史
-- 此表記錄每次交付的所有版本，支援退回和重新上傳
CREATE TABLE IF NOT EXISTS delivery_versions (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    freelancer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    version INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending',
    CONSTRAINT unique_project_version UNIQUE (project_id, version)
);

-- 創建索引以提升查詢效能
CREATE INDEX IF NOT EXISTS idx_delivery_versions_project_id ON delivery_versions(project_id);
CREATE INDEX IF NOT EXISTS idx_delivery_versions_freelancer_id ON delivery_versions(freelancer_id);
CREATE INDEX IF NOT EXISTS idx_delivery_versions_status ON delivery_versions(status);

-- 為 bids 表的 proposal_file_path 欄位新增註解
COMMENT ON COLUMN bids.proposal_file_path IS '提案計畫書 PDF 檔案路徑';

-- 為 delivery_versions 表新增註解
COMMENT ON TABLE delivery_versions IS '專案交付檔案版本歷史記錄';
COMMENT ON COLUMN delivery_versions.project_id IS '專案 ID';
COMMENT ON COLUMN delivery_versions.freelancer_id IS '接案人 ID';
COMMENT ON COLUMN delivery_versions.file_path IS '檔案儲存路徑';
COMMENT ON COLUMN delivery_versions.version IS '版本號（從 1 開始遞增）';
COMMENT ON COLUMN delivery_versions.uploaded_at IS '上傳時間';
COMMENT ON COLUMN delivery_versions.status IS '狀態：pending（待審核）、accepted（已接受）、rejected（已退回）';

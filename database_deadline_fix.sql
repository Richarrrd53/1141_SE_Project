-- 修正截止日期顯示問題
-- 新增 deadline_datetime 欄位來儲存完整的截止日期時間

-- 1. 新增 deadline_datetime 欄位（如果尚未存在）
ALTER TABLE posts ADD COLUMN IF NOT EXISTS deadline_datetime TIMESTAMP;

-- 2. 為現有資料填充 deadline_datetime（使用 create_time + deadline 分鐘）
UPDATE posts 
SET deadline_datetime = create_time + (deadline || ' minutes')::INTERVAL
WHERE deadline_datetime IS NULL AND deadline IS NOT NULL;

-- 3. 為欄位新增註解
COMMENT ON COLUMN posts.deadline_datetime IS '截止日期時間（完整的日期時間）';

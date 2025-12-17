import psycopg
from psycopg.rows import dict_row
from datetime import datetime

async def create_delivery_version(conn, project_id: int, freelancer_id: int, file_path: str, version: int):
    """創建新的交付檔案版本"""
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            INSERT INTO delivery_versions (project_id, freelancer_id, file_path, version, uploaded_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id
        """
        await cur.execute(sql, (project_id, freelancer_id, file_path, version))
        result = await cur.fetchone()
        return result['id']

async def get_latest_version_number(conn, project_id: int):
    """取得專案的最新版本號"""
    async with conn.cursor() as cur:
        sql = "SELECT COALESCE(MAX(version), 0) as max_version FROM delivery_versions WHERE project_id = %s"
        await cur.execute(sql, (project_id,))
        result = await cur.fetchone()
        return result['max_version'] if result else 0

async def get_all_delivery_versions(conn, project_id: int):
    """取得專案的所有交付版本"""
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT 
                dv.id,
                dv.project_id,
                dv.file_path,
                dv.version,
                dv.uploaded_at,
                dv.status,
                u.username as freelancer_username
            FROM delivery_versions dv
            JOIN users u ON dv.freelancer_id = u.id
            WHERE dv.project_id = %s
            ORDER BY dv.version DESC
        """
        await cur.execute(sql, (project_id,))
        rows = await cur.fetchall()
        return rows

async def get_latest_delivery_version(conn, project_id: int):
    """取得專案的最新交付版本"""
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT 
                dv.id,
                dv.project_id,
                dv.file_path,
                dv.version,
                dv.uploaded_at,
                dv.status,
                u.username as freelancer_username
            FROM delivery_versions dv
            JOIN users u ON dv.freelancer_id = u.id
            WHERE dv.project_id = %s
            ORDER BY dv.version DESC
            LIMIT 1
        """
        await cur.execute(sql, (project_id,))
        row = await cur.fetchone()
        return row

async def update_delivery_status(conn, delivery_id: int, status: str):
    """更新交付版本狀態"""
    async with conn.cursor() as cur:
        sql = "UPDATE delivery_versions SET status = %s WHERE id = %s"
        await cur.execute(sql, (status, delivery_id))
        return True

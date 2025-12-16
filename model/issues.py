import psycopg
from psycopg.rows import dict_row
from datetime import datetime



async def create_issue(conn, project_id: int, created_by: int, title: str, description: str):
    """建立新的 Issue"""
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            INSERT INTO issues (project_id, created_by, title, description, status)
            VALUES (%s, %s, %s, %s, 'open')
            RETURNING id, project_id, created_by, title, description, status, created_at
        """
        await cur.execute(sql, (project_id, created_by, title, description))
        return await cur.fetchone()


async def get_issues_by_project(conn, project_id: int):
    """取得專案的所有 Issues"""
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT 
                i.id,
                i.project_id,
                i.title,
                i.description,
                i.status,
                i.created_at,
                i.resolved_at,
                u.username AS creator_username,
                (SELECT COUNT(*) FROM issue_comments WHERE issue_id = i.id) AS comment_count
            FROM issues i
            JOIN users u ON i.created_by = u.id
            WHERE i.project_id = %s
            ORDER BY 
                CASE WHEN i.status = 'open' THEN 0 ELSE 1 END,
                i.created_at DESC
        """
        await cur.execute(sql, (project_id,))
        return await cur.fetchall()


async def get_issue_by_id(conn, issue_id: int):
    """取得單一 Issue 詳情"""
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT 
                i.id,
                i.project_id,
                i.title,
                i.description,
                i.status,
                i.created_at,
                i.resolved_at,
                i.created_by,
                u.username AS creator_username
            FROM issues i
            JOIN users u ON i.created_by = u.id
            WHERE i.id = %s
        """
        await cur.execute(sql, (issue_id,))
        return await cur.fetchone()


async def update_issue_status(conn, issue_id: int, status: str):
    """更新 Issue 狀態"""
    async with conn.cursor() as cur:
        if status == 'resolved':
            sql = """
                UPDATE issues 
                SET status = %s, resolved_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
        else:
            sql = """
                UPDATE issues 
                SET status = %s, resolved_at = NULL
                WHERE id = %s
            """
        await cur.execute(sql, (status, issue_id))
        return True


async def check_all_issues_resolved(conn, project_id: int):
    """檢查專案的所有 Issues 是否都已解決"""
    async with conn.cursor() as cur:
        sql = """
            SELECT COUNT(*) as open_count
            FROM issues
            WHERE project_id = %s AND status = 'open'
        """
        await cur.execute(sql, (project_id,))
        result = await cur.fetchone()
        return result['open_count'] == 0




async def create_issue_comment(conn, issue_id: int, user_id: int, comment: str):
    """新增 Issue 留言"""
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            INSERT INTO issue_comments (issue_id, user_id, comment)
            VALUES (%s, %s, %s)
            RETURNING id, issue_id, user_id, comment, created_at
        """
        await cur.execute(sql, (issue_id, user_id, comment))
        return await cur.fetchone()


async def get_comments_by_issue(conn, issue_id: int):
    """取得 Issue 的所有留言"""
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT 
                ic.id,
                ic.issue_id,
                ic.comment,
                ic.created_at,
                u.id AS user_id,
                u.username,
                u.role
            FROM issue_comments ic
            JOIN users u ON ic.user_id = u.id
            WHERE ic.issue_id = %s
            ORDER BY ic.created_at ASC
        """
        await cur.execute(sql, (issue_id,))
        return await cur.fetchall()


async def delete_issue_comment(conn, comment_id: int, user_id: int):
    """刪除留言 (只有留言者可以刪除)"""
    async with conn.cursor() as cur:
        sql = """
            DELETE FROM issue_comments
            WHERE id = %s AND user_id = %s
            RETURNING id
        """
        await cur.execute(sql, (comment_id, user_id))
        result = await cur.fetchone()
        return result is not None




async def get_issue_statistics(conn, project_id: int):
    """取得 Issue 統計資訊"""
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT 
                COUNT(*) as total_issues,
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open_issues,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_issues
            FROM issues
            WHERE project_id = %s
        """
        await cur.execute(sql, (project_id,))
        return await cur.fetchone()
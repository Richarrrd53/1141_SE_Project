import psycopg
from psycopg.rows import dict_row

async def create_notification(conn, user_id, message: str, link: str):
    async with conn.cursor() as cur:
        sql = """
            INSERT INTO notifications (user_id, message, link, is_read, created_at)
            VALUES (%s, %s, %s, FALSE, CURRENT_TIMESTAMP)
        """
        await cur.execute(sql, (user_id, message, link))
        
async def get_notifications_for_user(conn, user_id):
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT 
                id, 
                message, 
                link, 
                is_read, 
                created_at 
            FROM notifications 
            WHERE 
                user_id = %s
            ORDER BY 
                created_at DESC;
        """
        await cur.execute(sql, (user_id,))
        rows = await cur.fetchall()
        return rows
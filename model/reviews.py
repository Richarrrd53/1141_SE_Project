from psycopg.rows import dict_row

async def create_review(conn, project_id, from_user_id, to_user_id, target_role, s1, s2, s3, comment):
    async with conn.cursor() as cur:
        sql="""
            INSERT INTO reviews (project_id, from_user_id, to_user_id, target_role, score_1, score_2, score_3, comment) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
        """
        await cur.execute(sql, (project_id, from_user_id, to_user_id, target_role, s1, s2, s3, comment))
        
async def get_reviews_received(conn, user_id: int):
    async with conn.cursor(row_factory=dict_row) as cur:
        sql="""
            SELECT *, u.username as from_username, p.title as project_title 
            FROM reviews r 
            JOIN users u ON r.from_user_id = u.id 
            JOIN posts p ON r.project_id = p.id 
            WHERE r.to_user_id = %s 
            ORDER BY r.created_at DESC
        """
        await cur.execute(sql, (user_id,))
        return await cur.fetchall()
    
async def get_user_avg_rating(conn, user_id: int):
    async with conn.cursor() as cur:
        sql="""
            SELECT AVG((score_1 + score_2 + score_3) / 3.0) AS avg_score 
            FROM reviews 
            WHERE to_user_id = %s
        """
        await cur.execute(sql, (user_id,))
        result = await cur.fetchone()
        if result and result['avg_score'] is not None:
            return round(result['avg_score'], 1)
        return 0.0
    
async def check_if_reviewed(conn, project_id, from_id):
    async with conn.cursor() as cur:
        sql="""
            SELECT id
            FROM reviews 
            WHERE project_id = %s AND from_user_id = %s
        """
        await cur.execute(sql, (project_id, from_id))
        return await cur.fetchone() is not None
    
async def get_reviews_by_project(conn, project_id):
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT r.*, u.username as reviewer_name 
            FROM reviews r
            JOIN users u ON r.from_user_id = u.id
            WHERE r.project_id = %s
        """
        await cur.execute(sql, (project_id,))
        return await cur.fetchall()
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row


async def getList(conn, user_id):
    async with conn.cursor() as cur:
        sql="""
            SELECT
				client.username, 
    			p.status, 
       			p.user_id,
          		p.id, 
            	p.title, 
             	p.create_time, 
              	p.deadline, 
               	p.budget
            FROM posts AS p
            JOIN users AS client ON p.user_id = client.id
            WHERE p.user_id = %s AND p.is_deleted = FALSE
            ORDER BY p.id DESC;
        """
        await cur.execute(sql, (user_id,))
        rows = await cur.fetchall()
        return rows

async def getPost(conn, id):
	async with conn.cursor(row_factory=dict_row) as cur:
		sql = """
            SELECT 
                p.id, 
                p.title, 
                p.content, 
                p.budget, 
                p.create_time, 
                p.deadline, 
                p.status,
                p.delivery_file_path,
                client.username AS client_username,
                freelancer.username AS accepted_freelancer_username 
            FROM posts AS p
            
            JOIN users AS client ON p.user_id = client.id
            
            LEFT JOIN users AS freelancer ON p.accepted_freelancer_id = freelancer.id
            
            WHERE p.id = %s AND p.is_deleted = FALSE;
        """
		await cur.execute(sql, (id,))
		row = await cur.fetchone()
		return row

async def get_any_post_by_id(conn, id: int):
	async with conn.cursor(row_factory=dict_row) as cur:
		sql = """
				SELECT 
					p.id, 
					p.title, 
					p.content, 
					p.budget, 
					p.create_time, 
					p.deadline, 
					p.status,
					p.delivery_file_path,
					client.username AS client_username,
					freelancer.username AS accepted_freelancer_username 
				FROM posts AS p
				
				JOIN users AS client ON p.user_id = client.id
				
				LEFT JOIN users AS freelancer ON p.accepted_freelancer_id = freelancer.id
				
				WHERE p.id = %s;
			"""
		await cur.execute(sql, (id,))
		row = await cur.fetchone()
		return row


async def getUseridFromPost(conn, id):
    async with conn.cursor() as cur:
        sql="SELECT p.user_id FROM posts AS p WHERE p.id = %s"
        await cur.execute(sql, (id,))
        row = await cur.fetchone()
        return row

async def deletePost(conn, id):
	async with conn.cursor() as cur:
		sql="UPDATE posts SET is_deleted = TRUE WHERE id = %s;"
		sql2 = "UPDATE posts SET status = 'deleted' WHERE id = %s"
		await cur.execute(sql,(id,))
		await cur.execute(sql2,(id,))
		return True

async def createPost(conn, title, content, budget, create_time, deadline, user_id):
	async with conn.cursor() as cur:
		sql="insert into posts (title, content, budget, create_time, deadline, user_id) values (%s,%s,%s,%s,%s,%s);"
		await cur.execute(sql,(title, content, budget, create_time, deadline, user_id))
		return True
	
async def editPost(conn, title, content, budget, id):
	async with conn.cursor() as cur:
		sql1= "update posts set title = %s where id = %s;"
		sql2= "update posts set content = %s where id = %s;"
		sql3= "update posts set budget = %s where id = %s;"
		await cur.execute(sql1,(title,id))
		await cur.execute(sql2,(content,id))
		await cur.execute(sql3,(budget,id))
		return True

async def get_open_projects(conn):
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
        	SELECT 
         		p.id, 
           		p.title, 
             	p.budget, 
              	p.create_time, 
               	p.deadline, 
                u.username AS client_username 
			FROM posts AS p 
			INNER JOIN users AS u ON p.user_id = u.id 
   			WHERE p.status = 'open' AND p.is_deleted = FALSE
      		ORDER BY p.create_time DESC; 
        
        """
        await cur.execute(sql)
        rows = await cur.fetchall()
        return rows
    
async def update_project_status_and_assignee(conn, project_id, status: str, freelancer_id):
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = "UPDATE posts SET status = %s, accepted_freelancer_id = %s WHERE id = %s"
        await cur.execute(sql, (status, freelancer_id, project_id))
        return True
    
    
async def update_project_delivery(conn, project_id, file_path: str):
    async with conn.cursor() as cur:
        sql = "UPDATE posts SET status = 'delivered', delivery_file_path = %s WHERE id = %s AND status = 'in_progress' OR status = 'rejected'"
        await cur.execute(sql, (file_path, project_id))
        return True

async def get_projects_by_freelancer(conn, freelancer_id):
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT 
                p.id, 
                p.title, 
                p.budget, 
                p.create_time, 
                p.deadline,
                p.status,
                u.username AS client_username 
            FROM posts AS p
            
            INNER JOIN users AS u ON p.user_id = u.id
            
            WHERE p.accepted_freelancer_id = %s AND p.is_deleted = FALSE
            ORDER BY p.create_time DESC;
        """
        await cur.execute(sql, (freelancer_id,))
        rows = await cur.fetchall()
        return rows
    
async def get_one_project_by_freelancer(conn, freelancer_id):
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT 
                p.id, 
                p.title, 
                p.budget, 
                p.create_time, 
                p.deadline,
                p.status,
                u.username AS client_username 
            FROM posts AS p
            
            INNER JOIN users AS u ON p.user_id = u.id
            
            WHERE p.accepted_freelancer_id = %s AND p.is_deleted = FALSE
            ORDER BY p.create_time DESC;
        """
        await cur.execute(sql, (freelancer_id,))
        rows = await cur.fetchone()
        return rows

async def update_project_status(conn, project_id, status: str):
    async with conn.cursor() as cur:
        sql = "UPDATE posts SET status = %s WHERE id = %s"
        await cur.execute(sql, (status, project_id))
        
async def get_history_projects(conn, user_id, role):
	async with conn.cursor(row_factory=dict_row) as cur:
		if role == 'client':
			sql="""
				SELECT
					client.username, 
					p.status, 
					p.user_id,
					p.id, 
					p.title, 
					p.create_time, 
					p.deadline, 
					p.budget
				FROM posts AS p
				JOIN users AS client ON p.user_id = client.id
				WHERE p.user_id = %s
				ORDER BY p.id DESC;
				"""
		else:
			sql="""
					SELECT 
					p.id, 
					p.title, 
					p.budget, 
					p.create_time, 
					p.deadline,
					p.status,
					u.username AS client_username 
				FROM posts AS p

				INNER JOIN users AS u ON p.user_id = u.id

				WHERE p.accepted_freelancer_id = %s
				ORDER BY p.create_time DESC;
				"""
		await cur.execute(sql, (user_id,))
		return await cur.fetchall()

		
    
async def restore_project(conn, project_id, today):
    async with conn.cursor() as cur:
        sql = "UPDATE posts SET is_deleted = FALSE WHERE id = %s;"
        sql2 = "UPDATE posts SET status = 'open' WHERE id = %s;"
        sql3 = "UPDATE posts SET create_time = %s WHERE id = %s;"
        await cur.execute(sql, (project_id,))
        await cur.execute(sql2, (project_id,))
        await cur.execute(sql3, (today,project_id))
        return True
        
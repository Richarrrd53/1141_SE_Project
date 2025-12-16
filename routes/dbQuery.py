from fastapi import APIRouter, Depends
from model.db import getDB
router = APIRouter()

@router.get("/getUsers")
async def read_users(conn=Depends(getDB)):
    async with conn.cursor() as cur:
        await cur.execute("select * from users;")
        rows = await cur.fetchall()
        return {"items": rows}
    
@router.get("/findUserByName")
async def read_user(name:str,conn=Depends(getDB)):
	async with conn.cursor() as cur:
		name = f"{name}%"
		sql="SELECT * FROM users where name like %s"
		await cur.execute(sql,(name,))
		rows = await cur.fetchall()
		return {"items": rows}
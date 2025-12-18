from fastapi import FastAPI, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.encoders import jsonable_encoder

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

from routes.upload import router as upload_router
from routes.dbQuery import router as db_router
from model.db import getDB
import model.posts as posts
import model.users as users
import model.bids as bids
import model.notifications as notifications
import model.issues as issues
import model.reviews as reviews
import model.deliveries as deliveries

import security

from datetime import date, time, timedelta, datetime
from zoneinfo import ZoneInfo
from psycopg.rows import dict_row

import os
import re



app = FastAPI()

app.include_router(upload_router, prefix="/api")
app.include_router(db_router, prefix="/api")

from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key = "a5850536k5759525",
    max_age=None,
    same_site="lax",
    https_only=False
)

def get_current_user(req: Request):
    user_id = req.session.get("user")
    return user_id

def get_current_role(req:Request):
    return req.session.get("role")

def translate_status(status: str) -> str:
    status_map = {
        "open": "開放中",
        "in_progress": "進行中",
        "delivered": "已交付",
        "completed": "已結案",
        "rejected": "已退件",
        "cancelled": "已取消",
        "deleted": "已刪除"
    }
    return status_map.get(status, "未知狀態")

def translate_role(role: str) -> str:
    role_map = {
        "client": "委託人",
        "freelancer": "接案人"
    }
    return role_map.get(role, "未知身分")

def checkRole(reqRole:str):
    def checker(req: Request):
        user_role = req.session.get("role")
        if user_role == reqRole:
            return True
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    return checker

def safeFilename(filename:str):
    ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".zip", ".rar", ".ai"}
    name, ext = os.path.splitext(filename)

    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f": {', '.join(ALLOWED_EXTENSIONS)}"
        )
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)
    safe = re.sub(r'_+', '_', safe)
    return safe[:255]

async def get_notifications_for_user(conn, user_id):
    async with conn.cursor(row_factory=dict_row) as cur:
        sql = """
            SELECT * FROM notifications 
            WHERE user_id = %s AND is_read = FALSE 
            ORDER BY created_at DESC
        """
        await cur.execute(sql, (user_id,))
        return await cur.fetchall()


@app.get("/")
async def root(req: Request, conn = Depends(getDB), user:str=Depends(get_current_user)):
    if user is None:
        return RedirectResponse(url="login.html", status_code=302)
    
    current_user = await users.get_user_by_username(conn, user)
    if not current_user:
        return HTMLResponse("使用者錯誤", status_code=401)
    
    user_id = current_user['id']
    myRole = current_user['role']
    myList = await posts.getList(conn, user_id)
    return templates.TemplateResponse("postList.html", {"request":req,"items": myList,"role": myRole, "username": user})


@app.get("/page/my-projects", response_class=HTMLResponse)
async def get_my_projects_page(req: Request, conn = Depends(getDB), user:str=Depends(get_current_user)):
    if user is None:
        return HTMLResponse("請先登入", status_code=401)
    
    current_user = await users.get_user_by_username(conn, user)
    if not current_user:
        return HTMLResponse("使用者錯誤", status_code=401)
    
    user_id = current_user['id']
    myRole = current_user['role']
    myList = await posts.getList(conn, user_id)

    role_text = translate_role(myRole)

    # 定義台灣時區
    tw_tz = ZoneInfo("Asia/Taipei")

    for item in myList:
        d_dt = item.get('deadline_datetime')
        
        # 如果資料庫沒存絕對時間，才勉強用 create_time + deadline 分鐘數
        if d_dt is None and item.get('create_time') and item.get('deadline') is not None:
             d_dt = item['create_time'] + timedelta(minutes=item['deadline'])

        if d_dt:
            # 如果資料庫拿出來的是 Naive (沒有時區資訊，通常是 UTC)，先視為 UTC
            if d_dt.tzinfo is None:
                d_dt = d_dt.replace(tzinfo=ZoneInfo("UTC"))
            
            # 強制轉成台灣時間
            item['deadline_date'] = d_dt.astimezone(tw_tz)
        else:
            item['deadline_date'] = None
            
        is_deadline_passed = False
        if item.get("deadline_date"):
            is_deadline_passed = datetime.now(tw_tz) > item["deadline_date"]
            item["is_deadline_passed"] = is_deadline_passed

        item['status_text'] = translate_status(item.get('status', ''))
    

    return templates.TemplateResponse("partials/my_projects.html", {
        "request": req,
        "items": myList,
        "role_text": role_text,
        "role": myRole,
        "username": user,
    })

@app.get("/page/create-project", response_class=HTMLResponse)
async def get_create_project_page(req: Request, user:str=Depends(get_current_user)):
    if get_current_user(req) is None:
        return HTMLResponse("請先登入", status_code=401)
    
    today_str = date.today().strftime("%Y-%m-%d")
        
    return templates.TemplateResponse("partials/create_project_form.html", {
        "request": req,
        "user": user,
        "today_date": today_str
    })

@app.post("/page/create-project")
async def create_project(req: Request, conn = Depends(getDB), user_name: str = Depends(get_current_user),title: str = Form(...),content: str = Form(...),budget = Form(...),deadline = Form(...)):
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})
    try:
        tw_tz = ZoneInfo("Asia/Taipei")
        now = datetime.now(tw_tz)

        user = await users.get_user_by_username(conn, user_name)
        if not user:
            raise HTTPException(status_code=404, detail="找不到使用者")
        
        user_id = user['id']
        
        # 將前端傳來的 datetime-local 字串轉換為 datetime 物件
        deadline_dt = datetime.fromisoformat(deadline)
        
        # 如果前端傳來的時間沒有時區資訊 (Naive)，我們強制賦予它台灣時區
        if deadline_dt.tzinfo is None:
            deadline_dt = deadline_dt.replace(tzinfo=tw_tz)
        else:
            # 如果有帶時區，將其轉換為台灣時區以防萬一
            deadline_dt = deadline_dt.astimezone(tw_tz)
        
        # 計算從現在到截止時間的分鐘數
        time_diff = deadline_dt - now
        deadline_minutes = int(time_diff.total_seconds() / 60)
        
        
        
        # 確保截止時間在未來
        if deadline_minutes <= 0:
            return JSONResponse(status_code=400, content={"success": False, "message": "截止時間必須在未來"})

        await posts.createPost(conn, title, content, budget, now, deadline_minutes, user_id, deadline_dt)

        return JSONResponse(status_code=200, content={"success": True, "message": "專案建立成功"})
        

    except Exception as e:
        print(f"建立專案時發生錯誤: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": "伺服器內部錯誤"})

@app.get("/page/my-projects/read/{id}")
async def read_project(req: Request, id:int, conn = Depends(getDB), user: str=Depends(get_current_user)):
    if get_current_user(req) is None:
        return HTMLResponse("請先登入", status_code=401)
    
    project_detail = await posts.getPost(conn, id)
    if not project_detail:
        return HTMLResponse("<h1>404 - 找不到專案</h1>", status_code=404)
    


    # 定義台灣時區
    tw_tz = ZoneInfo("Asia/Taipei")
    d_dt = project_detail.get('deadline_datetime')
    if d_dt is None and project_detail.get("create_time") and project_detail.get("deadline") is not None:
        c_time = project_detail["create_time"]
        if not hasattr(c_time, 'hour'):  
            c_time = datetime.combine(c_time, time.min)
        d_dt = c_time + timedelta(minutes=project_detail["deadline"])
        
    if d_dt:
        if d_dt.tzinfo is None:
             # 假設 DB 存的是 UTC
            d_dt = d_dt.replace(tzinfo=ZoneInfo("UTC"))
        # 轉成台灣時間
        project_detail["deadline_date"] = d_dt.astimezone(tw_tz)
    else:
        project_detail["deadline_date"] = None
        
    project_detail["status_text"] = translate_status(project_detail.get("status", ""))
    
    # 檢查是否已過截止時間
    is_deadline_passed = False
    if project_detail.get("deadline_date"):
        is_deadline_passed = datetime.now(tw_tz) > project_detail["deadline_date"]
        
    # 取得所有交付版本
    delivery_versions = await deliveries.get_all_delivery_versions(conn, id)
    role = get_current_role(req)
    
    current_user_db = await users.get_user_by_username(conn, user) if user else None
   
    client_id = await posts.getUseridFromPost(conn, id)
    client_avg_score = await reviews.get_user_avg_rating(conn, client_id["user_id"])
    project_detail["client_avg_score"] = client_avg_score
   
    has_reviewed = False
   
    if current_user_db:
        has_reviewed = await reviews.check_if_reviewed(conn, id, current_user_db["id"])
        
    project_reviews = []
    if project_detail["status"] == "completed":
        project_reviews = await reviews.get_reviews_by_project(conn, id)
        
    for review in project_reviews:
        if review['created_at'].tzinfo is None:
            review['created_at'] = review['created_at'].replace(tzinfo=ZoneInfo("UTC"))
        review['created_at'] = review['created_at'].astimezone(ZoneInfo("Asia/Taipei"))
    
    if role == 'freelancer':
        freelancer_id = await users.get_user_by_username(conn, user)
        is_bid_exist = await bids.check_bid(conn, id, freelancer_id['id'])
        if is_bid_exist:
            bid_id = await bids.get_bid_id(conn, id, freelancer_id['id'])
            get_bid_status = await bids.get_bid_status(conn, bid_id['id'])
            bid_status = get_bid_status['status']
        else:
            bid_status = ""
        return templates.TemplateResponse("partials/read_project.html", {
            "request": req,
            "project": project_detail,
            "role": role,
            "current_user": user,
            "is_bid_exist": is_bid_exist, 
            "bid_status": bid_status,
            "delivery_versions": delivery_versions,
            "is_deadline_passed": is_deadline_passed,
            "has_reviewed": has_reviewed,
            "reviews_data": project_reviews
        })
    else:
        bids_list = await bids.get_bids_for_project(conn, id)
        return templates.TemplateResponse("partials/read_project.html", {
            "request":req,
            "project": project_detail, 
            "role": role, 
            "bids": bids_list,
            "current_user": user,
            "delivery_versions": delivery_versions,
            "is_deadline_passed": is_deadline_passed,
            "has_reviewed": has_reviewed,
            "reviews_data": project_reviews
            })
        

@app.get("/page/my-projects/edit-form/{id}", response_class=HTMLResponse)
async def get_project_edit_form(req: Request, id:int, conn = Depends(getDB), user:str=Depends(get_current_user)):
    if user is None:
        return HTMLResponse("請先登入", status_code=401)
    
    post_detail = await posts.getPost(conn, id)

    if not post_detail:
        return HTMLResponse("<h1>找不到專案</h1>", status_code=404)
    
    return templates.TemplateResponse("partials/project_edit_form.html", {
        "request": req,
        "item": post_detail
    })


@app.post("/page/my-projects/edit/{id}")
async def editPost(req: Request, id, conn = Depends(getDB), title: str=Form(...), content:str=Form(...), budget=Form(...), user:str=Depends(get_current_user)):
    await posts.editPost(conn, title, content, budget, id)
    
    project = await posts.getPost(conn, id)
    
    if project['status'] == 'in_progress' and project['accepted_freelancer_username']:
        freelancer = await users.get_user_by_username(conn, project['accepted_freelancer_username'])
        await notifications.create_notification(
            conn,
            user_id=freelancer['id'],
            message=f"您承接的專案「{project['title']}」資訊已被委託人變更。",
            link=f"/page/my-projects/read/{id}"
        )
    
    return JSONResponse(status_code=200, content={"success": True, "message": f"編輯成功！"})

    

@app.delete("/page/my-projects/delete/{id}")
async def delPost(
    req: Request, 
    id:int, 
    conn=Depends(getDB), 
    user_name:str=Depends(get_current_user)
):
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})
    
    try:
        project = await posts.get_any_post_by_id(conn, id)
        client = await posts.getUseridFromPost(conn, id)
        print(client)
        if not project or project['client_username'] != user_name:
            return JSONResponse(status_code=403, content={"success": False, "message": "沒有權限"})
        
        current_user = await users.get_user_by_username(conn, user_name)
        
        await posts.deletePost(conn, id)
        project_title = project['title']
        
        if project['accepted_freelancer_username']:
            await notifications.create_notification(
                conn,
                user_id=current_user['id'],
                message=f"您的專案「{project_title}」已被刪除。",
                link="/page/history"
            )

        bidders = await bids.get_bids_for_project(conn, id)
        for bid in bidders:
            if bid['status'] == 'pending' or  bid['status'] == 'accept' :
                await notifications.create_notification(
                    conn,
                    user_id=bid['freelancer_id'],
                    message=f"您投標的專案「{project_title}」已被委託人刪除。",
                    link="/page/browse-projects"
                )

        return JSONResponse(status_code=200, content={"success": True, "message": "刪除成功"})
        
    except Exception as e:
        await conn.rollback()
        return JSONResponse(status_code=500, content={"success": False, "message": f"伺服器錯誤: {str(e)}"})


@app.get("/page/browse-projects", response_class=HTMLResponse)
async def get_browse_projects_page(req: Request, conn = Depends(getDB), user:str=Depends(get_current_user)):
    if user is None:
        return HTMLResponse("請先登入", status_code=401)
    
    myRole = get_current_role(req)
    
    project_list = await posts.get_open_projects(conn)
    

            
    # 定義台灣時區
    tw_tz = ZoneInfo("Asia/Taipei")
    is_deadline_approaching = False
    for item in project_list:
        d_dt = item.get('deadline_datetime')
        
        # 如果資料庫沒存絕對時間，才勉強用 create_time + deadline 分鐘數
        if d_dt is None and item.get('create_time') and item.get('deadline') is not None:
             d_dt = item['create_time'] + timedelta(minutes=item['deadline'])

        if d_dt:
            # 如果資料庫拿出來的是 Naive (沒有時區資訊，通常是 UTC)，先視為 UTC
            if d_dt.tzinfo is None:
                d_dt = d_dt.replace(tzinfo=ZoneInfo("UTC"))
            
            # 強制轉成台灣時間
            item['deadline_date'] = d_dt.astimezone(tw_tz)
        else:
            item['deadline_date'] = None
            
        deadline = item["deadline_date"]
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=tw_tz)
        now = datetime.now(tw_tz)
        remaining_time = deadline - now
        
        if timedelta(0) < remaining_time <= timedelta(days=3):
            is_deadline_approaching = True
            
        item["is_deadline_approaching"] = is_deadline_approaching

        item['status_text'] = translate_status(item.get('status', ''))

    return templates.TemplateResponse("partials/browse_projects.html", {
        "request": req,
        "items": project_list,
        "role": myRole,
        "is_deadline_approaching": is_deadline_approaching
    })
    
@app.post("/api/project/bid", dependencies=[Depends(checkRole("freelancer"))])
async def submit_bid(
    req: Request, 
    conn = Depends(getDB), 
    user_name: str = Depends(get_current_user), 
    project_id = Form(...), 
    bid_amount = Form(...), 
    message: str = Form(""),
    proposal_file: UploadFile = File(...)
):
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})
    
    freelancer = await users.get_user_by_username(conn, user_name)
    if not freelancer:
        return JSONResponse(status_code=401, content={"success": False, "message": "找不到使用者"})
    
    freelancer_id = freelancer['id']
    
    filename_str = proposal_file.filename or ""
    
    if not filename_str.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"success": False, "message": "提案計畫書必須為 PDF 格式"})
    
    try:
        # 檢查專案狀態和截止日期
        project_detail = await posts.getPost(conn, project_id)
        if not project_detail:
            return JSONResponse(status_code=404, content={"success": False, "message": "找不到專案"})
        
        if project_detail['status'] != 'open':
            return JSONResponse(status_code=400, content={"success": False, "message": "此專案已不接受報價"})
        
        # 檢查截止日期
        deadline_dt = None
        if project_detail.get('deadline_datetime'):
            deadline_dt = project_detail['deadline_datetime']
        elif project_detail.get('create_time') and project_detail.get('deadline'):
            deadline_dt = project_detail['create_time'] + timedelta(minutes=project_detail['deadline'])
        
        if deadline_dt and datetime.now() > deadline_dt:
            return JSONResponse(status_code=400, content={"success": False, "message": "很抱歉，此專案已過截止日期，無法提交報價"})
        
        # 處理檔名防止覆蓋：使用 專案ID_接案人ID_時間戳_原始檔名
        
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename_str)
        unique_filename = f"proposal_{project_id}_{freelancer_id}_{timestamp}_{safe_filename}"
        
        # 儲存檔案
        upload_dir = "html/uploads/proposals"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            content = await proposal_file.read()
            buffer.write(content)
        
        # 儲存相對路徑
        relative_path = f"uploads/proposals/{unique_filename}"
        
        await bids.create_bid(conn, project_id, freelancer_id, bid_amount, message, relative_path)
        
        project_detail = await posts.getPost(conn, project_id)
        client_user = await users.get_user_by_username(conn, project_detail['client_username'])
        client_id = client_user['id']
        
        notify_message = f"您的專案「{project_detail['title']}」收到一筆來自 {user_name} 的新報價！"
        notify_link = f"/page/my-projects/read/{project_id}"
        
        await notifications.create_notification(conn, client_id, notify_message, notify_link)
        
        return JSONResponse(status_code=201, content={"success": True, "message": "報價已成功送出！"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})
    
@app.post("/api/project/accept-bid/{bid_id}", dependencies=[Depends(checkRole("client"))])
async def accept_bid_api(req: Request, bid_id, conn = Depends(getDB), user_name: str = Depends(get_current_user)):
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})

    try:
        current_user = await users.get_user_by_username(conn, user_name)
        
        bid_details = await bids.get_bid_details(conn, bid_id)
        if not bid_details:
            raise HTTPException(status_code=404, detail="找不到報價")
        
        project_id = bid_details['project_id']
        freelancer_id = bid_details['freelancer_id']

        project_detail = await posts.getPost(conn, project_id)
        if project_detail['client_username'] != user_name:
             raise HTTPException(status_code=403, detail="您沒有權限執行此操作")
        
        if project_detail['status'] != 'open':
            raise HTTPException(status_code=400, detail="此專案已不在開放競標狀態")
        
        await posts.update_project_status_and_assignee(conn, project_id, 'in_progress', freelancer_id)
        
        rejected_ids = await bids.set_bid_status(conn, bid_id, project_id, 'accepted')
        
        project_detail = await posts.get_one_project_by_freelancer(conn, freelancer_id)
        project_title = project_detail['title']
        
        await notifications.create_notification(
            conn,
            user_id=current_user["id"],
            message=f"您的專案「{project_title}」已鎖定並開始進入進程！",
            link=f"/page/my-projects/read/{project_id}"
        )
        
        
        await notifications.create_notification(
            conn,
            user_id=freelancer_id,
            message=f"恭喜！您對「{project_title}」的報價已被接受！",
            link=f"/page/my-projects/read/{project_id}"
        )
        
        for rejected_user_id in rejected_ids:
            await notifications.create_notification(
                conn,
                user_id=rejected_user_id,
                message=f"很遺憾，您對「{project_title}」的報價未被選中。",
                link=f"/page/browse-projects"
            )
        
        return JSONResponse(status_code=200, content={"success": True, "message": "已成功接受報價！專案現已開始進行。"})

    except Exception as e:
        await conn.rollback()
        return JSONResponse(status_code=500, content={"success": False, "message": f"伺服器錯誤: {str(e)}"})
    
@app.post("/api/project/{project_id}/reject", dependencies=[Depends(checkRole("client"))])
async def reject_project(
    req: Request, 
    project_id, 
    conn = Depends(getDB), 
    user_name: str = Depends(get_current_user)
):
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})

    try:
        project = await posts.getPost(conn, project_id)
        client_id = await posts.getUseridFromPost(conn, project_id)
        
        if not project or project['client_username'] != user_name:
            raise HTTPException(status_code=403, detail="您沒有權限執行此操作")
        if project['status'] != 'delivered':
            raise HTTPException(status_code=400, detail="此專案並非在『已交付』狀態")

        # 標記最新版本為已拒絕
        latest_version = await deliveries.get_latest_delivery_version(conn, project_id)
        if latest_version:
            await deliveries.update_delivery_status(conn, latest_version['id'], 'rejected')

        await posts.update_project_status(conn, project_id, 'rejected')
        
        freelancer = await users.get_user_by_username(conn, project['accepted_freelancer_username'])
        
        await notifications.create_notification(
            conn,
            user_id=client_id['user_id'],
            message=f"您已退回您的專案「{project['title']}」中接案人稿件，請等待接案人重新上傳。",
            link=f"/page/my-projects/read/{project_id}"
        )
        await notifications.create_notification(
            conn,
            user_id=freelancer['id'],
            message=f"您的專案「{project['title']}」已被委託人退件。",
            link=f"/page/my-projects/read/{project_id}"
        )
        
        return JSONResponse(status_code=200, content={"success": True, "message": "專案已退件，請等待接案人重新上傳。"})

    except Exception as e:
        await conn.rollback()
        return JSONResponse(status_code=500, content={"success": False, "message": f"伺服器錯誤: {str(e)}"})
    
@app.post("/api/project/{project_id}/deliver", dependencies=[Depends(checkRole("freelancer"))])
async def deliver_project(
    req: Request,
    project_id,
    conn = Depends(getDB),
    user_name: str = Depends(get_current_user),
    delivery_file: UploadFile = File(...)
):
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})

    try:
        current_user = await users.get_user_by_username(conn, user_name)
        project_detail = await posts.getPost(conn, project_id)
        client_id = await posts.getUseridFromPost(conn, project_id)

        if not project_detail:
            raise HTTPException(status_code=404, detail="找不到專案")
        
        if project_detail['accepted_freelancer_username'] != user_name:
            raise HTTPException(status_code=403, detail="您不是此專案的承接人")
        
        if project_detail['status'] != 'in_progress' and project_detail['status'] != 'rejected':
            raise HTTPException(status_code=400, detail="此專案並非在『進行中』狀態")
        
        if delivery_file.filename is None:
            raise HTTPException(status_code=400, detail="上傳的檔案缺少檔名")
        
        # 取得下一個版本號
        latest_version = await deliveries.get_latest_version_number(conn, project_id)
        next_version = latest_version + 1
        
        # 處理檔名防止覆蓋：使用 專案ID_版本號_時間戳_原始檔名
        timestamp = date.today().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', delivery_file.filename)
        unique_filename = f"delivery_{project_id}_v{next_version}_{timestamp}_{safe_name}"
        
        upload_dir = "html/uploads/deliveries"
        os.makedirs(upload_dir, exist_ok=True) 
        file_path_for_db = f"uploads/deliveries/{unique_filename}"
        full_save_path = os.path.join(upload_dir, unique_filename)

        with open(full_save_path, "wb") as buffer:
            buffer.write(await delivery_file.read())
        
        # 創建新版本記錄
        await deliveries.create_delivery_version(
            conn, 
            project_id, 
            current_user['id'], 
            file_path_for_db, 
            next_version
        )
        
        # 更新專案狀態為已交付
        await posts.update_project_delivery(conn, project_id, file_path_for_db)
        
        await notifications.create_notification(
            conn,
            user_id=client_id["user_id"],
            message=f"接案人已對您的專案「{project_detail['title']}」提交檔案（版本 {next_version}）。",
            link=f"/page/my-projects/read/{project_id}"
        )
        
        return JSONResponse(status_code=200, content={"success": True, "message": f"結案檔案版本 {next_version} 上傳成功！已通知委託人。"})

    except HTTPException as e:
        raise e
    except Exception as e:
        await conn.rollback()
        print(f"交付錯誤: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": f"伺服器錯誤: {str(e)}"})


@app.get("/page/my-jobs", response_class=HTMLResponse)
async def get_my_jobs_page(req: Request, conn = Depends(getDB), user_name:str=Depends(get_current_user)):
    if user_name is None:
        return HTMLResponse("請先登入", status_code=401)
    
    current_user = await users.get_user_by_username(conn, user_name)
    if not current_user:
        return HTMLResponse("使用者錯誤", status_code=401)
    
    freelancer_id = current_user['id']
    myRole = current_user['role']
    
    project_list = await posts.get_projects_by_freelancer(conn, freelancer_id)
    
    # 定義台灣時區
    tw_tz = ZoneInfo("Asia/Taipei")

    for item in project_list:
        d_dt = item.get('deadline_datetime')
        
        # 如果資料庫沒存絕對時間，才勉強用 create_time + deadline 分鐘數
        if d_dt is None and item.get('create_time') and item.get('deadline') is not None:
             d_dt = item['create_time'] + timedelta(minutes=item['deadline'])

        if d_dt:
            # 如果資料庫拿出來的是 Naive (沒有時區資訊，通常是 UTC)，先視為 UTC
            if d_dt.tzinfo is None:
                d_dt = d_dt.replace(tzinfo=ZoneInfo("UTC"))
            
            # 強制轉成台灣時間
            item['deadline_date'] = d_dt.astimezone(tw_tz)
        else:
            item['deadline_date'] = None
            
        is_deadline_passed = False
        if item.get("deadline_date"):
            is_deadline_passed = datetime.now(tw_tz) > item["deadline_date"]
            item["is_deadline_passed"] = is_deadline_passed

        item['status_text'] = translate_status(item.get('status', ''))

    return templates.TemplateResponse("partials/my_jobs.html", {
        "request": req,
        "items": project_list,
        "role": myRole
    })
    
@app.post("/api/project/{project_id}/complete", dependencies=[Depends(checkRole("client"))])
async def complete_project(
    req: Request, 
    project_id, 
    conn = Depends(getDB), 
    user_name: str = Depends(get_current_user)
):
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})

    try:
        project = await posts.getPost(conn, project_id)
        if not project or project['client_username'] != user_name:
            raise HTTPException(status_code=403, detail="您沒有權限執行此操作")
        
        if project['status'] != 'delivered':
            raise HTTPException(status_code=400, detail="此專案並非在『已交付』狀態")
        
        # 標記最新版本為已接受
        latest_version = await deliveries.get_latest_delivery_version(conn, project_id)
        if latest_version:
            await deliveries.update_delivery_status(conn, latest_version['id'], 'accepted')


        await posts.update_project_status(conn, project_id, 'completed')
        
        freelancer = await users.get_user_by_username(conn, project['accepted_freelancer_username'])
        await notifications.create_notification(
            conn,
            user_id=freelancer['id'],
            message=f"恭喜！專案「{project['title']}」已被委託人接受並結案。",
            link=f"/page/my-jobs"
        )
        
        client = await users.get_user_by_username(conn, project['client_username'])
        await notifications.create_notification(
            conn,
            user_id=client['id'],
            message=f"專案「{project['title']}」已成功結案。",
            link=f"/page/my-projects/read/{project_id}"
        )
        return JSONResponse(status_code=200, content={"success": True, "message": "專案已成功結案！"})
        
    except Exception as e:
        await conn.rollback()
        return JSONResponse(status_code=500, content={"success": False, "message": f"伺服器錯誤: {str(e)}"})
    

    
@app.get("/page/history", response_class=HTMLResponse)
async def get_history_page(req: Request, conn = Depends(getDB), user:str=Depends(get_current_user)):
    if user is None:
        return HTMLResponse("請先登入", status_code=401)
    
    current_user = await users.get_user_by_username(conn, user)
    user_id = current_user['id']
    
    role = current_user["role"]
    
    history_items = await posts.get_history_projects(conn, user_id, role)
    
    # 定義台灣時區
    tw_tz = ZoneInfo("Asia/Taipei")

    for item in history_items:
        d_dt = item.get('deadline_datetime')
        
        # 如果資料庫沒存絕對時間，才勉強用 create_time + deadline 分鐘數
        if d_dt is None and item.get('create_time') and item.get('deadline') is not None:
             d_dt = item['create_time'] + timedelta(minutes=item['deadline'])

        if d_dt:
            # 如果資料庫拿出來的是 Naive (沒有時區資訊，通常是 UTC)，先視為 UTC
            if d_dt.tzinfo is None:
                d_dt = d_dt.replace(tzinfo=ZoneInfo("UTC"))
            
            # 強制轉成台灣時間
            item['deadline_date'] = d_dt.astimezone(tw_tz)
        else:
            item['deadline_date'] = None

        item['status_text'] = translate_status(item.get('status', ''))

    return templates.TemplateResponse("partials/history.html", {
        "request": req,
        "items": history_items,
        "role": role
    })
    
@app.post("/api/project/{project_id}/restore", dependencies=[Depends(get_current_user)])
async def restore_project_api(
    req: Request, 
    project_id: int, 
    conn = Depends(getDB), 
    user_name: str = Depends(get_current_user)
):
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})

    try:
        current_user = await users.get_user_by_username(conn, user_name)
        role = current_user["role"]
        hostory_items = await posts.get_history_projects(conn, current_user['id'], role)
        
        allowed_ids = [item['id'] for item in hostory_items]
        
        if project_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="您沒有權限執行此操作")

        today = date.today().strftime("%Y-%m-%d")
        
        project = await posts.get_any_post_by_id(conn, project_id)
        project_title = project['title']
        await posts.restore_project(conn, project_id, today)
        if project['client_username'] == user_name: 
            if project['accepted_freelancer_username']:
                freelancer = await users.get_user_by_username(conn, project['accepted_freelancer_username'])
                await notifications.create_notification(
                    conn,
                    user_id=freelancer['id'],
                    message=f"您承接的專案「{project_title}」已被委託人重新發布。",
                    link=f"/page/my-jobs"
                )
        await notifications.create_notification(
            conn,
            user_id=current_user['id'],
            message=f"您的專案「{project_title}」已被重新發布。",
            link=f"/page/my-projects"
            )
        return JSONResponse(status_code=200, content={"success": True, "message": "專案已成功復原！"})

    except Exception as e:
        await conn.rollback()
        return JSONResponse(status_code=500, content={"success": False, "message": f"伺服器錯誤: {str(e)}"})
    
    
@app.get("/api/notifications")
async def get_my_notifications(req: Request, conn = Depends(getDB), user_name:str=Depends(get_current_user)):
    if user_name is None:
        return JSONResponse(status_code=401, content=[])
    
    current_user = await users.get_user_by_username(conn, user_name)
    user_id = current_user['id']
    
    notifs = await notifications.get_notifications_for_user(conn, user_id)
    
    safe_notifs = jsonable_encoder(notifs)
    return JSONResponse(status_code=200, content=safe_notifs)

@app.post("/api/notifications/mark-read")
async def mark_notifications_as_read(req: Request, conn = Depends(getDB), user_name:str=Depends(get_current_user)):
    if user_name is None:
        return JSONResponse(status_code=401)
        
    current_user = await users.get_user_by_username(conn, user_name)
    user_id = current_user['id']
    
    async with conn.cursor() as cur:
        sql = "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE"
        await cur.execute(sql, (user_id,))
        await conn.commit()
    
    return JSONResponse(status_code=200, content={"success": True})

@app.get("/logout")
async def logout(req:Request):
    req.session.clear()
    return RedirectResponse(url="/login.html")

@app.post("/login")
async def login(req:Request, username:str=Form(...), password:str=Form(...), conn = Depends(getDB)):
    user_from_db = await users.get_user_by_username(conn, username)

    if not user_from_db:
        req.session.clear()
        return JSONResponse(status_code=401, content={"success": False, "message": "使用者不存在！請再試一次。"})

    is_password_correct = security.verify_pwd(password, user_from_db["hashed_password"])

    if not is_password_correct:
        req.session.clear()
        return JSONResponse(status_code=401, content={"success": False, "message": "密碼錯誤！請再試一次。"})
    
    req.session["user"] = user_from_db["username"]
    req.session["role"] = user_from_db["role"]

    if user_from_db["role"] == "client":
        print(f"{username} 已登入，登入身分：委託人")
    else:
        print(f"{username} 已登入，登入身分：接案人")
    
    return JSONResponse(status_code=200, content={"success": True, "message": f"登入成功！歡迎， {username}"})






@app.get("/page/project/{project_id}/issues", response_class=HTMLResponse)
async def get_project_issues_page(
    req: Request,
    project_id: int,
    conn = Depends(getDB),
    user_name: str = Depends(get_current_user)
):
    """顯示專案的所有 Issues"""
    if user_name is None:
        return HTMLResponse("請先登入", status_code=401)
    
    current_user = await users.get_user_by_username(conn, user_name)
    project = await posts.getPost(conn, project_id)
    
    if not project:
        return HTMLResponse("<h1>找不到專案</h1>", status_code=404)
    
    
    if (project['client_username'] != user_name and 
        project['accepted_freelancer_username'] != user_name):
        return HTMLResponse("沒有權限", status_code=403)
    
    issues_list = await issues.get_issues_by_project(conn, project_id)
    stats = await issues.get_issue_statistics(conn, project_id)
    role = current_user['role']
    
    for issue in issues_list:
        if issue['created_at'].tzinfo is None:
            issue['created_at'] = issue['created_at'].replace(tzinfo=ZoneInfo("UTC"))
        issue['created_at'] = issue['created_at'].astimezone(ZoneInfo("Asia/Taipei"))
    
    return templates.TemplateResponse("partials/project_issues.html", {
        "request": req,
        "project": project,
        "issues": issues_list,
        "stats": stats,
        "role": role,
        "current_user": user_name
    })


@app.post("/api/project/{project_id}/issue/create", dependencies=[Depends(checkRole("client"))])
async def create_issue_api(
    req: Request,
    project_id: int,
    conn = Depends(getDB),
    user_name: str = Depends(get_current_user),
    title: str = Form(...),
    description: str = Form(...)
):
    """建立新的 Issue (僅委託人)"""
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})
    
    try:
        current_user = await users.get_user_by_username(conn, user_name)
        project = await posts.getPost(conn, project_id)
        
        if not project or project['client_username'] != user_name:
            raise HTTPException(status_code=403, detail="沒有權限")
        
        if project['status'] != 'delivered':
            raise HTTPException(status_code=400, detail="只有已交付的專案才能建立 Issue")
        
        
        new_issue = await issues.create_issue(conn, project_id, current_user['id'], title, description)
        
        
        freelancer = await users.get_user_by_username(conn, project['accepted_freelancer_username'])
        await notifications.create_notification(
            conn,
            user_id=freelancer['id'],
            message=f"專案「{project['title']}」有新的待解決事項：{title}",
            link=f"/page/project/{project_id}/issue/{new_issue['id']}"
        )
        
        return JSONResponse(status_code=201, content={
            "success": True,
            "message": "Issue 建立成功",
            "issue_id": new_issue['id']
        })
        
    except Exception as e:
        await conn.rollback()
        return JSONResponse(status_code=500, content={
            "success": False,
            "message": f"伺服器錯誤: {str(e)}"
        })


@app.get("/page/project/{project_id}/issue/{issue_id}", response_class=HTMLResponse)
async def get_issue_detail_page(
    req: Request,
    project_id: int,
    issue_id: int,
    conn = Depends(getDB),
    user_name: str = Depends(get_current_user)
):
    """顯示 Issue 詳情和留言"""
    if user_name is None:
        return HTMLResponse("請先登入", status_code=401)
    
    current_user = await users.get_user_by_username(conn, user_name)
    project = await posts.getPost(conn, project_id)
    issue = await issues.get_issue_by_id(conn, issue_id)
    
    if issue['created_at'].tzinfo is None:
        issue['created_at'] = issue['created_at'].replace(tzinfo=ZoneInfo("UTC"))
    issue['created_at'] = issue['created_at'].astimezone(ZoneInfo("Asia/Taipei"))
    
    if not project or not issue:
        return HTMLResponse("<h1>找不到資料</h1>", status_code=404)
    
    
    if (project['client_username'] != user_name and 
        project['accepted_freelancer_username'] != user_name):
        return HTMLResponse("沒有權限", status_code=403)
    
    comments = await issues.get_comments_by_issue(conn, issue_id)
    role = current_user['role']
    
    return templates.TemplateResponse("partials/issue_detail.html", {
        "request": req,
        "project": project,
        "issue": issue,
        "comments": comments,
        "role": role,
        "current_user": user_name,
        "user_id": current_user['id']
    })


@app.post("/api/issue/{issue_id}/comment")
async def add_issue_comment_api(
    req: Request,
    issue_id: int,
    conn = Depends(getDB),
    user_name: str = Depends(get_current_user),
    comment: str = Form(...)
):
    """新增 Issue 留言"""
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})
    
    try:
        current_user = await users.get_user_by_username(conn, user_name)
        issue = await issues.get_issue_by_id(conn, issue_id)
        
        if not issue:
            raise HTTPException(status_code=404, detail="找不到 Issue")
        
        project = await posts.getPost(conn, issue['project_id'])
        
        
        if (project['client_username'] != user_name and 
            project['accepted_freelancer_username'] != user_name):
            raise HTTPException(status_code=403, detail="沒有權限")
        
        
        new_comment = await issues.create_issue_comment(conn, issue_id, current_user['id'], comment)
        
        
        
        
        notify_user = None
        if user_name == project['client_username']:
            notify_user = await users.get_user_by_username(conn, project['accepted_freelancer_username'])
        else:
            notify_user = await users.get_user_by_username(conn, project['client_username'])
        
        if notify_user:
            await notifications.create_notification(
                conn,
                user_id=notify_user['id'],
                message=f"{user_name} 在 Issue「{issue['title']}」中留言了",
                link=f"/page/project/{issue['project_id']}/issue/{issue_id}"
            )
        
        return JSONResponse(status_code=201, content={
            "success": True,
            "message": "留言成功"
        })
        
    except Exception as e:
        await conn.rollback()
        return JSONResponse(status_code=500, content={
            "success": False,
            "message": f"伺服器錯誤: {str(e)}"
        })


@app.post("/api/issue/{issue_id}/resolve", dependencies=[Depends(checkRole("client"))])
async def resolve_issue_api(
    req: Request,
    issue_id: int,
    conn = Depends(getDB),
    user_name: str = Depends(get_current_user)
):
    """將 Issue 設為已解決 (僅委託人)"""
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})
    
    try:
        issue = await issues.get_issue_by_id(conn, issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="找不到 Issue")
        
        project = await posts.getPost(conn, issue['project_id'])
        
        if project['client_username'] != user_name:
            raise HTTPException(status_code=403, detail="沒有權限")
        
        
        await issues.update_issue_status(conn, issue_id, 'resolved')
        
        
        freelancer = await users.get_user_by_username(conn, project['accepted_freelancer_username'])
        await notifications.create_notification(
            conn,
            user_id=freelancer['id'],
            message=f"Issue「{issue['title']}」已被標記為已解決",
            link=f"/page/project/{issue['project_id']}/issue/{issue_id}"
        )
        
        
        all_resolved = await issues.check_all_issues_resolved(conn, issue['project_id'])
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Issue 已標記為已解決",
            "all_resolved": all_resolved
        })
        
    except Exception as e:
        await conn.rollback()
        return JSONResponse(status_code=500, content={
            "success": False,
            "message": f"伺服器錯誤: {str(e)}"
        })


@app.post("/api/issue/{issue_id}/reopen", dependencies=[Depends(checkRole("client"))])
async def reopen_issue_api(
    req: Request,
    issue_id: int,
    conn = Depends(getDB),
    user_name: str = Depends(get_current_user)
):
    """重新開啟 Issue (僅委託人)"""
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})
    
    try:
        issue = await issues.get_issue_by_id(conn, issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="找不到 Issue")
        
        project = await posts.getPost(conn, issue['project_id'])
        
        if project['client_username'] != user_name:
            raise HTTPException(status_code=403, detail="沒有權限")
        
        await issues.update_issue_status(conn, issue_id, 'open')
        
        
        freelancer = await users.get_user_by_username(conn, project['accepted_freelancer_username'])
        await notifications.create_notification(
            conn,
            user_id=freelancer['id'],
            message=f"Issue「{issue['title']}」已被重新開啟",
            link=f"/page/project/{issue['project_id']}/issue/{issue_id}"
        )
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Issue 已重新開啟"
        })
        
    except Exception as e:
        await conn.rollback()
        return JSONResponse(status_code=500, content={
            "success": False,
            "message": f"伺服器錯誤: {str(e)}"
        })
        
@app.post("/api/submit-review/{project_id}")
async def submit_review(
    req: Request,
    project_id: int,
    conn = Depends(getDB),
    user_name = Depends(get_current_user),
    score_1: int = Form(...),
    score_2: int = Form(...),
    score_3: int = Form(...),
    comment: str = Form(...)
):
    if not user_name:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})
       
    try:
        current_user = await users.get_user_by_username(conn, user_name)
        project = await posts.get_any_post_by_id(conn, project_id)
       
        target_user_id = None
        target_role = ""
       
        #委託人
        if current_user["id"] == project["user_id"]:
            target_user_id = project["accepted_freelancer_id"]
            target_role = "freelancer"
        elif current_user["id"] == project["accepted_freelancer_id"]:
            target_user_id = project["user_id"]
            target_role = "client"
        else:
            return JSONResponse(status_code=403, content={"success": False, "detail": "您無權評價此專案"})
       
        if project["status"] != "completed":
            return JSONResponse(status_code=400, content={"success": False, "detail": "專案尚未結案，無法評價"})
       
        if await reviews.check_if_reviewed(conn, project_id, current_user["id"]):
            return JSONResponse(status_code=400, content={"success": False, "detail": "您已經評價過此專案"})
       
        await reviews.create_review(conn, project_id, current_user["id"], target_user_id, target_role, score_1, score_2, score_3, comment)
        await conn.commit()
        
        
        
        project_title = project['title']
        notify_msg = f"專案「{project_title}」收到了一則來自 {current_user['username']} 的新評價！"
        notify_msg2 = f"您已完成對專案「{project_title}」合作夥伴 {project['accepted_freelancer_username']} 的評價！"
        notify_link = f"/page/my-projects/read/{project_id}"
        
        await notifications.create_notification(conn, target_user_id, notify_msg, notify_link)
        await notifications.create_notification(conn, current_user["id"], notify_msg2, notify_link)
        
        return JSONResponse(status_code=200, content={"success": True, "message": "評價送出成功！"})
    except Exception as e:
        await conn.rollback()
        print(f"評價錯誤: {e}")
        return JSONResponse(status_code=500, content={"success": False, "detail": f"伺服器錯誤: {str(e)}"})

@app.post("/register")
async def register_user(req: Request, conn = Depends(getDB), username: str = Form(...), password: str = Form(...), role: str = Form(...)):
    existin_user = await users.get_user_by_username(conn, username)
    if existin_user:
        return JSONResponse(status_code=400, content={"success": False, "message": "該使用者名稱已被註冊"})
    
    if role not in ['client', 'freelancer']:
        return JSONResponse(status_code=400, content={"success": False, "message": "無效的身分！"})
    
    hashed_password = security.get_pwd_hash(password)

    try:
        await users.create_user(conn, username, hashed_password, role)
        return JSONResponse(status_code=201, content={"success": False, "message": f"註冊成功！歡迎，{username}"})
    except Exception as e:
        print(f": {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": ""})
    
app.mount("/", StaticFiles(directory="html"))
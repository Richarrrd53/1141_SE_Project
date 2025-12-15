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
import security

from datetime import date
from datetime import timedelta
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

    for item in myList:
        # 優先使用 deadline_datetime，如果不存在則回退到舊的計算方式
        if item.get('deadline_datetime'):
            item['deadline_date'] = item['deadline_datetime']
        elif item.get('create_time') and item.get('deadline') is not None:
            item['deadline_date'] = item['create_time'] + timedelta(minutes=item['deadline'])
        else:
            item['deadline_date'] = None

        item['status_text'] = translate_status(item.get('status', ''))
    

    return templates.TemplateResponse("partials/my_projects.html", {
        "request": req,
        "items": myList,
        "role_text": role_text,
        "role": myRole,
        "username": user
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
async def create_project(req: Request, conn = Depends(getDB), user_name: str = Depends(get_current_user),title: str = Form(...),content: str = Form(...),budget = Form(...),deadline: str = Form(...)):
    if user_name is None:
        return JSONResponse(status_code=401, content={"success": False, "message": "請先登入"})
    try:
        from datetime import datetime
        now = datetime.now()

        user = await users.get_user_by_username(conn, user_name)
        if not user:
            raise HTTPException(status_code=404, detail="找不到使用者")
        
        user_id = user['id']
        
        # 將前端傳來的 datetime-local 字串轉換為 datetime 物件
        deadline_dt = datetime.fromisoformat(deadline)
        
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
    
    import model.deliveries as deliveries
    
    project_detail = await posts.getPost(conn, id)
    if not project_detail:
        return HTMLResponse("<h1>404 - 找不到專案</h1>", status_code=404)
    

    
    # 優先使用 deadline_datetime
    if project_detail.get("deadline_datetime"):
        project_detail["deadline_date"] = project_detail["deadline_datetime"]
    elif project_detail.get("create_time") and project_detail.get("deadline") is not None:
        project_detail["deadline_date"] = project_detail["create_time"] + timedelta(minutes=project_detail["deadline"])
    else:
        project_detail["deadline_date"] = None

    project_detail["status_text"] = translate_status(project_detail.get("status", ""))
    
    # 檢查是否已過截止日期
    from datetime import datetime
    is_deadline_passed = False
    if project_detail.get("deadline_date"):
        is_deadline_passed = datetime.now() > project_detail["deadline_date"]
    
    # 取得所有交付版本
    delivery_versions = await deliveries.get_all_delivery_versions(conn, id)
    
    role = get_current_role(req)
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
            "is_deadline_passed": is_deadline_passed
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
            "is_deadline_passed": is_deadline_passed
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
    
    for item in project_list:
        if item.get('deadline_datetime'):
            item['deadline_date'] = item['deadline_datetime']
        elif item.get('create_time') and item.get('deadline') is not None:
            item['deadline_date'] = item['create_time'] + timedelta(minutes=item['deadline'])
        else:
            item['deadline_date'] = None

    return templates.TemplateResponse("partials/browse_projects.html", {
        "request": req,
        "items": project_list,
        "role": myRole
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
    
    # 驗證檔案格式
    if not proposal_file.filename.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"success": False, "message": "提案計畫書必須為 PDF 格式"})
    
    try:
        from datetime import datetime
        
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
        safe_filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', proposal_file.filename)
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
        import model.deliveries as deliveries
        
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
        import model.deliveries as deliveries
        
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
    
    for item in project_list:
        if item.get('deadline_datetime'):
            item['deadline_date'] = item['deadline_datetime']
        elif item.get('create_time') and item.get('deadline') is not None:
            item['deadline_date'] = item['create_time'] + timedelta(minutes=item['deadline'])
        else:
            item['deadline_date'] = None
        
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
        import model.deliveries as deliveries
        
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
    
    for item in history_items:
        if item.get('deadline_datetime'):
            item['deadline_date'] = item['deadline_datetime']
        elif item.get('create_time') and item.get('deadline') is not None:
            item['deadline_date'] = item['create_time'] + timedelta(minutes=item['deadline'])
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
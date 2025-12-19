function $(str){
    return document.getElementById(str);
}

let tempLinks = [];
let tempLinksSrc = [];
let tempList = [];
let tempPage = 0;


document.addEventListener("DOMContentLoaded", () => {
    const vmenuLinks = $("vmenuContainer").children[0];
    for (let i = 0; i < vmenuLinks.children.length; i++){
        tempLinks.push(vmenuLinks.children[i].children[0].children[1].textContent);
        tempLinksSrc.push(vmenuLinks.children[i].children[0].children[0].src);
        vmenuLinks.children[i].children[0].children[1].textContent = "";
        vmenuLinks.children[i].children[0].style.width = 20 + "px";
    }
    checkNotifications();
    if($("menu-client")){
        tempPage = 0;
        menuLinkClick(1);
    }
    if($("menu-freelancer")){
        tempPage = 0;
        menuLinkClick(5);
    }

    $("logoSection").addEventListener("click", () => {
        if($("menu-client")){
            tempPage = 0;
            menuLinkClick(1);
        }
        if($("menu-freelancer")){
            tempPage = 0;
            menuLinkClick(5);
        }
    });
    
    setTimeout(() => {
        document.body.style.opacity = 1;
    }, 1000);
    $("label-check2").addEventListener("click", () => {
        if($("notifyCheck").checked){
            $("notifyBell").click();
        }
        let isChecked = $("label-check").checked;
        if(!isChecked){
            $("mainContent").style.width = "calc(100% - 116px - 80px - 30px - 10px - 200px)";
            $("mainContent").style.left = 316 + "px";
            for (let i = 0; i < vmenuLinks.children.length; i++){
                vmenuLinks.children[i].children[0].children[1].textContent = tempLinks[i];
                vmenuLinks.children[i].children[0].style.width = 210 + "px";
            }
        }
        else{
            $("mainContent").style.width = "calc(100% - 116px - 80px - 30px - 10px)";
            $("mainContent").style.left = 116 + "px";
            for (let i = 0; i < vmenuLinks.children.length; i++){
                vmenuLinks.children[i].children[0].children[1].textContent = "";
                vmenuLinks.children[i].children[0].style.width = 20 + "px";
            }
        }
    });

    $("notifyBell").addEventListener("click", () => {
        if($("label-check").checked){
            $("label-check2").click();
        }
        let isChecked = $("notifyCheck").checked;
        if(!isChecked){
            $("mainContent").style.width = "calc(100% - 116px - 80px - 30px - 10px - 400px - 40px)";
            $("notifyDropdown").style.right = 10 + "px";
            $("notifyBell").children[0].src = $("notifyBell").children[0].src.replace("blur", "focus");
            checkNotifications();

        }
        else{
            $("mainContent").style.width = "calc(100% - 116px - 80px - 30px - 10px)";
            $("notifyDropdown").style.right = -420 + "px";
            $("notifyBell").children[0].src = $("notifyBell").children[0].src.replace("focus", "blur");
        }
    });
    let vmenuTimer;
    $("vmenuContainer").addEventListener("mouseover", () => {
        clearTimeout(vmenuTimer);
        vmenuTimer = setTimeout(() => {
            if(!$("label-check").checked){
                $("label-check2").click();
            }
        }, 500);
    });
    $("vmenuContainer").addEventListener("mouseleave", () => {
        clearTimeout(vmenuTimer);
    });
    let mainTimer;
    $("mainContent").addEventListener("mouseover", () => {
        clearTimeout(mainTimer);
        mainTimer = setTimeout(() => {
            if($("label-check").checked){
                $("label-check2").click();
            }
        }, 1000);
    });
    $("mainContent").addEventListener("mouseleave", () => {
        clearTimeout(mainTimer);
    });
});


function menuLinkClick(n){
    if(tempPage == n){
        return false;
    }
    else{
        tempPage = n;
        const vmenuLinks = $("vmenuContainer").children[0];
    
        for (let i = 0; i < vmenuLinks.children.length; i++){
            vmenuLinks.children[i].children[0].classList.remove("checked");
            vmenuLinks.children[i].children[0].children[0].src = tempLinksSrc[i];
        }
        let index = (n-1)%4 +1;
        $("menuLink"+index).classList.add("checked");
        $("menuLink"+index).children[0].src = tempLinksSrc[index-1].replace("blur", "focus");
        switch (n){
            case 1:
                loadContent("/page/my-projects");
                break;
            case 2:
                loadContent("/page/create-project");
                break;
            case 3:
                loadContent("/page/history");
                break;
            case 4:
                notifyWindow("是否要登出？", "登出", "logout", 0, false);
                break;
            case 5:
                loadContent("/page/browse-projects");
                break;
            case 6:
                loadContent("/page/my-jobs");
                break;
            case 7:
                loadContent("/page/history");
                break;
            case 8:
                notifyWindow("是否要登出？", "登出", "logout", 0, false);
                break;
        }
    }
}


async function loadContent(url) {
    try {
        if(tempPage == 1 && url != "/page/my-projects"){
            tempPage = 0;
        }
        $("contentArea").style.opacity = 0;
        $("contentArea").style.filter = "blur(20px)";
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch(url, { method: "GET"});

        if (!response.ok) {
            throw new Error(`HTTP 錯誤! 狀態: ${response.status}`);
        }

        const htmlContent = await response.text();
        $("mainContent").innerHTML = htmlContent;
        checkNotifications();
        if(url == "/page/create-project"){
            setTimeout(() => {
                
                $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
                $("loading").style.opacity = 0;
                $("loading").style.scale = 0;
                $("loading").style.filter = "blur(20px)";
                $("contentArea").style.opacity = 1;
                $("contentArea").style.filter = "blur(0px)";
            }, 510);
        }
        else{
            setTimeout(() => {
                
                $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
                $("loading").style.opacity = 0;
                $("loading").style.scale = 0;
                $("loading").style.filter = "blur(20px)";
                $("contentArea").style.transition = "all 0.5s cubic-bezier(.31,.01,.66,-0.59)";
                $("contentArea").style.opacity = 1;
                $("contentArea").style.scale = 1;
                $("contentArea").style.filter = "blur(0px)";
            }, 10);
        }

        
    } catch (error) {
        console.error('載入內容時發生錯誤:', error);
        $("mainContent").innerHTML = "<h1>內容載入失敗</h1>";
    }
}

async function deletePost(n) {
    notifyCancel($("notifyWindowBG"), $("notifyWindow"));
    try{
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch(`/page/my-projects/delete/${n}`, { method: "DELETE", credentials: "include"});
        const data = await response.json();

        if(response.ok){
            setTimeout(() => {
                notifyWindow("刪除成功！","","alert",0,false);
            }, 500);
            tempPage = 0;
            menuLinkClick(1);
        }
        else {
            setTimeout(() => {
                notifyWindow("錯誤："+data.detail,"","alert",0,false);
                loadContent(`/page/my-projects/read/${n}`);
            }, 500);
        }
        
    } catch (error) {
        console.error('載入內容時發生錯誤:', error);
        $("mainContent").innerHTML = "<h1>內容載入失敗</h1>";
    }
}



async function editorSubmit(){
    notifyCancel($("notifyWindowBG"), $("notifyWindow"));
    $("content").value = $("description").value;
    const formElement = document.getElementsByClassName("editForm")[0];
    const formData = new FormData(formElement);
    const id = formElement.id.split("-")[2];
    try{
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch(`/page/my-projects/edit/${id}`,{method: "POST",body: formData});
        const data = await response.json();
        if (response.ok) {
            setTimeout(() => {
                notifyWindow(data.message,"","alert",0,false);
            }, 500);
            loadContent(`/page/my-projects/read/${id}`);
        } else {
            setTimeout(() => {
                notifyWindow("錯誤："+data.detail,"","alert",0,false);
                loadContent(`/page/my-projects/read/${id}`);
            }, 500);
        }
    } catch (error) {
        console.error('載入內容時發生錯誤222:', error);
        $("mainContent").innerHTML = `<h1>${error}</h1>`;
    }
}

function notifyWindow(str, str2, fun, n, color){
    const bg = document.createElement("div");
    bg.id = "notifyWindowBG";
    document.body.appendChild(bg);

    const window = document.createElement("div");
    window.id = "notifyWindow";
    bg.appendChild(window);

    const title = document.createElement("h1");
    title.textContent = str;
    window.appendChild(title);

    const btnContainer = document.createElement("div");
    btnContainer.id = "notifyBtnContainer";
    window.appendChild(btnContainer);

    const btn1 = document.createElement("button");
    btn1.classList.add("notifyBtns");
    btn1.onclick = () => {notifyCancel(bg, window)};
    btn1.textContent = "取消"
    if(color){
        btn1.classList.add("deleteBtn");
    }
    if (fun == "logout"){
        btn1.onclick = () => {notifyCancel(bg, window); if($("menu-client")){menuLinkClick(1);}if($("menu-freelancer")){menuLinkClick(5);}};
    }
    if(fun != "alert"){
        btnContainer.appendChild(btn1);
    }

    const btn2 = document.createElement("button");
    btn2.classList.add("notifyBtns");
    btn2.textContent = str2;
    if(color){
        btn2.classList.add("deleteBtn");
    }
    if(fun == "delete"){
        btn2.onclick = () => {deletePost(n)};
    }
    else if (fun == "logout"){
        btn2.onclick = () => {notifyCancel($("notifyWindowBG"), $("notifyWindow")); setTimeout(() => {globalThis.location.href = "/logout"}, 700);};
    }
    else if (fun == "create") {
        btn2.onclick = () => { submitCreateProject() };
    }
    else if (fun == "edit"){
        btn2.onclick = () => {editorSubmit()};
    }
    else if(fun == "sendBid"){
        btn2.onclick = () => {submitBids()};
    }
    else if (fun == "accept_bid") {
        btn2.onclick = () => { submitAcceptBid(n)};
    }
    else if (fun == "upload"){
        btn2.onclick = () => { submitDelivery(n);};
    }
    else if (fun == "accept_delivery") {
        btn2.onclick = () => { submitAcceptDelivery(n) };
    }
    else if (fun == "reject_delivery") {
        btn2.onclick = () => { submitRejectDelivery(n) };
    }
    else if (fun == "restore") {
        btn2.onclick = () => { submitRestoreProject(n) };
    }
    else if (fun == "create_review") {
        btn2.onclick = () => { submitCreateReview(n) };
    }
    if(fun != "alert"){
        btnContainer.appendChild(btn2);
    }

    setTimeout(() => {
        bg.style.background = "rgba(46, 46, 46, 0.2)";
        bg.style.backdropFilter = "blur(40px)";
        window.style.scale = 1;
        window.style.filter = "blur(0)";
    }, 10);

    if(fun == "alert"){
        setTimeout(() => {
            notifyCancel(bg, window);
        }, 2000);
    }
}

function notifyCancel(bg, window){
    bg.style.background = "rgba(46, 46, 46, 0)";
    bg.style.backdropFilter = "blur(0px)";
    window.style.transition = "all 0.5s cubic-bezier(.31,.01,.66,-0.59)";
    window.style.scale = 0;
    window.style.filter = "blur(20)";
    setTimeout(() => {
        bg.remove();
    }, 1000);
}


async function submitCreateProject() {
    notifyCancel($("notifyWindowBG"), $("notifyWindow"));
    $("content").value = $("description").value;
    const formElement = $("create-project-form");
    const formData = new FormData(formElement);
    try{
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch(`/page/create-project`,{method: "POST", body: formData});
        const data = response.json();
        if(response.ok){
            tempPage = 0;
            menuLinkClick(1);
            setTimeout(() => {
                notifyWindow("專案建立成功！","","alert",0,false);
            }, 500);
        }
        else{
            console.error('建立失敗:', data.message);
            setTimeout(() => {
                notifyWindow("建立專案失敗：" + data.detial,"","alert",0,false);
            }, 500);
            menuLinkClick(1);
        }
    } catch (error) {
        console.error('建立專案時發生錯誤:', error);
        alert("發生網路錯誤，請稍後再試。");
    }
}

async function submitBids(){
    notifyCancel($("notifyWindowBG"), $("notifyWindow"));
    const formElement = $("create-bid-form");
    const formData = new FormData(formElement);
    try {
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch("/api/project/bid", {
            method: "POST",
            body: formData,
            credentials: "include"
        });

        const data = await response.json();

        if (response.ok) {
            loadContent(`/page/my-projects/read/${formData.get('project_id')}`);
            setTimeout(() => {
                notifyWindow(data.message,"","alert",0,false);
            }, 500);
        } else {
            setTimeout(() => {
                notifyWindow("錯誤：" + data.detial,"","alert",0,false);
            }, 500);
            loadContent(`/page/my-projects/read/${formData.get('project_id')}`);
        }
    } catch (error) {
        console.error(':', error);
        alert("");
    }
}

async function submitAcceptBid(bid_id) {
    notifyCancel($("notifyWindowBG"), $("notifyWindow"));

    try {
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch(`/api/project/accept-bid/${bid_id}`, {
            method: "POST",
            credentials: "include"
        });

        const data = await response.json();

        if (response.ok) {
            setTimeout(() => {
                notifyWindow(data.message,"","alert",0,false);
            }, 500);
            menuLinkClick(1);
        } else {
            setTimeout(() => {
                notifyWindow("錯誤：" + data.detial,"","alert",0,false);

            }, 500);
            menuLinkClick(1);
        }
    } catch (error) {
        console.error(':', error);
        alert("");
    }
}

async function submitDelivery(n){
    notifyCancel($("notifyWindowBG"), $("notifyWindow"));
    const formElement = $("deliver-project-form");
    const formData = new FormData(formElement);
    try {
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch(`/api/project/${n}/deliver`, {
            method: "POST",
            body: formData,
            credentials: "include"
        });

        const data = await response.json();

        if (response.ok) {
            loadContent(`/page/my-projects/read/${n}`);
            setTimeout(() => {
                notifyWindow(data.message,"","alert",0,false);
            }, 500);
        } else {
            setTimeout(() => {
                notifyWindow("錯誤："+data.detail,"","alert",0,false);
            }, 500);
            loadContent(`/page/my-projects/read/${n}`);
        }
    } catch (error) {
        console.error(':', error);
        alert("");
    }
}

async function submitAcceptDelivery(project_id) {
    notifyCancel($("notifyWindowBG"), $("notifyWindow"));
    try {
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch(`/api/project/${project_id}/complete`, {
            method: "POST",
            credentials: "include"
        });
        const data = await response.json();

        if (response.ok) {
            setTimeout(() => {
                notifyWindow(data.message,"","alert",0,false);
            }, 500);
            loadContent(`/page/my-projects/read/${project_id}`);
        } else {
            setTimeout(() => {
                notifyWindow("錯誤："+data.detail,"","alert",0,false);
            }, 500);
            loadContent(`/page/my-projects/read/${project_id}`);
        }
    } catch (error) {
        console.error(':', error);
    }
}

async function submitRejectDelivery(project_id) {
    notifyCancel($("notifyWindowBG"), $("notifyWindow"));
    try {
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch(`/api/project/${project_id}/reject`, {
            method: "POST",
            credentials: "include"
        });
        const data = await response.json();

        if (response.ok) {
            setTimeout(() => {
                notifyWindow(data.message,"","alert",0,false);
            }, 500);
            loadContent(`/page/my-projects/read/${project_id}`);
        } else {
            setTimeout(() => {
                notifyWindow("錯誤："+data.detail,"","alert",0,false);
            }, 500);
            loadContent(`/page/my-projects/read/${project_id}`);
        }
    } catch (error) {
        console.error(':', error);
    }
}

async function submitRestoreProject(project_id) {
    notifyCancel($("notifyWindowBG"), $("notifyWindow"));
    try {
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch(`/api/project/${project_id}/restore`, {
            method: "POST",
            credentials: "include"
        });
        const data = await response.json();

        if (response.ok) {
            setTimeout(() => {
                notifyWindow(data.message,"","alert",0,false);
            }, 500);
            loadContent("/page/history");
        } else {
            setTimeout(() => {
                notifyWindow("錯誤："+data.detail,"","alert",0,false);
            }, 500);
            loadContent("/page/history");
        }
    } catch (error) {
        console.error(':', error);
    }
}

async function submitCreateReview(project_id) {
    notifyCancel($("notifyWindowBG"), $("notifyWindow"));
    const formElement = $("create-review-form");
    const formData = new FormData(formElement);
    try{
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        const response = await fetch(`/api/submit-review/${project_id}`, {
            method: "POST",
            body: formData,
            credentials: "include"
        });
        const data = await response.json();

        if (response.ok) {
            setTimeout(() => {
                notifyWindow(data.message,"","alert",0,false);
            }, 500);
            loadContent(`/page/my-projects/read/${project_id}`);
        } else {
            setTimeout(() => {
                notifyWindow("錯誤："+data.detail,"","alert",0,false);
                loadContent(`/page/my-projects/read/${project_id}`);
            }, 500);
        }
    } catch (error) {
        console.error(':', error);
    }
}

async function submitCreateIssue(projectId) {
    console.log('submitCreateIssue 被調用, projectId:', projectId);
    
    const formElement = $('create-issue-form');
    const titleInput = $('issue-title');
    const descInput = $('issue-description');
    const submitBtn = $('create-issue-btn');
    
    if (!formElement) {
        console.error('找不到表單元素');
        alert('表單載入錯誤，請重新整理頁面');
        return;
    }
    
    
    if (!titleInput || !titleInput.value.trim()) {
        alert('請輸入標題');
        if (titleInput) titleInput.focus();
        return;
    }
    
    if (!descInput || !descInput.value.trim()) {
        alert('請輸入詳細說明');
        if (descInput) descInput.focus();
        return;
    }
    const formData = new FormData(formElement);
    
    try {
        
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        
        const response = await fetch(`/api/project/${projectId}/issue/create`, {
            method: "POST",
            body: formData,
            credentials: "include"
        });
        const data = await response.json();
        
        if (response.ok) {
            
            loadContent(`/page/project/${projectId}/issues`);
            setTimeout(() => {
                notifyWindow("Issue 建立成功!", "", "alert", 0, false);
            }, 500);
        } else {
            setTimeout(() => {
                notifyWindow("錯誤: " + (data.detail || '建立失敗'), "", "alert", 0, false);
            }, 500)
            loadContent(`/page/project/${projectId}/issues`);
        }
    } catch (error) {
        console.error('建立 Issue 時發生錯誤:', error);
        notifyWindow("發生網路錯誤: " + (error.detail || '建立失敗'), "", "alert", 0, false);
    }
}

async function submitComment(issueId) {
    
    const formElement = document.getElementsByClassName('comment-form')[0];
    const project_id = formElement.id.split("-")[3];
    const commentInput = $('comment-text');
    
    if (!formElement || !commentInput) {
        alert('表單載入錯誤');
        return;
    }
    
    const formData = new FormData(formElement);
    
    if (!formData.get('comment').trim()) {
        alert('留言內容不能為空');
        commentInput.focus();
        return;
    }
    
    try {
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        
        const response = await fetch(`/api/issue/${issueId}/comment`, {
            method: "POST",
            body: formData,
            credentials: "include"
        });
        
        const data = await response.json();
        
        if (response.ok) {
            

            loadContent(`/page/project/${project_id}/issue/${issueId}`);
            setTimeout(() => {
                notifyWindow("留言成功!", "", "alert", 0, false);
            }, 500);
        } else {
            loadContent(`/page/project/${project_id}/issue/${issueId}`);
            setTimeout(() => {
                notifyWindow("錯誤: " + data.detial, "", "alert", 0, false);
            }, 500);
        }
    } catch (error) {
        console.error('建立 Issue 時發生錯誤:', error);
        notifyWindow("發生網路錯誤: " + (error.detail || '建立失敗'), "", "alert", 0, false);
    }
}

async function resolveIssue(issueId) {
    try {
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        
        const response = await fetch(`/api/issue/${issueId}/resolve`, {
            method: "POST",
            credentials: "include"
        });
        
        const data = await response.json();
        
        const issueMainCard = document.getElementsByClassName('issue-main-card')[0];
        const projectId = issueMainCard.id.split("-")[1];
        if (response.ok) {
            
            loadContent(`/page/project/${projectId}/issue/${issueId}`);
            setTimeout(() => {
                notifyWindow(data.message, "", "alert", 0, false);
                if (data.all_resolved) {
                    setTimeout(() => {
                        notifyWindow("所有 Issue 都已解決!您現在可以結案了", "", "alert", 0, false);
                    }, 2500);
                }
            }, 500);
        } else {
            setTimeout(() => {
                notifyWindow("錯誤: " + data.detail, "", "alert", 0, false);
            }, 500);
            loadContent(`/page/project/${projectId}/issue/${issueId}`);
        }
    } catch (error) {
        console.error('建立 Issue 時發生錯誤:', error);
        notifyWindow("發生網路錯誤: " + (error.detail || '建立失敗'), "", "alert", 0, false);
    }
}

async function reopenIssue(issueId) {
    
    try {
        $("loading").style.transition = "all 0.5s cubic-bezier(.33,1.53,.69,.99)";
        setTimeout(() => {
            $("loading").style.opacity = 1;
            $("loading").style.scale = 1;
            $("loading").style.filter = "blur(0)";
        }, 10);
        
        const response = await fetch(`/api/issue/${issueId}/reopen`, {
            method: "POST",
            credentials: "include"
        });
        
        const data = await response.json();
        const issueMainCard = document.getElementsByClassName('issue-main-card')[0];
        const projectId = issueMainCard.id.split("-")[1];
        
        if (response.ok) {
            
            loadContent(`/page/project/${projectId}/issue/${issueId}`);
            setTimeout(() => {
                notifyWindow(data.message, "", "alert", 0, false);
            }, 500);
        } else {
            setTimeout(() => {
                notifyWindow("錯誤: " + data.detail, "", "alert", 0, false);
            }, 500);
            loadContent(`/page/project/${projectId}/issue/${issueId}`);
        }
    } catch (error) {
        console.error('建立 Issue 時發生錯誤:', error);
        notifyWindow("發生網路錯誤: " + (error.detail || '建立失敗'), "", "alert", 0, false);
    }
}




async function checkNotifications() {
    const notifyBell = $("notifyBell");
    const notifyCount = $("notifyCount");
    const notifyDropdown = $("notifyDropdown");

    if (!notifyBell) return;

    try {
        const response = await fetch("/api/notifications");
        const notifs = await response.json();

        if (notifs.length > 0) {
            notifyBell.classList.add("has-unread");
            notifyCount.innerText = notifs.length;
            notifyCount.style.display = 'block';

            notifyDropdown.innerHTML = `<div class="notify-header-title"><img src="./img/bell.svg">通知中心</div>`;
            
            for (const notif of notifs) {
                
                let icon = '<img src="./img/bell.svg"style="filter: invert(51%) sepia(83%) saturate(7493%) hue-rotate(578deg) brightness(95%) contrast(101%);">'; 
                let typeClass = 'type-system';

                if (notif.message.includes("報價") || notif.message.includes("金額")) {
                    icon = '<img src="./img/bid.svg" style="filter: invert(39%) sepia(83%) saturate(7493%) hue-rotate(57deg) brightness(230%) contrast(101%);">';
                    typeClass = 'type-bid';
                } else if (notif.message.includes("結案") || notif.message.includes("成功") || notif.message.includes("接受")) {
                    icon = '<img src="./img/correct.svg">';
                    typeClass = 'type-success';
                } else if (notif.message.includes("刪除") || notif.message.includes("退回") || notif.message.includes("警告")) {
                    icon = '<img src="./img/delete.svg">';
                    typeClass = 'type-alert';
                } else if (notif.message.includes("評價")) {
                    icon = '<img src="./img/star2.svg" style="filter: invert(51%) sepia(83%) saturate(7493%) hue-rotate(774deg) brightness(223%) contrast(101%);">';
                    typeClass = 'type-bid';
                }

                notifyDropdown.innerHTML += `
                    <li class="notify-item" onclick="loadContentAndMarkRead('${notif.link}'); closeNotification();">
                        <div class="notify-icon-box ${typeClass}">
                            ${icon}
                        </div>
                        <div class="notify-content">
                            <a class="notifyLinks" href="javascript:void(0);">
                                ${notif.message}
                            </a>
                            <span class="notify-time">${notif.time || '剛剛'}</span>
                        </div>
                    </li>
                `;
            }
        } else {
            notifyBell.classList.remove("has-unread");
            notifyCount.style.display = 'none';
            notifyDropdown.innerHTML = `
                <div class="notify-header-title"><img src="./img/bell.svg">通知中心</div>
                <div style="text-align: center; color: #9ca3af; padding: 40px;">
                    <img src="./img/empty_box.svg" style="width: 40px; opacity: 0.3; margin-bottom: 10px; display: block; margin: 0 auto 10px;">
                    目前沒有新通知
                </div>
            `;
        }
    } catch (error) {
        console.error("Notification Error:", error);
    }
}

function closeNotification(){
    if($("notifyCheck").checked){
        $("notifyBell").click();
    }
}

async function loadContentAndMarkRead(link) {
    await fetch("/api/notifications/mark-read", {
        method: "POST",
        credentials: "include"
    });
    
    loadContent(link);
    
    checkNotifications();
}



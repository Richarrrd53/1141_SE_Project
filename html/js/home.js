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
    
    setTimeout(() => {
        document.body.style.opacity = 1;
    }, 1000);
    $("label-check2").addEventListener("click", () => {
        if($("notifyCheck").checked){
            $("notifyBell").click();
        }
        let isChecked = $("label-check").checked;
        if(!isChecked){
            $("mainContent").style.width = "calc(100% - 76px - 80px - 30px - 10px - 210px)";
            $("mainContent").style.left = 286 + "px";
            for (let i = 0; i < vmenuLinks.children.length; i++){
                vmenuLinks.children[i].children[0].children[1].textContent = tempLinks[i];
                vmenuLinks.children[i].children[0].style.width = 230 + "px";
            }
        }
        else{
            $("mainContent").style.width = "calc(100% - 76px - 80px - 30px - 10px)";
            $("mainContent").style.left = 76 + "px";
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
            $("mainContent").style.width = "calc(100% - 76px - 80px - 30px - 10px - 400px - 40px)";
            $("notifyDropdown").style.right = 10 + "px";
            $("notifyBell").children[0].src = $("notifyBell").children[0].src.replace("blur", "focus");
            checkNotifications();

        }
        else{
            $("mainContent").style.width = "calc(100% - 76px - 80px - 30px - 10px)";
            $("notifyDropdown").style.right = -420 + "px";
            $("notifyBell").children[0].src = $("notifyBell").children[0].src.replace("focus", "blur");
        }
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
        if(response.ok){
            setTimeout(() => {
                notifyWindow("刪除成功！","","alert",0,false);
            }, 500);
            tempPage = 0;
            menuLinkClick(1);
        }
        else{
            console.error("權限不足或未登入");
            setTimeout(() => {
                notifyWindow("你沒有權限執行此操作！"+response.json().message,"","alert",0,false);
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
        if(response.ok){
            tempPage = 0;
            menuLinkClick(1);
        }
        else{
            console.error('載入內容時發生錯誤111:', error);
            $("mainContent").innerHTML = "<h1>內容載入失敗</h1>";
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
                notifyWindow("建立專案失敗：" + data.message,"","alert",0,false);
            }, 500);
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
                notifyWindow("錯誤：" + data.message,"","alert",0,false);
            }, 500);
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
                notifyWindow("錯誤：" + data.message,"","alert",0,false);

            }, 500);
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
                notifyWindow("錯誤："+data.message,"","alert",0,false);
            }, 500);
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
            loadContent(`/page/my-projects/read/${project_id}`); // 
        } else {
            setTimeout(() => {
                notifyWindow("錯誤："+data.message,"","alert",0,false);
            }, 500);
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
            loadContent(`/page/my-projects/read/${project_id}`); // 
        } else {
            setTimeout(() => {
                notifyWindow("錯誤："+data.message,"","alert",0,false);
            }, 500);
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
                notifyWindow("錯誤："+data.message,"","alert",0,false);
            }, 500);
        }
    } catch (error) {
        console.error(':', error);
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

            notifyDropdown.innerHTML = "";
            for (const notif of notifs) {
                notifyDropdown.innerHTML += `
                    <li class="notify-item">
                        <a class="notifyLinks" onclick="loadContentAndMarkRead('${notif.link}'); closeNotification();">
                            ${notif.message}
                        </a>
                    </li>
                `;
            }
        } else {
            notifyBell.classList.remove("has-unread");
            notifyCount.style.display = 'none';
            notifyDropdown.innerHTML = "<li>目前沒有通知。</li>";
        }
    } catch (error) {
        console.error(":", error);
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
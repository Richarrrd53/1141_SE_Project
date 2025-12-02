function $(str){
    return document.getElementById(str);
}

document.addEventListener("DOMContentLoaded", () => {
    document.body.style.height = window.innerHeight + "px";
    nextPage($("verificationContainer"),$("loginFormSection"),1400,800);
    setTimeout(() => {
        $("mainContainer").style.scale = 1;
    }, 750);

    setTimeout(() => {
        $("loginImg").style.scale = 1;
        $("loginImg").play();
    }, 1000);
    setTimeout(() => {
        $("loginForm").style.scale = 1;
    }, 1250);
    let isShow = false;
    $("show").addEventListener("click", () => {
        $("input-password").style.opacity = 0;
        $("input-password").style.filter = "blur(10px)";
        isShow = !isShow;
        setTimeout(() => {
            $("input-password").type = isShow? "text" : "password";
            $("input-password").style.opacity = 1;
            $("input-password").style.filter = "blur(0px)";
        }, 250);
        $("inputShow2").style.transform = isShow? "translateY(-20px) scaleY(0)" : "translateY(0) scaleY(1)";
        $("inputShowMask2").style.y = isShow? "-157" : "-57";
    });
    $("submitBtn").addEventListener("click", () => {
        if($("input-username").value == "" || $("input-password").value == ""){
            $("errorMessage").style.opacity = 1;
            shake($("mainContainer"));
        }
        else if($("input-username").value != "" && $("input-password").value != ""){
            $("errorMessage").style.opacity = 0;
            nextPage($("loginFormSection"),$("loadingFlex"),400,400);
            $("loadingText").textContent = "正在檢查身分訊息...";
            setTimeout(() => {
                submitForm();
            }, 1000);
        }
    });
    $("signupBtn").addEventListener("click", () => {
        nextPage($("loginFormSection"),$("loadingFlex"),400,400);
        isShow = false;
        $("loadingText").textContent = "請稍後...";
        setTimeout(() => {
            nextPage($("loadingFlex"),$("registerFormSection"),1400,800);
        }, 1750);
        setTimeout(() => {
            $("registerImg").style.scale = 1;
            $("registerImg").play();
        }, 2000);
        setTimeout(() => {
            $("registerForm").style.scale = 1;
        }, 2250);
    });
    $("show2").addEventListener("click", () => {
        $("input-reg-password").style.opacity = 0;
        $("input-reg-password").style.filter = "blur(10px)";
        isShow = !isShow;
        setTimeout(() => {
            $("input-reg-password").type = isShow? "text" : "password";
            $("input-reg-password").style.opacity = 1;
            $("input-reg-password").style.filter = "blur(0px)";
        }, 250);
        $("inputShow4").style.transform = isShow? "translateY(-20px) scaleY(0)" : "translateY(0) scaleY(1)";
        $("inputShowMask4").style.y = isShow? "-157" : "-57";
    });
    $("backToLoginBtn").addEventListener("click", () => {
        nextPage($("registerFormSection"),$("loadingFlex"),400,400);
        isShow = false;
        $("loadingText").textContent = "請稍後...";
        setTimeout(() => {
            nextPage($("loadingFlex"),$("loginFormSection"),1400,800);
        }, 1750);
        setTimeout(() => {
            $("loginImg").style.scale = 1;
            $("loginImg").play();
        }, 2000);
        setTimeout(() => {
            $("loginForm").style.scale = 1;
        }, 2250);
    });
    $("registerBtn").addEventListener("click", () => {
        if($("input-reg-username").value == "" || $("input-reg-password").value == ""){
            $("registerErrorMessage").style.opacity = 1;
            shake($("mainContainer"));
        }
        else if($("input-reg-username").value != "" && $("input-reg-password").value != ""){
            $("registerErrorMessage").style.opacity = 0;
            nextPage($("registerFormSection"),$("loadingFlex"),400,400);
            $("loadingText").textContent = "正在檢查身分訊息...";
            setTimeout(() => {
                submitRegisterForm();
            }, 1000);
        }
    });
});


function shake(item){
    item.classList.remove("shake");
    item.classList.add("shake");
    setTimeout(() => {
        item.classList.remove("shake");
    }, 500);
}

window.addEventListener('resize', () => {
    document.body.style.height = window.innerHeight + "px";
});

function nextPage(from, to, bgW, bgH){
    from.style.opacity = 0;
    from.style.scale = 0;
    from.style.filter = "blur(30px)";
    to.style.display = "flex";
    setTimeout(() => {
        to.style.opacity = 1;
        to.style.scale = 1;
        to.style.filter = "blur(0)";
        $("mainContainer").style.width = bgW + "px";
        $("mainContainer").style.height = bgH + "px";
    }, 100);
    setTimeout(() => {
        from.style.display = "none";
    }, 1000);
}

async function submitForm(){
    const formData = new FormData($("loginForm2"));
    try{
        const response = await fetch("/login", {method: "POST", body: formData});
        const data = await response.json();
        if(response.ok){
            $("verificationContainerError").style.display = "none";
            $("verificationContainerCorrect").style.display = "block";
            $("verificationContainerText1").style.display = "none";
            $("verificationContainerText2").style.display = "block";
            $("verificationContainerText2").innerText = data.message;
            
            setTimeout(() => {
                nextPage($("loadingFlex"),$("verificationContainer"), 500, 500);
            }, 500);
            setTimeout(() => {
                $("verificationContainerCorrect").play();
            }, 1000);
            setTimeout(() => {
                $("mainContainer").style.transition = "all 0.5s cubic-bezier(.31,.01,.66,-0.59)";
                $("verificationContainerG").style.transition = "all 0.5s cubic-bezier(.31,.01,.66,-0.59)";
                $("verificationContainerG").style.scale = 3;
                $("verificationContainerG").style.opacity = 0;
                $("verificationContainerG").style.filter = "blur(30px)";
                $("mainContainer").style.width = 2000 + "px";
                $("mainContainer").style.height = 1200 + "px";
            }, 3000);
            setTimeout(() => {
                window.location.href = '/';
            }, 3500);

        }
        else{
            $("verificationContainerError").style.display = "block";
            $("verificationContainerCorrect").style.display = "none";
            $("verificationContainerText1").style.display = "block";
            $("verificationContainerText2").style.display = "none";
            $("verificationContainerText1").innerText = data.message;
            setTimeout(() => {
                nextPage($("loadingFlex"),$("verificationContainer"), 500, 500);
            }, 500);
            
            setTimeout(() => {
                nextPage($("verificationContainer"),$("loginFormSection"),1400,800);
                
            }, 3000);
        }
    }

    catch (error) {
        console.error('登入時發生錯誤:', error);
    }
}


async function submitRegisterForm(){
    const formData = new FormData($("registerForm2"));
    try{
        const response = await fetch("/register", {method: "POST", body: formData});
        const data = await response.json();
        if(response.ok){
            $("verificationContainerError").style.display = "none";
            $("verificationContainerCorrect").style.display = "block";
            $("verificationContainerText1").style.display = "none";
            $("verificationContainerText2").style.display = "block";
            $("verificationContainerText2").innerText = data.message;

            $("input-username").value = $("input-reg-username").value;
            $("input-password").value = $("input-reg-password").value;
            submitForm();

            // setTimeout(() => {
            //     nextPage($("loadingFlex"),$("verificationContainer"), 500, 500);
            // }, 500);
            // setTimeout(() => {
            //     $("verificationContainerCorrect").play();
            // }, 1000);
            // setTimeout(() => {
            //     $("mainContainer").style.transition = "all 0.5s cubic-bezier(.31,.01,.66,-0.59)";
            //     $("verificationContainerG").style.transition = "all 0.5s cubic-bezier(.31,.01,.66,-0.59)";
            //     $("verificationContainerG").style.scale = 3;
            //     $("verificationContainerG").style.opacity = 0;
            //     $("verificationContainerG").style.filter = "blur(30px)";
            //     $("mainContainer").style.width = 2000 + "px";
            //     $("mainContainer").style.height = 1200 + "px";
            // }, 3000);
            // setTimeout(() => {
            //     window.location.href = '/';
            // }, 3500);

        }
        else{
            $("verificationContainerError").style.display = "block";
            $("verificationContainerCorrect").style.display = "none";
            $("verificationContainerText1").style.display = "block";
            $("verificationContainerText2").style.display = "none";
            $("verificationContainerText1").innerText = data.message;
            setTimeout(() => {
                nextPage($("loadingFlex"),$("verificationContainer"), 500, 500);
            }, 500);
            
            setTimeout(() => {
                nextPage($("verificationContainer"),$("registerFormSection"),1400,800);
                
            }, 3000);
        }
    }

    catch (error) {
        console.error('註冊時發生錯誤:', error);
    }
}

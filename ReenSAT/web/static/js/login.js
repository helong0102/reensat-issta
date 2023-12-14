$(document).ready(function () {

        $("#login-btn").click(function () {
            // 获取表单数据
            var formData = $("#loginForm").serialize();
            // 发送AJAX请求
            $.ajax({
                type: "POST",
                url: "/login",
                data: formData,
                dataType: "json",
                success: function (response) {
                    // 处理登录成功的逻辑
                    if(response.success){
                        window.location.href = "/success-page";
                    }
                    else{
                         alert(response.msg)
                    }
                },
                error: function (error) {
                    // 处理登录失败的逻辑
                    console.log("登录失败", error);
                }
            });
        });


});
$(document).ready(function () {
    //根据DOM元素的id构造出一个编辑器
    var editor = CodeMirror.fromTextArea($("#code").get(0), {
      mode: "application/xml", //实现xml代码高亮
      mode: "text/x-javascript", //实现javascript代码高亮
      mode: "text/x-java", //实现Java代码高亮
      lineNumbers: true, //显示行号
      theme: "mdn-like", //设置主题
      lineWrapping: false, //false则超过宽带会显示水平滚动条，true不会显示
      foldGutter: true, //代码是否可折叠
      gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
      matchBrackets: true, //括号匹配
      indentWithTabs: true, //前 N*tabSize 个空格是否应替换为 N 个制表符
      smartIndent: true, //上下文相关缩进（即是否缩进与之前的行相同）
      autofocus: true,
      styleActiveLine: true, //光标所在行高亮
      //readOnly: true,      //只读
    });


    editor.setSize('100%', '100%'); //设置代码框的长宽
    //editor.setValue("测试测试");    //给代码框赋初始值
    //editor.getValue();    //获取代码框的值
    $("#code").on("input",()=>{
      console.log("输入内容",editor.getValue());
    })

    // 文件上传按钮点击事件
    $("#upload_file").click(function () {
        // 打开文件选择窗口
        $("#fileInput").click();
    });

    // 文件选择变化事件
    $("#fileInput").change(function () {
        // 获取选中的文件
        var file = $("#fileInput")[0].files[0];

        if (file) {
            // 创建 FormData 对象
            var formData = new FormData();
            formData.append("file", file);

            // 发送 AJAX 请求
            $.ajax({
                type: "POST",
                url: "/upload_file_path",  // 替换为实际的后端接口地址
                data: formData,
                contentType: false,
                processData: false,
                success: function (response) {
                    // 处理成功响应，response 包含后端返回的数据
                    console.log("文件上传成功", response);

                    // 在这里处理后端返回的文件内容
                    editor.setValue(response.fileContent);
                    // 替换按钮文本
                    $("#version_btn").text(response.versionNumber);
                },
                error: function (error) {
                    // 处理错误
                    console.log("文件上传失败", error);
                }
            });
        }
    });

    // 检测bugs
    $("#detect-bugs").click(function () {
        // 发送漏洞检测请求给后端
        $.ajax({
            type: "GET",
            url: "/detect_bugs",  // 替换为实际的后端接口地址
            success: function (response) {
                // 处理成功响应，response 包含后端返回的数据

                // 将后端返回的字符串写入右边的框体中
                $("#result-container").html(response.result.replace(/\n/g, '<br/>'));
            },
            error: function (error) {
                // 处理错误
                console.log("漏洞检测请求失败", error);
            }
        });
    });

    // 批量检测
    $("#batch-detection").click(function() {
        $.ajax({
            type: "GET",
            url: "/batch_detection",
            success: function (response) {
                // 处理成功的逻辑
                if(response.success){
                    alert(response.msg);
                }
                else{
                     alert(response.msg)
                }
            },
            error: function (error) {
                // 处理错误
                console.log("批量检测请求失败", error);
            }
        });
    });

});
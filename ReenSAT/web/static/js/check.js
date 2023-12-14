/*
 * @Author: tangchen 190854524@qq.com
 * @Date: 2023-12-02 11:54:05
 * @LastEditors: tangchen 190854524@qq.com
 * @LastEditTime: 2023-12-02 12:19:54
 * @FilePath: \ErMiao-Powder\js\check.js
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
$(".bug-check").css({
    background: `url("../static/img/check/btn-active.png")`,
    "background-size": "100% 100%"
})

$(".bug-check").on("click", () => {
    $("#bug-check").show();
    $("#about-me").hide();
    $(".bug-check").css({
        background: `url("../static/img/check/btn-active.png")`,
        "background-size": "100% 100%"
    })
    $(".about-me").css({
        background: `url("../static/img/check/btn-default.png")`,
        "background-size": "100% 100%"
    })
})

$(".about-me").on("click", () => {
    $("#about-me").show();
    $("#bug-check").hide();
    $(".about-me").css({
        background: `url("../static/img/check/btn-active.png")`,
        "background-size": "100% 100%"
    })
    $(".bug-check").css({
        background: `url("../static/img/check/btn-default.png")`,
        "background-size": "100% 100%"
    })
})
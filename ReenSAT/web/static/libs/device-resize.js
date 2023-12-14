$(function () {
  function _setObj(obj, name, objFun) {
    if (typeof obj !== "object") {
      console.log("这不是对象！", obj);
      return false;
    }
    var value;
    objFun = typeof objFun === "object" ? objFun : {};
    Object.defineProperty(obj, "" + name, {
      get: function () {
        if (typeof objFun.get === "function") {
          return objFun.get(value);
        } else {
          return value;
        }
      },
      set: function (val) {
        typeof objFun.set === "function"
          ? objFun.set(val, function (num) {
              value = num;
            })
          : (value = val);
      },
      configurable: true,
      enumerable: true,
    });
  }
  var _$info = {
    browser: undefined,
    // device: undefined,
    engine: undefined,
    language: undefined,
    os: undefined,
    osVersion: undefined,
    version: undefined,
    // orientation: undefined
  };

  var $html = $("html");
  var $body = $("body");
  var $page = $("#page");

  /**
   * browser   浏览器
   * device    设备 ( PC - 电脑 | Tablet - 平板或PDA | Mobile - 手机 )
   * engine    内核 ( EdgeHTML | Trident | Presto | WebKit | Blink | Gecko )
   * language  语言
   * os        系统或平台
   * osVersion (系统或平台)版本
   * version   (内核)版本
   */
  // 获取移动端横竖屏
  function getOrientation() {
    var orientation;
    if (
      window.screen &&
      window.screen.orientation &&
      typeof window.screen.orientation.type !== "undefined"
    ) {
      // 先走 screen.orientation API
      orientation =
        window.screen.orientation.type.indexOf("landscape") !== -1
          ? "landscape"
          : "portrait";
    } else if (typeof window.orientation !== "undefined") {
      // 再走 window.orientation API
      orientation =
        [90, -90].indexOf(window.orientation) !== -1 ? "landscape" : "portrait";
    } else {
      // 依据窗口大小判断
      orientation =
        window.innerWidth > window.innerHeight ? "landscape" : "portrait";
    }
    if (_$info.orientation !== orientation) {
      _$info.orientation = orientation;
    }
    return orientation;
  }

  // 获取浏览器信息
  function getBrowserInfo() {
    var browserinfo = new Browser();
    for (var key in browserinfo) {
      if (_$info[key + ""] !== browserinfo[key + ""]) {
        _$info[key + ""] = browserinfo[key + ""];
      }
    }
    return browserinfo;
  }

  // 监听设备旋转
  window.addEventListener("orientationchange", function () {
    getOrientation();
  });
  // 监听浏览器尺寸变化
  window.addEventListener("resize", function () {
    getBrowserInfo();
    inputFocus();
    ContainerResize();
  });

  // 容器大小设置
  function ContainerResize() {
    var w = document.body.clientWidth,
      h = document.body.clientHeight,
      ratio = 16 / 9,
      r = w / h;
    var setW, setH, setTop, setLeft, fontSize;
    if (r >= ratio) {
      // 高度撑满
      setW = h * ratio;
      setLeft = (w - setW) / 2;
      fontSize = (100 * setW) / 1920;
    } else {
      // 宽度撑满
      setH = w / ratio;
      setTop = (h - setH) / 2;
      fontSize = (100 * setH) / 1080;
    }
    $html.css("font-size", fontSize + "px");
    $page.css({
      width: (setW || w) + "px",
      height: (setH || h) + "px",
      top: (setTop || 0) + "px",
      left: (setLeft || 0) + "px",
    });
  }

  var fixedHeight = document.body.clientHeight + "px";
  // 移动端表单输入兼容
  function inputFocus() {
    if (_$info.device === "Mobile") {
      var activeElement = document.activeElement;
      if (
        ["input", "textarea"].indexOf(activeElement.tagName.toLowerCase()) !==
        -1
      ) {
        // 当黑名单的元素处于焦点时，固定页面高度
        $body.css("height", fixedHeight);
        // 可视区域移动到焦点区域
        activeElement.scrollIntoView({ behavior: "smooth" });
      } else {
        // 无需固定高度的情况
        $body.css("height", "");
        fixedHeight = document.body.clientHeight + "px";
      }
    }
  }

  // 提示
  function device_tips() {
    if (_$info.orientation === "portrait" && _$info.device === "Mobile") {
      $("#device_tips").show();
      $page.hide();
      $html.css("overflow", "hidden");
    } else {
      $("#device_tips").hide();
      $page.show();
      $html.css("overflow", "");
    }
  }

  (function () {
    $("body").append(
      $(
        '<div id="device_tips" style="display:none"><div class="device-orient"></div><p>为了更好的体验，请使用横屏浏览</p></div>'
      )
    );
    device_tips();

    _setObj(_$info, "device", {
      set: function (device, save) {
        save(device);
        $html.removeClass("PC Tablet Mobile").addClass(device);
        device_tips();
      },
    });
    _setObj(_$info, "orientation", {
      set: function (orientation, save) {
        save(orientation);
        $html.removeClass("landscape portrait").addClass(orientation);
        device_tips();
        if (_$info.device === "Mobile") {
          // 失去当前焦点
          var activeElement = document.activeElement;
          activeElement && activeElement.blur && activeElement.blur();
        }
      },
    });

    getBrowserInfo();
    getOrientation();
    ContainerResize();
  })();
});

/*
 * @Author: tangchen 190854524@qq.com
 * @Date: 2023-12-02 18:48:21
 * @LastEditors: tangchen 190854524@qq.com
 * @LastEditTime: 2023-12-02 18:50:17
 * @FilePath: \web\static\libs\code-editor\comment-fold.js
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: https://codemirror.net/LICENSE

(function(mod) {
    if (typeof exports == "object" && typeof module == "object") // CommonJS
      mod(require("../../lib/codemirror"));
    else if (typeof define == "function" && define.amd) // AMD
      define(["../../lib/codemirror"], mod);
    else // Plain browser env
      mod(CodeMirror);
  })(function(CodeMirror) {
  "use strict";
  
  CodeMirror.registerGlobalHelper("fold", "comment", function(mode) {
    return mode.blockCommentStart && mode.blockCommentEnd;
  }, function(cm, start) {
    var mode = cm.getModeAt(start), startToken = mode.blockCommentStart, endToken = mode.blockCommentEnd;
    if (!startToken || !endToken) return;
    var line = start.line, lineText = cm.getLine(line);
  
    var startCh;
    for (var at = start.ch, pass = 0;;) {
      var found = at <= 0 ? -1 : lineText.lastIndexOf(startToken, at - 1);
      if (found == -1) {
        if (pass == 1) return;
        pass = 1;
        at = lineText.length;
        continue;
      }
      if (pass == 1 && found < start.ch) return;
      if (/comment/.test(cm.getTokenTypeAt(CodeMirror.Pos(line, found + 1))) &&
          (found == 0 || lineText.slice(found - endToken.length, found) == endToken ||
           !/comment/.test(cm.getTokenTypeAt(CodeMirror.Pos(line, found))))) {
        startCh = found + startToken.length;
        break;
      }
      at = found - 1;
    }
  
    var depth = 1, lastLine = cm.lastLine(), end, endCh;
    outer: for (var i = line; i <= lastLine; ++i) {
      var text = cm.getLine(i), pos = i == line ? startCh : 0;
      for (;;) {
        var nextOpen = text.indexOf(startToken, pos), nextClose = text.indexOf(endToken, pos);
        if (nextOpen < 0) nextOpen = text.length;
        if (nextClose < 0) nextClose = text.length;
        pos = Math.min(nextOpen, nextClose);
        if (pos == text.length) break;
        if (pos == nextOpen) ++depth;
        else if (!--depth) { end = i; endCh = pos; break outer; }
        ++pos;
      }
    }
    if (end == null || line == end && endCh == startCh) return;
    return {from: CodeMirror.Pos(line, startCh),
            to: CodeMirror.Pos(end, endCh)};
  });
  
  });
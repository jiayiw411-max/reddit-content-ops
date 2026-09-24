// 书签工具的源码(可读版)。真正装进浏览器书签栏的是同目录 README 里那行压缩过的
// javascript: 链接——那不是自动化脚本,是你自己点一下书签、在你已经打开的页面上
//跑一次,只读当前页面上本来就显示给你看的数据,不会自己去访问 Reddit。
(function () {
  var el = document.querySelector("shreddit-post");
  if (!el) {
    alert("没找到帖子数据,确认一下你是不是在帖子详情页(不是列表页)。");
    return;
  }

  var score = el.getAttribute("score");
  var comments = el.getAttribute("comment-count");
  var ratio = el.getAttribute("upvote-ratio");
  var url = location.href.split("?")[0];

  var cmd = 'reddit-ops record --url "' + url + '" --score ' + score + " --comments " + comments;
  if (ratio) {
    cmd += " --upvote-ratio " + ratio;
  }

  function done(copied) {
    var msg = copied
      ? "已复制到剪贴板,粘贴到终端运行即可记录:\n\n"
      : "复制失败,手动复制这行,粘贴到终端运行:\n\n";
    alert(msg + cmd + "\n\n(如果想顺便记录浏览量,在命令末尾自己加 --views 数字)");
  }

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(cmd).then(
      function () {
        done(true);
      },
      function () {
        done(false);
      }
    );
  } else {
    done(false);
  }
})();

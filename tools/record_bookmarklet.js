// 书签工具的源码(可读版)。真正装进浏览器书签栏的是同目录 README 里那行压缩过的
// javascript: 链接——那不是自动化脚本,是你自己点一下书签、在你已经打开的页面上
// 跑一次,只读当前页面上本来就显示给你的数据,发给你自己电脑上跑着的本地看板
// (reddit-ops serve),不会自己去访问 Reddit,也不联网发给任何第三方。
(function () {
  var el = document.querySelector("shreddit-post");
  if (!el) {
    alert("没找到帖子数据,确认一下你是不是在帖子详情页(不是列表页)。");
    return;
  }

  var viewsInput = prompt("浏览量(可选,没有就留空直接确定):", "");
  var views = viewsInput ? parseInt(viewsInput, 10) : null;

  var payload = {
    url: location.href.split("?")[0],
    score: parseInt(el.getAttribute("score"), 10),
    comments: parseInt(el.getAttribute("comment-count"), 10),
    upvote_ratio: el.getAttribute("upvote-ratio") ? parseFloat(el.getAttribute("upvote-ratio")) : null,
    views: views,
    subreddit: el.getAttribute("subreddit-name") || null,
    title: el.getAttribute("post-title") || null,
  };

  fetch("http://127.0.0.1:8765/api/record", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(function () {
      alert("已记录: score=" + payload.score + " comments=" + payload.comments);
    })
    .catch(function (err) {
      alert("记录失败,确认一下本地看板是不是开着(终端跑 reddit-ops serve)。\n" + err);
    });
})();

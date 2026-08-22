
const $ = (id) => document.getElementById(id);

async function loadHealth() {
  try {
    const r = await fetch("/api/health");
    const data = await r.json();
    const ul = $("engines");
    ul.innerHTML = "";
    for (const e of data.engines || []) {
      const li = document.createElement("li");
      li.className = e.available ? "on" : "off";
      li.textContent = `${e.name}${e.version ? " " + e.version : ""}${e.available ? "" : "（未安装）"}`;
      ul.appendChild(li);
    }
    if (data.ffmpeg) {
      const li = document.createElement("li");
      li.className = "on";
      li.textContent = "ffmpeg";
      ul.appendChild(li);
    }
    if (data.cookies && data.cookies.file_configured) {
      const li = document.createElement("li");
      li.className = "on";
      li.textContent = "cookies 文件已配置";
      ul.appendChild(li);
    }
    if (data.cookies && data.cookies.browser_configured) {
      const li = document.createElement("li");
      li.className = "on";
      li.textContent = "cookies_from_browser 已配置";
      ul.appendChild(li);
    }
  } catch (err) {
    $("engines").innerHTML = "<li class='off'>健康检查失败</li>";
  }
}

function fmtSize(n) {
  if (!n) return "大小未知";
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / 1024 / 1024).toFixed(1) + " MB";
}

$("paste").onclick = async () => {
  try {
    $("url").value = await navigator.clipboard.readText();
  } catch {
    $("url").focus();
  }
};

$("parse").onclick = async () => {
  const url = $("url").value.trim();
  const status = $("status");
  const result = $("result");
  result.hidden = true;
  const preview = $("preview");
  preview.removeAttribute("src");
  preview.removeAttribute("poster");
  preview.hidden = true;
  $("previewHint").hidden = true;
  $("previewHint").textContent = "";
  if (!url) {
    status.hidden = false;
    status.className = "status err";
    status.textContent = "请先粘贴链接或分享口令";
    return;
  }
  status.hidden = false;
  status.className = "status";
  status.textContent = "正在并行解析…";
  $("parse").disabled = true;
  try {
    const file = $("cookiesFile").files && $("cookiesFile").files[0];
    const browser = $("cookiesBrowser").value;
    let r;
    if (file || browser) {
      const fd = new FormData();
      fd.append("url", url);
      if (browser) fd.append("cookies_from_browser", browser);
      if (file) fd.append("cookies_file", file, file.name);
      r = await fetch("/api/parse", { method: "POST", body: fd });
    } else {
      r = await fetch("/api/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
    }
    const data = await r.json();
    if (!data.ok) {
      status.className = "status err";
      let msg = data.error || "解析失败";
      if (data.needs_cookie && data.hint) msg += " — " + data.hint;
      else if (data.needs_cookie) msg += " — 可展开上方「本机 Cookies」上传 Netscape 文件";
      status.textContent = msg;
      return;
    }
    status.className = "status ok";
    status.textContent = "解析成功";
    $("title").textContent = data.title || "未命名";
    $("platform").textContent = data.platform || "未知平台";
    $("engine").textContent = data.extractor || "";
    $("info").textContent = `${(data.ext || "mp4").toUpperCase()} · ${fmtSize(data.filesize)}`;
    $("dl").href = data.download_url;
    const preview = $("preview");
    const hint = $("previewHint");
    hint.hidden = true;
    hint.textContent = "";
    preview.onerror = () => {
      if (data.thumbnail) {
        $("thumb").src = data.thumbnail;
        $("thumb").hidden = false;
      }
      hint.hidden = false;
      hint.textContent = "预览加载失败，仍可下载";
    };
    if (data.thumbnail) {
      preview.poster = data.thumbnail;
      $("thumb").src = data.thumbnail;
      $("thumb").hidden = true;
    } else {
      preview.removeAttribute("poster");
      $("thumb").hidden = true;
    }
    preview.src = data.preview_url || ("/api/preview?job=" + data.job);
    preview.hidden = false;
    result.hidden = false;
  } catch (err) {
    status.className = "status err";
    status.textContent = "网络错误：" + err;
  } finally {
    $("parse").disabled = false;
  }
};

loadHealth();

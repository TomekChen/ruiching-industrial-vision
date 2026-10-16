#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切片 E · 低代码网页入口（仅标准库，浏览器点几下）。

启动：
  python tools/lowcode_app.py
  浏览器打开 http://127.0.0.1:8765/
"""

from __future__ import annotations

import html
import json
import subprocess
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from slice_e_core import (  # noqa: E402
    annotate_howto,
    build_board_checklist,
    check_yolo_pairs,
    detect_lan_ipv4,
    ensure_yolo_layout,
    import_images,
)

DEFAULT_DS = Path(r"E:\yolo_files\datasets\my-plant")
DEFAULT_PACK = Path(r"E:\yolo_files\neu_ncnn_board_pack")
DEFAULT_EXPORT = Path(r"E:\yolo_files\exports\neu-det-mini-gpu")
LABEL_URL = "http://47.115.223.159:8903/"


PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>睿擎工业视觉 · 低代码工具（切片 E）</title>
<style>
  :root { --bg:#f4f6f8; --card:#fff; --ink:#1a2332; --accent:#0b6e4f; --muted:#5b6b7c; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
         background: linear-gradient(160deg,#e8eef2,#f7f3ea); color:var(--ink); }
  header { padding: 28px 24px 8px; max-width: 920px; margin: 0 auto; }
  h1 { margin:0; font-size: 1.6rem; letter-spacing: .02em; }
  .sub { color: var(--muted); margin-top: 8px; }
  main { max-width: 920px; margin: 0 auto; padding: 12px 24px 40px; display:grid; gap:16px; }
  section { background: var(--card); border-radius: 12px; padding: 18px 20px;
            box-shadow: 0 8px 24px rgba(26,35,50,.06); }
  h2 { margin: 0 0 10px; font-size: 1.15rem; color: var(--accent); }
  label { display:block; font-size:.9rem; color:var(--muted); margin: 10px 0 4px; }
  input[type=text] { width:100%; padding:10px 12px; border:1px solid #cfd8e3; border-radius:8px; }
  .row { display:flex; flex-wrap:wrap; gap:10px; margin-top:14px; }
  button { background: var(--accent); color:#fff; border:0; border-radius:8px;
           padding:10px 16px; cursor:pointer; font-size:.95rem; }
  button.secondary { background:#2c3e50; }
  pre { background:#0f1720; color:#d7e2ef; padding:14px; border-radius:8px;
        overflow:auto; white-space:pre-wrap; font-size:.85rem; min-height: 80px; }
  a { color: var(--accent); }
</style>
</head>
<body>
<header>
  <h1>睿擎工业视觉 · 低代码工具</h1>
  <p class="sub">切片 E：采图入库 → 标注入口 → 一键生成板上部署清单（不改实时内核）</p>
</header>
<main>
  <section>
    <h2>1. 采图入库</h2>
    <label>数据集根目录</label>
    <input id="ds" type="text" value="__DS__"/>
    <label>现场原图文件夹（可选，导入到 train/images）</label>
    <input id="raw" type="text" placeholder="例如 D:\\photos\\line1"/>
    <div class="row">
      <button onclick="post('init')">创建目录骨架</button>
      <button onclick="post('import')">导入图片</button>
      <button class="secondary" onclick="post('check')">检查标注配对</button>
    </div>
  </section>
  <section>
    <h2>2. 在线标注</h2>
    <p>打开 <a href="__LABEL__" target="_blank" rel="noopener">智标 X-AnyLabeling</a>，
       导出 YOLO txt 到数据集的 <code>train/labels</code>（与图片同名）。</p>
    <div class="row">
      <button class="secondary" onclick="post('howto')">显示标注步骤</button>
    </div>
  </section>
  <section>
    <h2>3. 低代码部署清单</h2>
    <label>上板包目录（含 neu_yolov8n.param/.bin）</label>
    <input id="pack" type="text" value="__PACK__"/>
    <label>电脑 IP（板子要能 ping 通；可留空自动探测）</label>
    <input id="ip" type="text" placeholder="自动探测"/>
    <div class="row">
      <button onclick="post('pack')">打包（复用已有 NCNN）</button>
      <button onclick="post('checklist')">生成板端命令</button>
    </div>
  </section>
  <section>
    <h2>输出</h2>
    <pre id="out">点上面的按钮开始…</pre>
  </section>
</main>
<script>
async function post(action) {
  const body = {
    action,
    dataset: document.getElementById('ds').value,
    raw: document.getElementById('raw').value,
    pack: document.getElementById('pack').value,
    ip: document.getElementById('ip').value,
  };
  document.getElementById('out').textContent = '执行中…';
  const r = await fetch('/api', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  });
  const j = await r.json();
  document.getElementById('out').textContent = j.ok ? j.message : ('错误: ' + j.message);
}
</script>
</body>
</html>
"""


def _page() -> bytes:
    html_page = (
        PAGE.replace("__DS__", html.escape(str(DEFAULT_DS)))
        .replace("__PACK__", html.escape(str(DEFAULT_PACK)))
        .replace("__LABEL__", html.escape(LABEL_URL))
    )
    return html_page.encode("utf-8")


def _handle_api(data: dict) -> dict:
    action = (data.get("action") or "").strip()
    ds = Path((data.get("dataset") or str(DEFAULT_DS)).strip())
    raw = (data.get("raw") or "").strip()
    pack = Path((data.get("pack") or str(DEFAULT_PACK)).strip())
    ip = (data.get("ip") or "").strip() or detect_lan_ipv4()

    if action == "init":
        ensure_yolo_layout(ds)
        return {"ok": True, "message": f"已创建骨架:\n{ds}\n图片→train/images\n标注→train/labels"}

    if action == "import":
        if not raw:
            return {"ok": False, "message": "请填写现场原图文件夹路径"}
        ensure_yolo_layout(ds)
        copied = import_images(Path(raw), ds / "train" / "images")
        return {"ok": True, "message": f"导入 {len(copied)} 张图 → {ds / 'train' / 'images'}"}

    if action == "check":
        c = check_yolo_pairs(ds / "train" / "images", ds / "train" / "labels")
        msg = (
            f"图片={c.images} 标注={c.labels} 成对={c.paired}\n"
            f"缺标注={c.missing_labels[:20]}\n"
            f"多余标注={c.orphan_labels[:20]}\n"
            + ("状态: 可以对齐训练" if c.ok else "状态: 还需要补标注")
        )
        return {"ok": True, "message": msg}

    if action == "howto":
        return {"ok": True, "message": annotate_howto(dataset_root=ds, label_url=LABEL_URL)}

    if action == "pack":
        ncnn = DEFAULT_EXPORT / "best_ncnn_model"
        if not (ncnn / "model.ncnn.param").is_file():
            return {
                "ok": False,
                "message": f"缺少 NCNN: {ncnn}\n请先 python tools/export_neu_ncnn.py",
            }
        subprocess.check_call(
            [sys.executable, str(TOOLS / "pack_neu_board.py"), "--ncnn-dir", str(ncnn), "--out", str(pack)]
        )
        return {"ok": True, "message": f"打包完成: {pack}\n接着点「生成板端命令」"}

    if action == "checklist":
        samples = []
        if pack.is_dir():
            for name in ("scratches_10.jpg", "inclusion_10.jpg", "patches_10.jpg"):
                if (pack / name).is_file():
                    samples.append(name)
        text = build_board_checklist(
            pc_ip=ip, pack_dir=pack, sample_images=samples or None
        )
        pack.mkdir(parents=True, exist_ok=True)
        out = pack / "BOARD_CHECKLIST.txt"
        out.write_text(text, encoding="utf-8")
        return {"ok": True, "message": f"已写 {out}\n\n{text}"}

    return {"ok": False, "message": f"未知动作: {action}"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            body = _page()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
            result = _handle_api(data)
        except Exception as e:
            result = {"ok": False, "message": f"{e}\n{traceback.format_exc()}"}
        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    host, port = "127.0.0.1", 8765
    print(f"切片 E 低代码页: http://{host}:{port}/", flush=True)
    print("浏览器打开上面地址。Ctrl+C 结束。", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切片 E · 低代码部署向导：权重 →（可选导出）→ 打包 → 板端清单。

默认可复用已有 NCNN（跳过耗时导出）。需要重新导出时加 --export。

可运行信号：
  python tools/lowcode_deploy.py
  → 写出 E:\\yolo_files\\neu_ncnn_board_pack\\BOARD_CHECKLIST.txt
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from slice_e_core import build_board_checklist, detect_lan_ipv4  # noqa: E402


def _run(script: Path, extra: list[str]) -> None:
    cmd = [sys.executable, str(script), *extra]
    print(">>>", " ".join(cmd), flush=True)
    subprocess.check_call(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="切片 E：低代码部署向导")
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path(r"E:\yolo_files\runs\neu-det-mini-gpu\best.pt"),
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=Path(r"E:\yolo_files\exports\neu-det-mini-gpu"),
    )
    parser.add_argument(
        "--pack-dir",
        type=Path,
        default=Path(r"E:\yolo_files\neu_ncnn_board_pack"),
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="先跑 export_neu_ncnn.py（需 ultralytics；默认跳过）",
    )
    parser.add_argument("--pack", action="store_true", default=True, help="打包上板目录")
    parser.add_argument("--no-pack", action="store_true", help="不打包，只写清单")
    parser.add_argument("--pc-ip", default="", help="板子访问的电脑 IP；空则自动探测")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--serve",
        action="store_true",
        help="打包后在 pack-dir 启动 http.server（阻塞）",
    )
    args = parser.parse_args()

    if args.export:
        if not args.weights.is_file():
            raise SystemExit(f"找不到权重: {args.weights}")
        _run(
            TOOLS / "export_neu_ncnn.py",
            ["--weights", str(args.weights), "--out-dir", str(args.export_dir)],
        )

    do_pack = args.pack and not args.no_pack
    if do_pack:
        ncnn = args.export_dir / "best_ncnn_model"
        param = ncnn / "model.ncnn.param"
        if not param.is_file():
            raise SystemExit(
                f"缺少 NCNN: {param}\n"
                "请先: python tools/export_neu_ncnn.py\n"
                "或加 --export 让本向导代跑导出"
            )
        _run(
            TOOLS / "pack_neu_board.py",
            ["--ncnn-dir", str(ncnn), "--out", str(args.pack_dir)],
        )

    ip = args.pc_ip.strip() or detect_lan_ipv4()
    samples = []
    if args.pack_dir.is_dir():
        for name in ("scratches_10.jpg", "inclusion_10.jpg", "patches_10.jpg"):
            if (args.pack_dir / name).is_file():
                samples.append(name)
    checklist = build_board_checklist(
        pc_ip=ip,
        http_port=args.port,
        pack_dir=args.pack_dir,
        sample_images=samples or None,
    )
    args.pack_dir.mkdir(parents=True, exist_ok=True)
    out = args.pack_dir / "BOARD_CHECKLIST.txt"
    out.write_text(checklist, encoding="utf-8")
    print(f"[OK] 板端清单已写: {out}")
    print(f"[OK] 探测/使用 PC IP: {ip}")
    print("--- 清单预览 ---")
    print(checklist)

    if args.serve:
        import os

        os.chdir(args.pack_dir)
        print(f"[SERVE] http://{ip}:{args.port}/  目录={args.pack_dir}", flush=True)
        from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

        ThreadingHTTPServer(("0.0.0.0", args.port), SimpleHTTPRequestHandler).serve_forever()


if __name__ == "__main__":
    main()

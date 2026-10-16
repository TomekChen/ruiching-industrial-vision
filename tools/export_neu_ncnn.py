#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 NEU 训练好的 best.pt 导出为 ONNX / NCNN。

可运行信号：
  E:/yolo_files/exports/neu-det-mini-gpu/best.onnx 存在
  若本机有 pnnx，则同时生成 .param/.bin
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")


def main() -> None:
    parser = argparse.ArgumentParser(description="导出 NEU YOLO → ONNX/NCNN")
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path(r"E:\yolo_files\runs\neu-det-mini-gpu\best.pt"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(r"E:\yolo_files\exports\neu-det-mini-gpu"),
    )
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument(
        "--formats",
        default="onnx,ncnn",
        help="逗号分隔：onnx / ncnn",
    )
    args = parser.parse_args()

    if not args.weights.is_file():
        raise SystemExit(f"找不到权重: {args.weights}")

    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise SystemExit(f"请先 pip install ultralytics\n{e}") from e

    args.out_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(args.weights))
    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]

    produced: list[Path] = []
    for fmt in formats:
        print(f"=== export format={fmt} imgsz={args.imgsz} ===", flush=True)
        try:
            kwargs = {"format": fmt, "imgsz": args.imgsz, "simplify": True}
            if fmt == "onnx":
                kwargs["opset"] = 12
            out = model.export(**kwargs)
        except Exception as e:
            if fmt == "ncnn":
                print(
                    f"[WARN] NCNN 导出失败（常因缺少 pnnx）: {e}\n"
                    "  仍保留 ONNX；可稍后安装 pnnx 再跑 --formats ncnn",
                    flush=True,
                )
                continue
            raise
        src = Path(out)
        # ultralytics 常把文件写在权重同目录；拷到统一导出目录
        if fmt == "onnx":
            dst = args.out_dir / "best.onnx"
            shutil.copy2(src, dst)
            produced.append(dst)
            print(f"ONNX -> {dst} ({dst.stat().st_size} bytes)", flush=True)
        elif fmt == "ncnn":
            # 导出目录一般是 best_ncnn_model/ 含 model.ncnn.param / model.ncnn.bin
            if src.is_dir():
                dst_dir = args.out_dir / "best_ncnn_model"
                if dst_dir.exists():
                    shutil.rmtree(dst_dir)
                shutil.copytree(src, dst_dir)
                produced.append(dst_dir)
                for p in sorted(dst_dir.rglob("*")):
                    if p.is_file():
                        print(f"NCNN {p.relative_to(dst_dir)} ({p.stat().st_size})", flush=True)
            else:
                dst = args.out_dir / src.name
                shutil.copy2(src, dst)
                produced.append(dst)
                print(f"NCNN -> {dst}", flush=True)

    if not produced:
        raise SystemExit("没有任何导出产物")

    # 写一份类别对照，方便板端/对比
    names_path = args.out_dir / "names.txt"
    names = model.names if isinstance(model.names, dict) else {i: n for i, n in enumerate(model.names)}
    names_path.write_text(
        "\n".join(f"{i} {names[i]}" for i in sorted(names)) + "\n",
        encoding="utf-8",
    )
    print(f"names -> {names_path}", flush=True)
    print("导出完成:", *[str(p) for p in produced], flush=True)


if __name__ == "__main__":
    main()

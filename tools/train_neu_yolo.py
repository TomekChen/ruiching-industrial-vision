#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 Ultralytics 在 NEU 子集上训练轻量 YOLO（默认 yolov8n）。

可运行信号：runs/detect/neu-det-mini/weights/best.pt 生成。
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

# Windows + Anaconda 常出现双份 OpenMP，不设会直接退出
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")


def main() -> None:
    parser = argparse.ArgumentParser(description="训练 NEU 工业缺陷 YOLO")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(r"E:\yolo_files\datasets\neu-det-mini\data.yaml"),
    )
    parser.add_argument("--model", default="yolov8n.pt", help="预训练权重")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--name", default="neu-det-mini")
    parser.add_argument("--device", default="cpu", help="cpu 或 0（GPU）")
    args = parser.parse_args()

    if not args.data.is_file():
        raise SystemExit(
            f"找不到 {args.data}，请先运行: python tools/prepare_neu_subset.py"
        )

    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise SystemExit(
            "未安装 ultralytics。请执行:\n"
            "  pip install ultralytics\n"
            f"原始错误: {e}"
        ) from e

    model = YOLO(args.model)
    results = model.train(
        data=str(args.data.resolve()),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        name=args.name,
        device=args.device,
        project=str(Path(r"E:\yolo_files\runs")),
        exist_ok=True,
    )
    print(results)
    print("训练结束。权重一般在 E:\\yolo_files\\runs\\detect\\<name>\\weights\\best.pt")


if __name__ == "__main__":
    main()

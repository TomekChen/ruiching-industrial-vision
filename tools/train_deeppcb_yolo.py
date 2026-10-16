#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 DeepPCB 子集训练（薄封装，复用 ultralytics）。"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(r"E:\yolo_files\datasets\deeppcb-mini\data.yaml"),
    )
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(r"E:\yolo_files\runs"),
    )
    parser.add_argument("--name", default="deeppcb-mini")
    args = parser.parse_args()

    if not args.data.is_file():
        raise SystemExit(
            f"找不到 {args.data}\n请先: python tools/prepare_deeppcb_subset.py --src <DeepPCB目录>"
        )

    from ultralytics import YOLO

    model = YOLO(args.model)
    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        device=args.device,
        project=str(args.project),
        name=args.name,
    )
    print("训练结束。导出: python tools/export_neu_ncnn.py --weights <best.pt> --out-dir ...")


if __name__ == "__main__":
    main()

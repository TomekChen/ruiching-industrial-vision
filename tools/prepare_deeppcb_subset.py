#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切片 H · DeepPCB 原始数据 → YOLO 训练子集。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deeppcb_core import prepare_deeppcb_subset  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="DeepPCB → YOLO 子集")
    parser.add_argument(
        "--src",
        type=Path,
        default=Path(r"E:\yolo_files\data\DeepPCB"),
        help="DeepPCB 解压根目录（内含 *_test.jpg 与标注 txt）",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(r"E:\yolo_files\datasets\deeppcb-mini"),
    )
    parser.add_argument("--train-n", type=int, default=80)
    parser.add_argument("--val-n", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not args.src.is_dir():
        raise SystemExit(
            f"源目录不存在: {args.src}\n"
            "下载: https://github.com/tangsanli5201/DeepPCB\n"
            "或交大页: http://www.pami.sjtu.edu.cn/Show/56/77\n"
            "解压后把路径传给 --src"
        )

    summary = prepare_deeppcb_subset(
        args.src,
        args.out,
        train_n=args.train_n,
        val_n=args.val_n,
        seed=args.seed,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("OK: 接着训练示例:")
    print(
        f"  yolo detect train data={args.out / 'data.yaml'} "
        f"model=yolov8n.pt imgsz=320 epochs=30"
    )
    print("板端换类名: 见 demos/deeppcb-slice/README.md 与 BOARD_CLASS_NAMES.txt")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切片 E · 采图入库 + 标注校验。

可运行信号：
  python tools/collect_images.py --init --root E:\\yolo_files\\datasets\\my-plant
  python tools/collect_images.py --import-from <现场图文件夹> --root ...
  python tools/collect_images.py --check --root ...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from slice_e_core import (  # noqa: E402
    annotate_howto,
    check_yolo_pairs,
    ensure_yolo_layout,
    import_images,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="切片 E：采图入库 / 标注校验")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(r"E:\yolo_files\datasets\my-plant"),
        help="数据集根目录",
    )
    parser.add_argument("--init", action="store_true", help="创建 YOLO 目录 + data.yaml")
    parser.add_argument(
        "--import-from",
        type=Path,
        default=None,
        help="把该目录下的图片拷进 train/images",
    )
    parser.add_argument("--check", action="store_true", help="检查图/标注是否成对")
    parser.add_argument("--howto", action="store_true", help="打印标注入口说明")
    parser.add_argument(
        "--label-url",
        default="http://47.115.223.159:8903/",
        help="智标 / 标注工具地址",
    )
    args = parser.parse_args()

    if not any([args.init, args.import_from, args.check, args.howto]):
        parser.print_help()
        raise SystemExit(
            "\n请至少指定一个动作: --init / --import-from / --check / --howto"
        )

    if args.init:
        ensure_yolo_layout(args.root)
        print(f"[OK] 已创建数据集骨架: {args.root}")
        print(f"     图片放: {args.root / 'train' / 'images'}")
        print(f"     标注放: {args.root / 'train' / 'labels'}")

    if args.import_from is not None:
        ensure_yolo_layout(args.root)
        copied = import_images(args.import_from, args.root / "train" / "images")
        print(f"[OK] 导入 {len(copied)} 张图 → {args.root / 'train' / 'images'}")
        if not copied:
            print("[WARN] 源目录没有 jpg/png/bmp")

    if args.check:
        c = check_yolo_pairs(args.root / "train" / "images", args.root / "train" / "labels")
        print(
            f"图片={c.images} 标注={c.labels} 成对={c.paired} "
            f"缺标注={len(c.missing_labels)} 多余标注={len(c.orphan_labels)}"
        )
        if c.missing_labels[:10]:
            print("  缺标注示例:", ", ".join(c.missing_labels[:10]))
        if c.orphan_labels[:10]:
            print("  多余标注示例:", ", ".join(c.orphan_labels[:10]))
        if c.ok:
            print("[OK] 训练集图标注已对齐，可以训练")
        else:
            print("[!] 尚未对齐。先 --howto 看标注步骤，标完再 --check")
            raise SystemExit(1)

    if args.howto:
        print(annotate_howto(dataset_root=args.root, label_url=args.label_url), end="")


if __name__ == "__main__":
    main()

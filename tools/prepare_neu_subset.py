#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 NEU-DET（YOLO 格式）抽样生成可训练的工业缺陷子集。

可运行信号：输出目录含 train/images、train/labels、valid/...、data.yaml，
且每张图都有同名 .txt 标注。
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
from collections import defaultdict
from pathlib import Path

# 与 NEU-DET data.yaml 一致（类别 ID 0..5）
CLASS_NAMES = [
    "crazing",
    "inclusion",
    "patches",
    "pitted_surface",
    "rolled-in_scale",
    "scratches",
]

_STEM_RE = re.compile(
    r"^(crazing|inclusion|patches|pitted_surface|rolled-in_scale|scratches)_\d+$"
)


def class_from_stem(stem: str) -> str | None:
    """从文件名主干解析类别名，无法识别则返回 None。"""
    m = _STEM_RE.match(stem)
    return m.group(1) if m else None


def index_split(images_dir: Path) -> dict[str, list[Path]]:
    """按类别收集 jpg/png 路径。"""
    buckets: dict[str, list[Path]] = defaultdict(list)
    for p in sorted(images_dir.iterdir()):
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        cls = class_from_stem(p.stem)
        if cls is None:
            continue
        buckets[cls].append(p)
    return buckets


def sample_paths(
    buckets: dict[str, list[Path]],
    per_class: int,
    seed: int,
) -> list[Path]:
    rng = random.Random(seed)
    chosen: list[Path] = []
    for cls in CLASS_NAMES:
        pool = list(buckets.get(cls, []))
        if not pool:
            raise FileNotFoundError(f"类别 {cls} 在源目录中没有图片")
        rng.shuffle(pool)
        n = min(per_class, len(pool))
        chosen.extend(pool[:n])
    return chosen


def copy_pair(img: Path, labels_dir: Path, out_img_dir: Path, out_lbl_dir: Path) -> None:
    lbl = labels_dir / f"{img.stem}.txt"
    if not lbl.is_file():
        raise FileNotFoundError(f"缺少标注: {lbl}")
    out_img_dir.mkdir(parents=True, exist_ok=True)
    out_lbl_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(img, out_img_dir / img.name)
    shutil.copy2(lbl, out_lbl_dir / lbl.name)


def write_data_yaml(out_root: Path) -> Path:
    yaml_path = out_root / "data.yaml"
    names_lines = "\n".join(f"  {i}: {n}" for i, n in enumerate(CLASS_NAMES))
    # Ultralytics 接受 path + train/val 相对 path
    text = (
        f"path: {out_root.resolve().as_posix()}\n"
        f"train: train/images\n"
        f"val: valid/images\n"
        f"nc: {len(CLASS_NAMES)}\n"
        f"names:\n{names_lines}\n"
    )
    yaml_path.write_text(text, encoding="utf-8")
    return yaml_path


def prepare(
    src_root: Path,
    out_root: Path,
    train_per_class: int,
    val_per_class: int,
    seed: int,
) -> dict:
    train_img = src_root / "train" / "images"
    train_lbl = src_root / "train" / "labels"
    valid_img = src_root / "valid" / "images"
    valid_lbl = src_root / "valid" / "labels"

    if not train_img.is_dir() or not train_lbl.is_dir():
        raise FileNotFoundError(f"源训练目录不完整: {src_root}")

    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)

    train_buckets = index_split(train_img)
    train_files = sample_paths(train_buckets, train_per_class, seed)
    for img in train_files:
        copy_pair(img, train_lbl, out_root / "train" / "images", out_root / "train" / "labels")

    # 验证集：优先从官方 valid 抽；不够则从 train 剩余抽（换种子）
    if valid_img.is_dir() and valid_lbl.is_dir() and any(valid_img.iterdir()):
        val_buckets = index_split(valid_img)
        # 官方 valid 往往很少，按类尽量取
        val_files: list[Path] = []
        rng = random.Random(seed + 1)
        for cls in CLASS_NAMES:
            pool = list(val_buckets.get(cls, []))
            rng.shuffle(pool)
            if pool:
                val_files.extend(pool[: min(val_per_class, len(pool))])
            else:
                # 该类 valid 为空：从训练集未选中的补
                train_pool = [p for p in train_buckets[cls] if p not in train_files]
                rng.shuffle(train_pool)
                val_files.extend(train_pool[:val_per_class])
        val_lbl_dir = valid_lbl
    else:
        val_files = sample_paths(train_buckets, val_per_class, seed + 7)
        # 避免与 train 重叠
        train_set = set(train_files)
        val_files = [p for p in val_files if p not in train_set]
        val_lbl_dir = train_lbl

    for img in val_files:
        # 若图来自 train 目录，标注也在 train/labels
        lbl_dir = train_lbl if (train_lbl / f"{img.stem}.txt").is_file() else val_lbl_dir
        copy_pair(img, lbl_dir, out_root / "valid" / "images", out_root / "valid" / "labels")

    yaml_path = write_data_yaml(out_root)
    summary = {
        "src": str(src_root.resolve()),
        "out": str(out_root.resolve()),
        "train_images": len(train_files),
        "valid_images": len(val_files),
        "train_per_class": train_per_class,
        "val_per_class": val_per_class,
        "seed": seed,
        "classes": CLASS_NAMES,
        "data_yaml": str(yaml_path),
    }
    (out_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="NEU-DET → 可训练 YOLO 子集")
    parser.add_argument(
        "--src",
        type=Path,
        default=Path(r"E:\yolo_files\data\NEU-DET\images\NEU-DET"),
        help="含 train/ valid/ 的 NEU-DET 根目录",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(r"E:\yolo_files\datasets\neu-det-mini"),
        help="输出子集目录",
    )
    parser.add_argument("--train-per-class", type=int, default=40)
    parser.add_argument("--val-per-class", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    summary = prepare(
        args.src, args.out, args.train_per_class, args.val_per_class, args.seed
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("OK: 子集已生成，可用 tools/train_neu_yolo.py 训练。")


if __name__ == "__main__":
    main()

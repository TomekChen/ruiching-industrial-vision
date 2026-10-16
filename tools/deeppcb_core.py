# -*- coding: utf-8 -*-
"""切片 H · DeepPCB → YOLO 转换核心（可单测，不依赖完整数据集）。"""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

# 官方 type: 1..6 → YOLO id 0..5
DEEPPCB_CLASS_NAMES = [
    "open",
    "short",
    "mousebite",
    "spur",
    "copper",
    "pin-hole",
]


def deeppcb_type_to_yolo(type_id: int) -> int | None:
    """DeepPCB type 1..6 → YOLO 0..5；非法返回 None。"""
    if 1 <= type_id <= 6:
        return type_id - 1
    return None


def xyxy_to_yolo(
    x1: float, y1: float, x2: float, y2: float, img_w: int, img_h: int
) -> tuple[float, float, float, float] | None:
    if img_w <= 0 or img_h <= 0 or x2 <= x1 or y2 <= y1:
        return None
    cx = ((x1 + x2) / 2.0) / img_w
    cy = ((y1 + y2) / 2.0) / img_h
    w = (x2 - x1) / img_w
    h = (y2 - y1) / img_h
    # clamp
    cx = min(max(cx, 0.0), 1.0)
    cy = min(max(cy, 0.0), 1.0)
    w = min(max(w, 0.0), 1.0)
    h = min(max(h, 0.0), 1.0)
    return cx, cy, w, h


def convert_annotation_text(
    text: str, img_w: int = 640, img_h: int = 640
) -> list[str]:
    """把 DeepPCB 原始标注文本转为 YOLO 行列表。"""
    lines_out: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # 支持逗号或空白分隔
        parts = line.replace(",", " ").split()
        if len(parts) < 5:
            continue
        try:
            x1, y1, x2, y2 = map(float, parts[:4])
            type_id = int(float(parts[4]))
        except ValueError:
            continue
        yolo_id = deeppcb_type_to_yolo(type_id)
        if yolo_id is None:
            continue
        box = xyxy_to_yolo(x1, y1, x2, y2, img_w, img_h)
        if box is None:
            continue
        cx, cy, w, h = box
        lines_out.append(f"{yolo_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    return lines_out


def write_data_yaml(out_root: Path, class_names: list[str] | None = None) -> Path:
    names = class_names or DEEPPCB_CLASS_NAMES
    names_lines = "\n".join(f"  {i}: {n}" for i, n in enumerate(names))
    path = out_root / "data.yaml"
    path.write_text(
        f"path: {out_root.resolve().as_posix()}\n"
        f"train: train/images\n"
        f"val: valid/images\n"
        f"nc: {len(names)}\n"
        f"names:\n{names_lines}\n",
        encoding="utf-8",
    )
    return path


def find_deeppcb_pairs(src_root: Path) -> list[tuple[Path, Path]]:
    """在源目录递归找 *_test.jpg/.png + 同 stem 的 .txt。

    stem 例：00041000_test → 标注可为 00041000.txt 或 00041000_test.txt
    """
    pairs: list[tuple[Path, Path]] = []
    for img in sorted(src_root.rglob("*_test.jpg")) + sorted(src_root.rglob("*_test.png")):
        stem = img.name
        base = stem.replace("_test.jpg", "").replace("_test.png", "")
        # 官方解压：图在 00041/，标注在同级 00041_not/
        not_dir = img.parent.parent / f"{img.parent.name}_not"
        candidates = [
            img.with_name(base + ".txt"),
            img.with_name(img.stem + ".txt"),
            img.parent / f"{base}.txt",
            not_dir / f"{base}.txt",
        ]
        lbl = next((c for c in candidates if c.is_file()), None)
        if lbl is not None:
            pairs.append((img, lbl))
    return pairs


def prepare_deeppcb_subset(
    src_root: Path,
    out_root: Path,
    *,
    train_n: int = 80,
    val_n: int = 20,
    seed: int = 42,
    img_w: int = 640,
    img_h: int = 640,
) -> dict:
    """从 DeepPCB 原始目录抽样转 YOLO 子集。"""
    pairs = find_deeppcb_pairs(src_root)
    if not pairs:
        raise FileNotFoundError(
            f"在 {src_root} 未找到 *_test.jpg + 标注。\n"
            "请先下载 DeepPCB：https://github.com/tangsanli5201/DeepPCB"
        )

    rng = random.Random(seed)
    rng.shuffle(pairs)
    need = train_n + val_n
    if len(pairs) < need:
        # 有多少用多少
        train_n = max(1, int(len(pairs) * 0.8))
        val_n = max(1, len(pairs) - train_n)
    train_pairs = pairs[:train_n]
    val_pairs = pairs[train_n : train_n + val_n]

    if out_root.exists():
        shutil.rmtree(out_root)

    def _dump(split: str, items: list[tuple[Path, Path]]) -> int:
        img_dir = out_root / split / "images"
        lbl_dir = out_root / split / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)
        n = 0
        for img, lbl in items:
            text = lbl.read_text(encoding="utf-8", errors="ignore")
            yolo_lines = convert_annotation_text(text, img_w=img_w, img_h=img_h)
            if not yolo_lines:
                continue
            out_name = img.name
            shutil.copy2(img, img_dir / out_name)
            (lbl_dir / f"{Path(out_name).stem}.txt").write_text(
                "\n".join(yolo_lines) + "\n", encoding="utf-8"
            )
            n += 1
        return n

    n_train = _dump("train", train_pairs)
    n_val = _dump("valid", val_pairs)
    yaml_path = write_data_yaml(out_root)
    summary = {
        "src": str(src_root.resolve()),
        "out": str(out_root.resolve()),
        "found_pairs": len(pairs),
        "train_images": n_train,
        "valid_images": n_val,
        "classes": DEEPPCB_CLASS_NAMES,
        "data_yaml": str(yaml_path),
        "seed": seed,
    }
    (out_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # 板端换类名提示
    (out_root / "BOARD_CLASS_NAMES.txt").write_text(
        "\n".join(f"{i} {n}" for i, n in enumerate(DEEPPCB_CLASS_NAMES)) + "\n",
        encoding="utf-8",
    )
    return summary

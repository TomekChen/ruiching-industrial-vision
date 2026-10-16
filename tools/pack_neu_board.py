# -*- coding: utf-8 -*-
"""把导出的 NCNN + 切片 A 图打成可 wget 的上板目录。"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ncnn-dir",
        type=Path,
        default=Path(r"E:\yolo_files\exports\neu-det-mini-gpu\best_ncnn_model"),
    )
    parser.add_argument(
        "--images",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "demos"
        / "neu-det-slice-a"
        / "images",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(r"E:\yolo_files\neu_ncnn_board_pack"),
    )
    args = parser.parse_args()

    param = args.ncnn_dir / "model.ncnn.param"
    bin_f = args.ncnn_dir / "model.ncnn.bin"
    if not param.is_file() or not bin_f.is_file():
        raise SystemExit(f"缺少 NCNN 文件，请先: python tools/export_neu_ncnn.py\n{args.ncnn_dir}")

    args.out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(param, args.out / "neu_yolov8n.param")
    shutil.copy2(bin_f, args.out / "neu_yolov8n.bin")
    names = args.ncnn_dir.parent / "names.txt"
    if names.is_file():
        shutil.copy2(names, args.out / "names.txt")
    onnx = args.ncnn_dir.parent / "best.onnx"
    if onnx.is_file():
        shutil.copy2(onnx, args.out / "best.onnx")

    n_img = 0
    for img in list(args.images.glob("*.jpg")) + list(args.images.glob("*.png")):
        shutil.copy2(img, args.out / img.name)
        n_img += 1

    print(f"打包完成: {args.out}")
    print(f"  neu_yolov8n.param / .bin + {n_img} 张图")
    print(f"  开服务: cd /d {args.out} && python -m http.server 8000")


if __name__ == "__main__":
    main()

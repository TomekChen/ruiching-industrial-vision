#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切片 H · 准备 NCNN INT8 量化材料。

默认可运行（无 ncnn 工具也能完成）：
  1) 校准 imagelist
  2) INT8_RECIPE.txt 步骤
  3) 可选：调用 ultralytics export int8=True

可运行信号：
  E:\\yolo_files\\exports\\neu-int8\\calib_imagelist.txt 存在
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from int8_core import (  # noqa: E402
    build_int8_checklist,
    build_int8_recipe,
    collect_calib_images,
    write_imagelist,
)
from slice_e_core import detect_lan_ipv4  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="切片 H：INT8 量化材料")
    parser.add_argument(
        "--images",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "demos"
        / "neu-det-slice-a"
        / "images",
        help="校准图目录",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(r"E:\yolo_files\exports\neu-int8"),
    )
    parser.add_argument("--limit", type=int, default=64)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path(r"E:\yolo_files\runs\neu-det-mini-gpu\best.pt"),
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(r"E:\yolo_files\datasets\neu-det-mini\data.yaml"),
        help="Ultralytics INT8 校准时需要",
    )
    parser.add_argument(
        "--try-ultralytics",
        action="store_true",
        help="尝试 yolo export format=ncnn int8=True（需 ultralytics+校准 data）",
    )
    parser.add_argument("--pc-ip", default="")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    imgs = collect_calib_images(args.images, limit=args.limit)
    if not imgs:
        raise SystemExit(f"校准目录无图片: {args.images}")

    imagelist = write_imagelist(imgs, args.out_dir / "calib_imagelist.txt", args.imgsz)
    print(f"[OK] imagelist ({len(imgs)}) -> {imagelist}")

    # 若已有 FP32 上板包，拷一份 param/bin 到 int8 工作目录方便本机量化
    pack = Path(r"E:\yolo_files\neu_ncnn_board_pack")
    for name in ("neu_yolov8n.param", "neu_yolov8n.bin"):
        src = pack / name
        if src.is_file():
            shutil.copy2(src, args.out_dir / name)
            print(f"[OK] 拷贝 {name}")

    recipe = build_int8_recipe(
        fp32_param=args.out_dir / "neu_yolov8n.param",
        fp32_bin=args.out_dir / "neu_yolov8n.bin",
        imagelist=imagelist,
        imgsz=args.imgsz,
    )
    recipe_path = args.out_dir / "INT8_RECIPE.txt"
    recipe_path.write_text(recipe, encoding="utf-8")
    print(f"[OK] 菜谱 -> {recipe_path}")

    ip = args.pc_ip.strip() or detect_lan_ipv4()
    checklist = build_int8_checklist(ip)
    (args.out_dir / "INT8_BOARD_CHECKLIST.txt").write_text(checklist, encoding="utf-8")
    print(f"[OK] 板端清单 -> {args.out_dir / 'INT8_BOARD_CHECKLIST.txt'}")

    if args.try_ultralytics:
        if not args.weights.is_file():
            raise SystemExit(f"无权重: {args.weights}")
        if not args.data.is_file():
            raise SystemExit(f"无 data.yaml（INT8 校准需要）: {args.data}")
        try:
            from ultralytics import YOLO
        except ImportError as e:
            raise SystemExit(f"请 pip install ultralytics\n{e}") from e
        print("=== ultralytics export ncnn int8 ===", flush=True)
        model = YOLO(str(args.weights))
        try:
            out = model.export(
                format="ncnn",
                imgsz=args.imgsz,
                int8=True,
                data=str(args.data),
            )
            print(f"[OK] ultralytics 输出: {out}")
        except Exception as e:
            print(f"[WARN] ultralytics INT8 导出失败，请改用 INT8_RECIPE.txt 手工量化:\n{e}")

    print("完成。有 ncnn2table/ncnn2bin 时按 INT8_RECIPE.txt 执行；完成后再上板对比时延。")


if __name__ == "__main__":
    main()

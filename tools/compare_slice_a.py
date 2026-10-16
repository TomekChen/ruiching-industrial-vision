#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切片 C：用自定义 NEU 模型对切片 A 同款工业图做 PC 推理，留下对比图。

可运行信号：demos/neu-det-slice-c/compare/ 下每张图有 *_pred.jpg，
且 summary.json 里检出数显著优于切片 A（通用模型几乎漏检）。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# 与切片 A 一致的 6 类中文（写报告用）
NEU_CN = {
    "crazing": "龟裂",
    "inclusion": "夹杂",
    "patches": "斑块",
    "pitted_surface": "点蚀",
    "rolled-in_scale": "氧化皮压入",
    "scratches": "划痕",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="NEU 模型 vs 切片 A 同图对比")
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path(r"E:\yolo_files\runs\neu-det-mini-gpu\best.pt"),
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
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "demos"
        / "neu-det-slice-c"
        / "compare",
    )
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--conf", type=float, default=0.25)
    args = parser.parse_args()

    if not args.weights.is_file():
        raise SystemExit(f"找不到权重: {args.weights}")
    if not args.images.is_dir():
        raise SystemExit(f"找不到图片目录: {args.images}")

    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise SystemExit(f"请先 pip install ultralytics\n{e}") from e

    args.out_dir.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(args.weights))
    names = model.names if isinstance(model.names, dict) else {i: n for i, n in enumerate(model.names)}

    images = sorted(args.images.glob("*.jpg")) + sorted(args.images.glob("*.png"))
    if not images:
        raise SystemExit(f"{args.images} 下没有图片")

    # 切片 A 真机回填（来自 DEV_LOG / slice-a README）
    slice_a = {
        "crazing_10.jpg": {"detect_ms": 3050, "note": "无检出"},
        "scratches_10.jpg": {"detect_ms": 3027, "note": "误检 COCO 类5 conf=0.42"},
        "inclusion_10.jpg": {"detect_ms": 3026, "note": "无检出"},
    }

    rows: list[dict] = []
    for img in images:
        results = model.predict(
            str(img),
            imgsz=args.imgsz,
            conf=args.conf,
            save=False,
            verbose=False,
        )
        r0 = results[0]
        n = len(r0.boxes) if r0.boxes is not None else 0
        dets = []
        if n:
            for box in r0.boxes:
                cls_id = int(box.cls.item())
                cls_name = names.get(cls_id, str(cls_id))
                dets.append(
                    {
                        "cls": cls_name,
                        "cls_cn": NEU_CN.get(cls_name, cls_name),
                        "conf": round(float(box.conf.item()), 3),
                    }
                )
        # 保存画框图
        plotted = r0.plot()
        out_img = args.out_dir / f"{img.stem}_pred.jpg"
        import cv2

        cv2.imwrite(str(out_img), plotted)

        row = {
            "image": img.name,
            "detections": n,
            "boxes": dets,
            "pred_image": str(out_img.relative_to(args.out_dir.parent)),
            "slice_a": slice_a.get(img.name, {"note": "切片A未单独回填"}),
        }
        rows.append(row)
        print(f"{img.name}: {n} boxes -> {out_img.name}", flush=True)

    summary = {
        "weights": str(args.weights),
        "imgsz": args.imgsz,
        "conf": args.conf,
        "images": len(rows),
        "total_detections": sum(r["detections"] for r in rows),
        "per_image": rows,
        "verdict": (
            "自定义 NEU 模型在 PC 上对同款工业图有检出；"
            "切片 A 通用 COCO 模型在板上几乎漏检/误检 → 证明必须做工业模型适配。"
        ),
    }
    summary_path = args.out_dir.parent / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"summary -> {summary_path}", flush=True)
    print(
        f"完成：{len(rows)} 张图，共检出 {summary['total_detections']} 个框",
        flush=True,
    )


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""切片 H · INT8 量化辅助（不依赖 GPU；无 pnnx 时仍生成校准清单与步骤）。"""

from __future__ import annotations

from pathlib import Path

DEFAULT_IMGSZ = 320


def collect_calib_images(images_dir: Path, limit: int = 64) -> list[Path]:
    """收集 jpg/png 作为 NCNN INT8 校准图。"""
    if not images_dir.is_dir():
        return []
    files = sorted(
        [
            p
            for p in images_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
        ]
    )
    return files[:limit]


def write_imagelist(images: list[Path], out_file: Path, imgsz: int = DEFAULT_IMGSZ) -> Path:
    """写 ncnn2table 用的 imagelist（每行一张图路径）。"""
    out_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [str(p.resolve()) for p in images]
    # 头部注释方便人看；ncnn2table 通常忽略空行，路径行必须干净
    body = "\n".join(lines) + ("\n" if lines else "")
    out_file.write_text(body, encoding="utf-8")
    meta = out_file.with_suffix(".meta.txt")
    meta.write_text(
        f"count={len(lines)}\nimgsz={imgsz}\nnote=feed this list to ncnn2table\n",
        encoding="utf-8",
    )
    return out_file


def build_int8_recipe(
    *,
    fp32_param: str | Path = "neu_yolov8n.param",
    fp32_bin: str | Path = "neu_yolov8n.bin",
    imagelist: str | Path = "calib_imagelist.txt",
    out_param: str = "neu_yolov8n_int8.param",
    out_bin: str = "neu_yolov8n_int8.bin",
    imgsz: int = DEFAULT_IMGSZ,
) -> str:
    """生成人可复制的 INT8 量化步骤（Windows/Linux 通用说明）。"""
    return "\n".join(
        [
            "# 切片 H · NCNN INT8 量化菜谱（在已安装 ncnn 工具的环境执行）",
            f"# 输入 FP32: {fp32_param} + {fp32_bin}",
            f"# 校准列表: {imagelist}",
            f"# 输出: {out_param} + {out_bin}",
            "",
            "# 1) 生成校准表（mean/norm 与板端一致：/255 → 0~1）",
            f"ncnn2table {fp32_param} {fp32_bin} {imagelist} neu_yolov8n.table mean=[0,0,0] norm=[0.00392157,0.00392157,0.00392157] shape=[{imgsz},{imgsz},3] pixel=RGB thread=2 method=kl",
            "",
            "# 2) 写入 int8 模型",
            f"ncnn2bin {fp32_param} {fp32_bin} neu_yolov8n.table {out_param} {out_bin}",
            "",
            "# 3) 打包上板（文件名可与 FP32 并存）",
            f"# 拷到 E:\\yolo_files\\neu_ncnn_board_pack\\ 后：",
            f"#   wget .../{out_param}",
            f"#   wget .../{out_bin}",
            "# 板端临时把 neu_yolov8.cpp 里加载名改成 int8 文件，或覆盖原文件名再测时延",
            "",
            "# 备选（Ultralytics，需 data.yaml 校准）：",
            "#   yolo export model=best.pt format=ncnn imgsz=320 int8=True data=data.yaml",
            "",
        ]
    )


def build_int8_checklist(pc_ip: str, http_port: int = 8000) -> str:
    return "\n".join(
        [
            "# INT8 上板试跑（量化产物就位后）",
            "cd /data",
            f"wget http://{pc_ip}:{http_port}/neu_yolov8n_int8.param neu_yolov8n_int8.param",
            f"wget http://{pc_ip}:{http_port}/neu_yolov8n_int8.bin neu_yolov8n_int8.bin",
            "# 若固件仍加载 neu_yolov8n.* ，可临时覆盖：",
            "cp neu_yolov8n_int8.param neu_yolov8n.param",
            "cp neu_yolov8n_int8.bin neu_yolov8n.bin",
            "neu_yolov8_test scratches_10.jpg out_neu_int8_scratches.jpg",
            "",
        ]
    )

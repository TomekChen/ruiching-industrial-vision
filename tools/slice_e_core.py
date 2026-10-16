# -*- coding: utf-8 -*-
"""切片 E 核心逻辑（无 Ultralytics / 无 GPU，可单测）。

职责：
1. 采图入库 → 标准 YOLO 目录
2. 检查标注配对
3. 生成板端 wget / neu_yolov8_test 清单
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import NamedTuple

# 与 NEU-DET / 板端 names 对齐
DEFAULT_CLASS_NAMES = [
    "crazing",
    "inclusion",
    "patches",
    "pitted_surface",
    "rolled-in_scale",
    "scratches",
]

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


class DatasetCheck(NamedTuple):
    images: int
    labels: int
    paired: int
    missing_labels: list[str]
    orphan_labels: list[str]

    @property
    def ok(self) -> bool:
        return (
            self.images > 0
            and self.paired == self.images
            and not self.missing_labels
            and not self.orphan_labels
        )


def ensure_yolo_layout(root: Path, class_names: list[str] | None = None) -> Path:
    """创建 train/valid 的 images+labels，并写 data.yaml。返回 root。"""
    names = class_names or DEFAULT_CLASS_NAMES
    for split in ("train", "valid"):
        (root / split / "images").mkdir(parents=True, exist_ok=True)
        (root / split / "labels").mkdir(parents=True, exist_ok=True)

    yaml = root / "data.yaml"
    lines = [
        f"path: {root.as_posix()}",
        "train: train/images",
        "val: valid/images",
        f"nc: {len(names)}",
        "names:",
    ]
    for i, n in enumerate(names):
        lines.append(f"  {i}: {n}")
    yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


def import_images(src_dir: Path, dst_images: Path) -> list[Path]:
    """把源目录图片拷到 dst_images，返回新文件列表。"""
    if not src_dir.is_dir():
        raise FileNotFoundError(f"源目录不存在: {src_dir}")
    dst_images.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for p in sorted(src_dir.iterdir()):
        if not p.is_file() or p.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        dst = dst_images / p.name
        shutil.copy2(p, dst)
        copied.append(dst)
    return copied


def check_yolo_pairs(images_dir: Path, labels_dir: Path) -> DatasetCheck:
    """检查每张图是否有同名 .txt 标注。"""
    imgs = [
        p
        for p in sorted(images_dir.iterdir())
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    ] if images_dir.is_dir() else []
    labs = [
        p for p in sorted(labels_dir.iterdir()) if p.is_file() and p.suffix.lower() == ".txt"
    ] if labels_dir.is_dir() else []

    img_stems = {p.stem for p in imgs}
    lab_stems = {p.stem for p in labs}
    missing = sorted(img_stems - lab_stems)
    orphan = sorted(lab_stems - img_stems)
    paired = len(img_stems & lab_stems)
    return DatasetCheck(
        images=len(imgs),
        labels=len(labs),
        paired=paired,
        missing_labels=missing,
        orphan_labels=orphan,
    )


def _list_ipv4() -> list[str]:
    """枚举本机 IPv4（排除回环）。"""
    import socket

    found: list[str] = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127.") and ip not in found:
                found.append(ip)
    except OSError:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127.") and ip not in found:
                found.insert(0, ip)
        finally:
            s.close()
    except OSError:
        pass
    return found


def detect_lan_ipv4() -> str:
    """优先选与板子常见网段一致的 IP（192.168.2.x），否则取第一个局域网地址。"""
    ips = _list_ipv4()
    for ip in ips:
        if ip.startswith("192.168.2."):
            return ip
    for ip in ips:
        # 排除常见虚拟网卡网段
        if ip.startswith("172.19.") or ip.startswith("100."):
            continue
        if ip.startswith("192.168.") or ip.startswith("10."):
            return ip
    return ips[0] if ips else "192.168.2.10"


def build_board_checklist(
    *,
    pc_ip: str,
    http_port: int = 8000,
    pack_dir: str | Path = r"E:\yolo_files\neu_ncnn_board_pack",
    sample_images: list[str] | None = None,
) -> str:
    """生成给 msh 用的人话清单（wget + neu_yolov8_test）。"""
    samples = sample_images or [
        "scratches_10.jpg",
        "inclusion_10.jpg",
        "patches_10.jpg",
    ]
    base = f"http://{pc_ip}:{http_port}"
    lines = [
        "# 切片 E · 板端一键部署清单（复制到 msh）",
        f"# PC 打包目录: {pack_dir}",
        f"# PC 先执行: cd /d {pack_dir} && python -m http.server {http_port}",
        "",
        "cd /data",
        f"wget {base}/neu_yolov8n.param neu_yolov8n.param",
        f"wget {base}/neu_yolov8n.bin neu_yolov8n.bin",
    ]
    for name in samples:
        lines.append(f"wget {base}/{name} {name}")
    lines.append("")
    for name in samples:
        stem = Path(name).stem
        lines.append(f"neu_yolov8_test {name} out_neu_{stem}.jpg")
    lines.append("")
    lines.append("# 提示: 若命令找不到，先 Ctrl+C 再 Enter 清行后重试")
    return "\n".join(lines) + "\n"


def annotate_howto(
    *,
    dataset_root: str | Path,
    label_url: str = "http://47.115.223.159:8903/",
) -> str:
    """标注入口说明（智标 / 本地导出路径约定）。"""
    root = Path(dataset_root)
    return "\n".join(
        [
            "# 切片 E · 标注入口",
            f"1. 浏览器打开智标（X-AnyLabeling）: {label_url}",
            f"2. 打开本机图片目录: {root / 'train' / 'images'}",
            "3. 画缺陷框，导出 YOLO txt",
            f"4. 把 .txt 放到: {root / 'train' / 'labels'}（与图片同名）",
            "5. 校验: python tools/collect_images.py --check --root <数据集根目录>",
            "6. 训练: python tools/train_neu_yolo.py （或 GPU 脚本）",
            "7. 部署: python tools/lowcode_deploy.py",
            "",
        ]
    )

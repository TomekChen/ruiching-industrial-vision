# -*- coding: utf-8 -*-
"""切片 E 核心逻辑测试（不依赖 GPU / 权重）。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_core():
    import sys
    from importlib.util import module_from_spec, spec_from_file_location

    path = ROOT / "tools" / "slice_e_core.py"
    spec = spec_from_file_location("slice_e_core", path)
    assert spec and spec.loader
    mod = module_from_spec(spec)
    # 先登记再 exec，避免 dataclass/注解在动态加载时踩坑
    sys.modules["slice_e_core"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_ensure_yolo_layout_creates_dirs_and_yaml(tmp_path: Path):
    core = _load_core()
    root = tmp_path / "ds"
    core.ensure_yolo_layout(root)
    assert (root / "train" / "images").is_dir()
    assert (root / "train" / "labels").is_dir()
    assert (root / "valid" / "images").is_dir()
    assert (root / "valid" / "labels").is_dir()
    text = (root / "data.yaml").read_text(encoding="utf-8")
    assert "nc: 6" in text
    assert "scratches" in text


def test_import_and_check_pairs(tmp_path: Path):
    core = _load_core()
    src = tmp_path / "raw"
    src.mkdir()
    (src / "a.jpg").write_bytes(b"fake")
    (src / "b.jpg").write_bytes(b"fake")
    (src / "ignore.txt").write_text("x", encoding="utf-8")

    ds = tmp_path / "ds"
    core.ensure_yolo_layout(ds)
    copied = core.import_images(src, ds / "train" / "images")
    assert len(copied) == 2

    check = core.check_yolo_pairs(ds / "train" / "images", ds / "train" / "labels")
    assert check.images == 2
    assert check.paired == 0
    assert check.missing_labels == ["a", "b"]
    assert check.ok is False

    (ds / "train" / "labels" / "a.txt").write_text("0 0.5 0.5 0.1 0.1\n", encoding="utf-8")
    (ds / "train" / "labels" / "b.txt").write_text("1 0.5 0.5 0.1 0.1\n", encoding="utf-8")
    check2 = core.check_yolo_pairs(ds / "train" / "images", ds / "train" / "labels")
    assert check2.ok is True
    assert check2.paired == 2


def test_build_board_checklist_contains_wget_and_test():
    core = _load_core()
    text = core.build_board_checklist(pc_ip="192.168.2.10", http_port=8000)
    assert "wget http://192.168.2.10:8000/neu_yolov8n.param" in text
    assert "wget http://192.168.2.10:8000/neu_yolov8n.bin" in text
    assert "neu_yolov8_test scratches_10.jpg out_neu_scratches_10.jpg" in text
    assert "python -m http.server 8000" in text


def test_annotate_howto_mentions_label_url():
    core = _load_core()
    text = core.annotate_howto(dataset_root=r"E:\yolo_files\datasets\my-plant")
    assert "47.115.223.159:8903" in text
    assert "train" in text and "labels" in text

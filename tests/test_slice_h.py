# -*- coding: utf-8 -*-
"""切片 H：INT8 辅助 + DeepPCB 转换测试。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    import sys
    from importlib.util import module_from_spec, spec_from_file_location

    path = ROOT / "tools" / f"{name}.py"
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_int8_imagelist_and_recipe(tmp_path: Path):
    core = _load("int8_core")
    img_dir = tmp_path / "imgs"
    img_dir.mkdir()
    (img_dir / "a.jpg").write_bytes(b"x")
    (img_dir / "b.png").write_bytes(b"y")
    imgs = core.collect_calib_images(img_dir, limit=10)
    assert len(imgs) == 2
    out = core.write_imagelist(imgs, tmp_path / "list.txt")
    text = out.read_text(encoding="utf-8")
    assert "a.jpg" in text and "b.png" in text
    recipe = core.build_int8_recipe(imagelist=out)
    assert "ncnn2table" in recipe and "ncnn2bin" in recipe
    assert "0.00392157" in recipe


def test_deeppcb_annotation_convert():
    core = _load("deeppcb_core")
    # type 1=open → yolo 0；640x640 上 0,0,320,320
    lines = core.convert_annotation_text("0,0,320,320,1\n10 10 20 20 6\n")
    assert len(lines) == 2
    assert lines[0].startswith("0 ")
    assert lines[1].startswith("5 ")  # pin-hole
    assert core.deeppcb_type_to_yolo(0) is None
    assert core.deeppcb_type_to_yolo(3) == 2


def test_deeppcb_pairs_official_not_folder(tmp_path: Path):
    core = _load("deeppcb_core")
    img_dir = tmp_path / "PCBData" / "group00041" / "00041"
    lbl_dir = tmp_path / "PCBData" / "group00041" / "00041_not"
    img_dir.mkdir(parents=True)
    lbl_dir.mkdir(parents=True)
    (img_dir / "00041000_test.jpg").write_bytes(b"fake")
    (lbl_dir / "00041000.txt").write_text("0 0 10 10 1\n", encoding="utf-8")
    pairs = core.find_deeppcb_pairs(tmp_path)
    assert len(pairs) == 1
    assert pairs[0][1].name == "00041000.txt"


def test_deeppcb_prepare_from_synthetic(tmp_path: Path):
    core = _load("deeppcb_core")
    src = tmp_path / "raw"
    src.mkdir()
    (src / "0001_test.jpg").write_bytes(b"fake")
    (src / "0001.txt").write_text("0,0,100,100,2\n50,50,80,90,4\n", encoding="utf-8")
    (src / "0002_test.jpg").write_bytes(b"fake")
    (src / "0002.txt").write_text("1,1,30,40,1\n", encoding="utf-8")
    out = tmp_path / "ds"
    summary = core.prepare_deeppcb_subset(src, out, train_n=1, val_n=1, seed=0)
    assert summary["train_images"] >= 1
    assert (out / "data.yaml").is_file()
    assert "open" in (out / "data.yaml").read_text(encoding="utf-8")
    assert (out / "BOARD_CLASS_NAMES.txt").is_file()


def test_docs_and_demos_exist():
    assert (ROOT / "docs" / "int8-optimization.md").is_file()
    assert (ROOT / "demos" / "neu-det-slice-h-int8" / "README.md").is_file()
    assert (ROOT / "demos" / "deeppcb-slice" / "README.md").is_file()
    assert (ROOT / "board" / "deeppcb_class_names.snippet.txt").is_file()

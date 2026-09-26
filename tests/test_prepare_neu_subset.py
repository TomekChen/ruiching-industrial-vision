# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from prepare_neu_subset import CLASS_NAMES, class_from_stem, prepare  # noqa: E402


def test_class_from_stem_ok():
    assert class_from_stem("crazing_10") == "crazing"
    assert class_from_stem("rolled-in_scale_99") == "rolled-in_scale"
    assert class_from_stem("scratches_1") == "scratches"


def test_class_from_stem_reject():
    assert class_from_stem("bus") is None
    assert class_from_stem("crazing") is None
    assert class_from_stem("foo_10") is None


def test_prepare_mini_fixture(tmp_path: Path):
    """用假数据验证：每类抽 1 张 train + 1 张 valid，标注成对。"""
    src = tmp_path / "neu"
    for split in ("train", "valid"):
        (src / split / "images").mkdir(parents=True)
        (src / split / "labels").mkdir(parents=True)
        for i, cls in enumerate(CLASS_NAMES):
            stem = f"{cls}_{i + 1}"
            img = src / split / "images" / f"{stem}.jpg"
            lbl = src / split / "labels" / f"{stem}.txt"
            img.write_bytes(b"\xff\xd8\xff")  # 最小伪 jpeg 头
            lbl.write_text(f"{i} 0.5 0.5 0.2 0.2\n", encoding="utf-8")

    out = tmp_path / "out"
    summary = prepare(src, out, train_per_class=1, val_per_class=1, seed=0)
    assert summary["train_images"] == 6
    assert summary["valid_images"] == 6
    assert (out / "data.yaml").is_file()
    for p in (out / "train" / "images").glob("*.jpg"):
        assert (out / "train" / "labels" / f"{p.stem}.txt").is_file()

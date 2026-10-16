# -*- coding: utf-8 -*-
"""切片 C 工具的轻量测试（不依赖 GPU / 大权重）。"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_export_script_exists():
    assert (ROOT / "tools" / "export_neu_ncnn.py").is_file()


def test_compare_script_exists():
    assert (ROOT / "tools" / "compare_slice_a.py").is_file()


def test_slice_a_images_present():
    imgs = list((ROOT / "demos" / "neu-det-slice-a" / "images").glob("*.jpg"))
    assert len(imgs) >= 6


def test_neu_cn_keys_cover_six_classes():
    # 与 prepare / data.yaml 一致
    from importlib.util import module_from_spec, spec_from_file_location

    path = ROOT / "tools" / "compare_slice_a.py"
    spec = spec_from_file_location("compare_slice_a", path)
    assert spec and spec.loader
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    expected = {
        "crazing",
        "inclusion",
        "patches",
        "pitted_surface",
        "rolled-in_scale",
        "scratches",
    }
    assert set(mod.NEU_CN.keys()) == expected

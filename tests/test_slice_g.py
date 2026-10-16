# -*- coding: utf-8 -*-
"""切片 G：治理文件与演示脚本存在性。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_license_and_notice_exist():
    assert (ROOT / "LICENSE").is_file()
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in text
    assert (ROOT / "NOTICE").is_file()
    assert "Ultralytics" in (ROOT / "NOTICE").read_text(encoding="utf-8")


def test_governance_docs_exist():
    assert (ROOT / "CONTRIBUTING.md").is_file()
    gov = (ROOT / "docs" / "opensource-governance.md").read_text(encoding="utf-8")
    assert "Apache-2.0" in gov
    assert "维护计划" in gov


def test_demo_script_has_key_numbers():
    text = (ROOT / "demos" / "neu-det-slice-g" / "DEMO_SCRIPT.md").read_text(encoding="utf-8")
    assert "3550" in text
    assert "Apache-2.0" in text

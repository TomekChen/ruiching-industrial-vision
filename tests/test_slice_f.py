# -*- coding: utf-8 -*-
"""切片 F：报告与摘要存在性 / 关键数字一致性。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_performance_report_exists_and_has_sections():
    path = ROOT / "docs" / "performance-report.md"
    text = path.read_text(encoding="utf-8")
    for needle in (
        "模型适配与优化策略",
        "资源占用",
        "板端时延",
        "3551",
        "3027",
        "不修改",
    ):
        assert needle in text, f"missing: {needle}"


def test_slice_f_summary_matches_board_numbers():
    data = json.loads((ROOT / "demos" / "neu-det-slice-f" / "summary.json").read_text(encoding="utf-8"))
    d = data["board_latency_ms"]["slice_d_neu_yolov8"]
    assert d["scratches_10"] == 3551
    assert d["inclusion_10"] == 3548
    assert d["patches_10"] == 3552
    a = data["board_latency_ms"]["slice_a_mnet_yolov3"]
    assert a["scratches_10"] == 3027
    assert data["board_detections"]["patches_10"]["count"] == 2
    assert data["industrial_model"]["val_mAP50"] == 0.67

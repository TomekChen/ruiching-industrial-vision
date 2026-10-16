#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切片 G · 演示前一键自检（不依赖板子在线 / GPU）。

可运行信号：退出码 0，并打印「评委演示 5 步」。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ok(msg: str) -> None:
    print(f"[OK] {msg}")


def _fail(msg: str) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)


def check_files() -> list[str]:
    required = [
        ROOT / "LICENSE",
        ROOT / "NOTICE",
        ROOT / "CONTRIBUTING.md",
        ROOT / "docs" / "performance-report.md",
        ROOT / "docs" / "opensource-governance.md",
        ROOT / "board" / "applications" / "neu_yolov8.cpp",
        ROOT / "tools" / "lowcode_app.py",
        ROOT / "tools" / "lowcode_deploy.py",
        ROOT / "tools" / "collect_images.py",
        ROOT / "demos" / "neu-det-slice-f" / "summary.json",
        ROOT / "demos" / "neu-det-slice-g" / "DEMO_SCRIPT.md",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    return missing


def check_summary_numbers() -> str | None:
    path = ROOT / "demos" / "neu-det-slice-f" / "summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    d = data["board_latency_ms"]["slice_d_neu_yolov8"]
    if d.get("scratches_10") != 3551:
        return f"summary scratches_10 期望 3551，实际 {d.get('scratches_10')}"
    return None


def run_pytest() -> int:
    return subprocess.call(
        [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-q"],
        cwd=str(ROOT),
    )


def print_demo_steps() -> None:
    print(
        """
======== 评委演示 5 步（口播详见 demos/neu-det-slice-g/DEMO_SCRIPT.md）========
1. 打开性能报告：docs/performance-report.md（背：3.55s / +17% / 语义正确）
2. 启动低代码页：python tools/lowcode_app.py → http://127.0.0.1:8765/
3. 展示板端清单：E:\\yolo_files\\neu_ncnn_board_pack\\BOARD_CHECKLIST.txt
4. 串口 msh：neu_yolov8_test scratches_10.jpg out.jpg（先 Ctrl+C 清行）
5. 对比叙事：切片 A 通用模型漏检/误检 → 工业模型正确出框
===============================================================================
""".strip()
    )


def main() -> int:
    print("切片 G · demo_smoke 自检", flush=True)
    missing = check_files()
    if missing:
        _fail("缺少文件:\n  - " + "\n  - ".join(missing))
        return 1
    _ok("关键交付文件齐全")

    err = check_summary_numbers()
    if err:
        _fail(err)
        return 1
    _ok("切片 F 摘要数字一致")

    code = run_pytest()
    if code != 0:
        _fail("pytest 未全部通过")
        return code
    _ok("pytest 通过")

    print_demo_steps()
    _ok("demo_smoke 完成，可以演示")
    return 0


if __name__ == "__main__":
    # 修正成功文案：check_files 空列表时不要算错数量
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fix data.yaml absolute path, train, pull best.pt."""
from __future__ import annotations

import os
import time
from pathlib import Path

import paramiko

PASS = os.environ["GPU_SSH_PASS"]
ROOT = "/workspace/apps/ruiching-neu-train"
VENV = f"{ROOT}/venv"
RUNS = f"{ROOT}/runs"
DS = f"{ROOT}/datasets/neu-det-mini"
LOCAL_OUT = Path(r"E:\yolo_files\runs\neu-det-mini-gpu")


def log(m):
    print(m, flush=True)


def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        "219.133.7.139",
        30768,
        username="root",
        password=PASS,
        timeout=30,
        allow_agent=False,
        look_for_keys=False,
    )
    return c


def run(c, cmd, timeout=120):
    log(f"> {cmd[:160]}")
    _, o, e = c.exec_command(cmd, timeout=timeout, get_pty=False)
    out = o.read().decode("utf-8", errors="replace")
    err = e.read().decode("utf-8", errors="replace")
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-2500:], flush=True)
    return o.channel.recv_exit_status(), text


def put_text(c, text, remote):
    sftp = c.open_sftp()
    try:
        with sftp.file(remote, "w") as f:
            f.write(text)
    finally:
        sftp.close()


def sget(c, remote, local: Path):
    local.parent.mkdir(parents=True, exist_ok=True)
    sftp = c.open_sftp()
    try:
        sftp.get(remote, str(local))
        log(f"got {local} ({local.stat().st_size})")
    finally:
        sftp.close()


def main():
    c = connect()
    try:
        yaml = (
            f"path: {DS}\n"
            "train: train/images\n"
            "val: valid/images\n"
            "nc: 6\n"
            "names:\n"
            "  0: crazing\n"
            "  1: inclusion\n"
            "  2: patches\n"
            "  3: pitted_surface\n"
            "  4: rolled-in_scale\n"
            "  5: scratches\n"
        )
        put_text(c, yaml, f"{DS}/data.yaml")
        run(c, f"ls {DS}/train/images | wc -l; ls {DS}/valid/images | wc -l; cat {DS}/data.yaml")

        train_py = f"""#!/usr/bin/env python3
from ultralytics import YOLO
from pathlib import Path
model = YOLO("{ROOT}/yolov8n.pt")
model.train(
    data="{DS}/data.yaml",
    epochs=30,
    imgsz=320,
    batch=16,
    name="neu-det-mini-gpu",
    device=0,
    project="{RUNS}",
    exist_ok=True,
    amp=False,
)
print("TRAIN_DONE")
print("best_exists", Path("{RUNS}/neu-det-mini-gpu/weights/best.pt").is_file())
"""
        train_sh = f"""#!/bin/bash
set -euo pipefail
export PYTHONUNBUFFERED=1
cd {ROOT}
{VENV}/bin/python {ROOT}/train_neu.py
echo TRAIN_SHELL_DONE
"""
        put_text(c, train_py, f"{ROOT}/train_neu.py")
        put_text(c, train_sh, f"{ROOT}/train.sh")
        run(c, f"chmod +x {ROOT}/train.sh; : > {ROOT}/train.log")
        run(
            c,
            f"setsid bash {ROOT}/train.sh > {ROOT}/train.log 2>&1 < /dev/null & echo STARTED",
        )

        t0 = time.time()
        while time.time() - t0 < 3600:
            _, text = run(c, f"tail -n 30 {ROOT}/train.log")
            if "TRAIN_SHELL_DONE" in text:
                break
            if "Traceback" in text and time.time() - t0 > 45:
                _, p = run(c, "pgrep -f train_neu.py || echo NO_PROC")
                if "NO_PROC" in p:
                    raise SystemExit("train failed")
            time.sleep(15)
        else:
            raise SystemExit("timeout")

        run(c, f"ls -la {RUNS}/neu-det-mini-gpu/weights/")
        LOCAL_OUT.mkdir(parents=True, exist_ok=True)
        sget(c, f"{RUNS}/neu-det-mini-gpu/weights/best.pt", LOCAL_OUT / "best.pt")
        try:
            sget(c, f"{RUNS}/neu-det-mini-gpu/weights/last.pt", LOCAL_OUT / "last.pt")
        except Exception as e:
            log(f"last skip {e}")
        for n in ("results.csv", "args.yaml"):
            try:
                sget(c, f"{RUNS}/neu-det-mini-gpu/{n}", LOCAL_OUT / n)
            except Exception as e:
                log(f"{n} skip {e}")
        try:
            sget(c, f"{ROOT}/train.log", LOCAL_OUT / "train.log")
        except Exception:
            pass
        log(f"完成: {LOCAL_OUT / 'best.pt'}")
    finally:
        c.close()


if __name__ == "__main__":
    main()

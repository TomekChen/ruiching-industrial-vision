#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPU 远程训练编排：上传数据 → nohup 装环境/训练 → 轮询日志 → 拉回权重。

环境变量：GPU_SSH_HOST/PORT/USER/PASS，NEU_EPOCHS/IMGSZ/BATCH
"""

from __future__ import annotations

import io
import os
import sys
import tarfile
import time
from pathlib import Path

import paramiko

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

HOST = os.environ.get("GPU_SSH_HOST", "219.133.7.139")
PORT = int(os.environ.get("GPU_SSH_PORT", "30768"))
USER = os.environ.get("GPU_SSH_USER", "root")
PASS = os.environ.get("GPU_SSH_PASS", "")

LOCAL_DS = Path(os.environ.get("LOCAL_NEU_DS", r"E:\yolo_files\datasets\neu-det-mini"))
LOCAL_OUT = Path(os.environ.get("LOCAL_NEU_OUT", r"E:\yolo_files\runs\neu-det-mini-gpu"))
REMOTE_ROOT = "/workspace/apps/ruiching-neu-train"
REMOTE_DS = f"{REMOTE_ROOT}/datasets/neu-det-mini"
REMOTE_RUNS = f"{REMOTE_ROOT}/runs"
REMOTE_VENV = f"{REMOTE_ROOT}/venv"
EPOCHS = int(os.environ.get("NEU_EPOCHS", "30"))
IMGSZ = int(os.environ.get("NEU_IMGSZ", "320"))
BATCH = int(os.environ.get("NEU_BATCH", "16"))


def _safe_print(text: str) -> None:
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        sys.stdout.buffer.write((text + "\n").encode(enc, errors="replace"))
        sys.stdout.buffer.flush()


def log(msg: str) -> None:
    _safe_print(msg)


def connect() -> paramiko.SSHClient:
    if not PASS:
        raise SystemExit("请设置环境变量 GPU_SSH_PASS")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    log(f"连接 {USER}@{HOST}:{PORT} ...")
    client.connect(
        HOST,
        port=PORT,
        username=USER,
        password=PASS,
        timeout=30,
        allow_agent=False,
        look_for_keys=False,
    )
    return client


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 120) -> tuple[int, str]:
    log(f"$ {cmd}")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    text = (out or "") + (("\n" + err) if err.strip() else "")
    if text.strip():
        _safe_print(text.rstrip("\n"))
    return code, text


def sftp_put_bytes(client: paramiko.SSHClient, data: bytes, remote: str) -> None:
    sftp = client.open_sftp()
    try:
        with sftp.file(remote, "wb") as f:
            f.write(data)
        log(f"已上传 {len(data)} bytes -> {remote}")
    finally:
        sftp.close()


def sftp_put_text(client: paramiko.SSHClient, text: str, remote: str) -> None:
    sftp_put_bytes(client, text.encode("utf-8"), remote)


def sftp_get(client: paramiko.SSHClient, remote: str, local: Path) -> None:
    local.parent.mkdir(parents=True, exist_ok=True)
    sftp = client.open_sftp()
    try:
        sftp.get(remote, str(local))
        log(f"已下载 {remote} -> {local} ({local.stat().st_size} bytes)")
    finally:
        sftp.close()


def make_dataset_tarball() -> bytes:
    if not LOCAL_DS.is_dir():
        raise SystemExit(f"本地数据集不存在: {LOCAL_DS}")
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode="w:gz") as tar:
        for path in LOCAL_DS.rglob("*"):
            if path.is_file() and path.name != "data.yaml":
                arc = f"neu-det-mini/{path.relative_to(LOCAL_DS).as_posix()}"
                tar.add(path, arcname=arc)
        yaml = (
            "path: .\n"
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
        info = tarfile.TarInfo(name="neu-det-mini/data.yaml")
        data = yaml.encode("utf-8")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return bio.getvalue()


SETUP_SH = f"""#!/bin/bash
set -euo pipefail
echo "=== SETUP START $(date -Is) ==="
cd "{REMOTE_ROOT}"
if [ ! -x "{REMOTE_VENV}/bin/python" ]; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-venv python3-pip
  python3 -m venv "{REMOTE_VENV}"
fi
source "{REMOTE_VENV}/bin/activate"
export PIP_PROGRESS_BAR=off
export PYTHONUNBUFFERED=1
python -m pip install -U pip -i https://pypi.tuna.tsinghua.edu.cn/simple
if ! python -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
  echo "Installing torch cu128 ..."
  python -m pip install --progress-bar off torch torchvision --index-url https://download.pytorch.org/whl/cu128
fi
python -m pip install --progress-bar off ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple
python -c "import torch; from ultralytics import YOLO; print('OK', torch.__version__, 'cuda', torch.cuda.is_available(), 'dev', torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
echo "=== SETUP DONE $(date -Is) ==="
"""

TRAIN_SH = f"""#!/bin/bash
set -euo pipefail
echo "=== TRAIN START $(date -Is) ==="
source "{REMOTE_VENV}/bin/activate"
export PYTHONUNBUFFERED=1
cd "{REMOTE_ROOT}"
python "{REMOTE_ROOT}/train_neu.py"
echo "=== TRAIN DONE $(date -Is) ==="
"""

TRAIN_PY = f"""#!/usr/bin/env python3
from ultralytics import YOLO
from pathlib import Path

model = YOLO("yolov8n.pt")
results = model.train(
    data="{REMOTE_DS}/data.yaml",
    epochs={EPOCHS},
    imgsz={IMGSZ},
    batch={BATCH},
    name="neu-det-mini-gpu",
    device=0,
    project="{REMOTE_RUNS}",
    exist_ok=True,
)
print("TRAIN_DONE")
best = Path("{REMOTE_RUNS}/neu-det-mini-gpu/weights/best.pt")
print("best=", best, "exists=", best.is_file())
"""


def wait_for_marker(
    client: paramiko.SSHClient,
    log_path: str,
    done_marker: str,
    proc_pattern: str,
    timeout_s: int,
    poll_s: int = 20,
) -> None:
    """轮询远程日志，直到出现完成标记或超时。"""
    t0 = time.time()
    while True:
        _, text = run(
            client,
            f"echo LOG_TAIL; tail -n 20 {log_path} 2>/dev/null; "
            f"echo PROC_TAIL; ps aux | grep -E '{proc_pattern}' | grep -v grep || echo NO_PROC",
            timeout=60,
        )
        if done_marker in text:
            log(f"检测到完成标记: {done_marker}")
            return
        # 只看超时；不因短暂 NO_PROC 误杀（grep 模式易抖）
        if time.time() - t0 > timeout_s:
            raise TimeoutError(f"等待超时 {timeout_s}s，日志: {log_path}")
        time.sleep(poll_s)


def main() -> None:
    client = connect()
    try:
        run(client, "nvidia-smi || true", timeout=60)
        run(client, f"mkdir -p {REMOTE_ROOT}/datasets {REMOTE_RUNS}", timeout=30)

        # 数据集：若已存在则跳过重传
        code, _ = run(client, f"test -f {REMOTE_DS}/data.yaml && echo DS_OK || echo DS_NEED")
        if "DS_NEED" in _:
            log("打包并上传数据集...")
            tgz = make_dataset_tarball()
            remote_tgz = f"{REMOTE_ROOT}/neu-det-mini.tgz"
            sftp_put_bytes(client, tgz, remote_tgz)
            code, _ = run(
                client,
                f"rm -rf {REMOTE_DS} && tar -xzf {remote_tgz} -C {REMOTE_ROOT}/datasets "
                f"&& ls {REMOTE_DS}/train/images | wc -l",
                timeout=120,
            )
            if code != 0:
                raise SystemExit("解压数据集失败")
        else:
            log("远程数据集已存在，跳过上传")

        sftp_put_text(client, SETUP_SH, f"{REMOTE_ROOT}/setup.sh")
        sftp_put_text(client, TRAIN_SH, f"{REMOTE_ROOT}/train.sh")
        sftp_put_text(client, TRAIN_PY, f"{REMOTE_ROOT}/train_neu.py")
        run(client, f"chmod +x {REMOTE_ROOT}/setup.sh {REMOTE_ROOT}/train.sh", timeout=30)

        # 若已有可用 torch+cuda，跳过 setup
        code, out = run(
            client,
            f"{REMOTE_VENV}/bin/python -c \"import torch; assert torch.cuda.is_available(); "
            f"print('TORCH_OK', torch.__version__)\" 2>/dev/null || echo TORCH_NEED",
            timeout=60,
        )
        if "TORCH_OK" not in out:
            run(client, f": > {REMOTE_ROOT}/setup.log", timeout=10)
            run(
                client,
                f"nohup bash {REMOTE_ROOT}/setup.sh >> {REMOTE_ROOT}/setup.log 2>&1 & echo SETUP_PID=$!; sleep 1; pgrep -af setup.sh || true",
                timeout=30,
            )
            wait_for_marker(
                client,
                f"{REMOTE_ROOT}/setup.log",
                "=== SETUP DONE",
                "setup.sh|pip install",
                timeout_s=7200,
                poll_s=30,
            )
        else:
            log("Torch+CUDA 已就绪，跳过 setup")

        # 训练
        run(client, f": > {REMOTE_ROOT}/train.log", timeout=10)
        run(
            client,
            f"nohup bash {REMOTE_ROOT}/train.sh >> {REMOTE_ROOT}/train.log 2>&1 & echo TRAIN_PID=$!; sleep 1; pgrep -af train || true",
            timeout=30,
        )
        wait_for_marker(
            client,
            f"{REMOTE_ROOT}/train.log",
            "=== TRAIN DONE",
            "train.sh|train_neu.py|ultralytics",
            timeout_s=7200,
            poll_s=20,
        )

        remote_best = f"{REMOTE_RUNS}/neu-det-mini-gpu/weights/best.pt"
        remote_last = f"{REMOTE_RUNS}/neu-det-mini-gpu/weights/last.pt"
        run(client, f"ls -la {REMOTE_RUNS}/neu-det-mini-gpu/weights/", timeout=30)

        LOCAL_OUT.mkdir(parents=True, exist_ok=True)
        sftp_get(client, remote_best, LOCAL_OUT / "best.pt")
        try:
            sftp_get(client, remote_last, LOCAL_OUT / "last.pt")
        except Exception as e:
            log(f"last.pt 跳过: {e}")
        for name in ("results.csv", "args.yaml"):
            try:
                sftp_get(
                    client,
                    f"{REMOTE_RUNS}/neu-det-mini-gpu/{name}",
                    LOCAL_OUT / name,
                )
            except Exception as e:
                log(f"{name} 跳过: {e}")

        # 拉一份训练日志
        try:
            sftp_get(client, f"{REMOTE_ROOT}/train.log", LOCAL_OUT / "train.log")
        except Exception:
            pass

        log(f"完成。本地权重: {LOCAL_OUT / 'best.pt'}")
    finally:
        client.close()


if __name__ == "__main__":
    main()

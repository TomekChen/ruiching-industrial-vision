# PC 侧工具

## 切片 B：NEU 工业子集整理 + 训练入口

NEU-DET **已自带 YOLO 标注**，本切片不再手动画框，而是：

1. 从完整 NEU 抽样生成小数据集（每类均衡）  
2. 用 Ultralytics 训练轻量模型（`yolov8n`）  
3. 导出 ONNX/NCNN 并对比切片 A（切片 C，见下）

### 1. 生成子集

```text
cd /d F:\projects\ruiching-industrial-vision
python tools\prepare_neu_subset.py --train-per-class 40 --val-per-class 5
```

默认：

- 源：`E:\yolo_files\data\NEU-DET\images\NEU-DET`
- 出：`E:\yolo_files\datasets\neu-det-mini\`（含 `data.yaml`、`summary.json`）

### 2. 训练（需安装 ultralytics）

```text
pip install ultralytics
python tools\train_neu_yolo.py --epochs 30 --device cpu
```

有 NVIDIA GPU 时把 `--device cpu` 改成 `--device 0`。  
权重输出：`E:\yolo_files\runs\neu-det-mini-gpu\best.pt`（GPU 正式训）或 smoke 目录。

### 3. 自测

```text
pip install pytest
python -m pytest tests\test_prepare_neu_subset.py tests\test_slice_c_tools.py -q
```

## 切片 C：导出 + 对比切片 A

```text
python tools\compare_slice_a.py
python tools\export_neu_ncnn.py
python tools\pack_neu_board.py
```

| 脚本 | 作用 |
|---|---|
| `compare_slice_a.py` | 对切片 A 同图推理，写 `demos/neu-det-slice-c/` |
| `export_neu_ncnn.py` | `best.pt` → ONNX + NCNN |
| `pack_neu_board.py` | 打成 `E:\yolo_files\neu_ncnn_board_pack\` 供 wget |

说明：板端 `mnet_yolov3_test` **不能**直接加载 YOLOv8 NCNN。  
切片 D 已提供板端命令源码：`board/applications/neu_yolov8.cpp`，操作见 `demos/neu-det-slice-d/README.md`。

## 切片 E：采图 / 标注入口 + 低代码部署

```text
:: 浏览器低代码页（推荐）
python tools\lowcode_app.py
:: 打开 http://127.0.0.1:8765/

:: 或命令行
python tools\collect_images.py --init --root E:\yolo_files\datasets\my-plant
python tools\collect_images.py --check --root E:\yolo_files\datasets\my-plant
python tools\lowcode_deploy.py --pc-ip 192.168.2.10
```

| 脚本 | 作用 |
|---|---|
| `slice_e_core.py` | 核心：建目录 / 导图 / 检标注 / 板端清单 |
| `collect_images.py` | 采图入库 + 标注校验 |
| `lowcode_deploy.py` | 打包 + 写出 `BOARD_CHECKLIST.txt` |
| `lowcode_app.py` | 本地网页低代码入口 |

说明见 `demos/neu-det-slice-e/README.md`。

## 切片 G：演示前自检

```text
python tools\demo_smoke.py
```

口播稿：`demos/neu-det-slice-g/DEMO_SCRIPT.md`。

## 切片 H：INT8 + DeepPCB

```text
:: INT8 材料（校准列表 + 菜谱）
python tools\quantize_neu_int8.py
:: 可选尝试 Ultralytics INT8
python tools\quantize_neu_int8.py --try-ultralytics

:: DeepPCB（需先下载解压到 --src）
python tools\prepare_deeppcb_subset.py --src E:\yolo_files\data\DeepPCB
python tools\train_deeppcb_yolo.py --device cpu --epochs 3
```

说明：`demos/neu-det-slice-h-int8/`、`demos/deeppcb-slice/`、`docs/int8-optimization.md`。

## 标注工具（可选）

若要标自己的产线图，可用阿里云智标：http://47.115.223.159:8903/  
导出 YOLO txt 后，目录结构对齐 `train/images` + `train/labels` 即可复用上面的训练脚本。


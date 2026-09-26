# PC 侧工具

## 切片 B：NEU 工业子集整理 + 训练入口

NEU-DET **已自带 YOLO 标注**，本切片不再手动画框，而是：

1. 从完整 NEU 抽样生成小数据集（每类均衡）  
2. 用 Ultralytics 训练轻量模型（`yolov8n`）  
3. 下一步再转 ONNX → NCNN 上板（切片 D）

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
权重输出：`E:\yolo_files\runs\detect\neu-det-mini\weights\best.pt`

### 3. 自测

```text
pip install pytest
python -m pytest tests\test_prepare_neu_subset.py -q
```

## 标注工具（可选）

若以后要标自己的产线图，可用阿里云智标：http://47.115.223.159:8903/  
导出 YOLO txt 后，目录结构对齐 `train/images` + `train/labels` 即可复用上面的训练脚本。

# 切片 H-1：INT8 量化加速

> 主路径仍是 FP32 NCNN（已真机验证）。INT8 用于**进一步降时延/体积**，需本机有 `ncnn2table` / `ncnn2bin` 或 Ultralytics INT8 导出。

## 一键准备材料

```text
cd /d F:\projects\ruiching-industrial-vision
python tools\quantize_neu_int8.py
```

产出（默认）：

```text
E:\yolo_files\exports\neu-int8\
  calib_imagelist.txt
  INT8_RECIPE.txt
  INT8_BOARD_CHECKLIST.txt
  neu_yolov8n.param / .bin   （若上板包已存在则自动拷贝）
```

## 量化（二选一）

### A. NCNN 官方工具（推荐，与板端一致）

按 `INT8_RECIPE.txt` 执行 `ncnn2table` → `ncnn2bin`。

### B. Ultralytics

```text
python tools\quantize_neu_int8.py --try-ultralytics
```

需要 `best.pt` + `neu-det-mini/data.yaml`。

## 上板对比

1. 把 `neu_yolov8n_int8.param/.bin` 放进 `neu_ncnn_board_pack`  
2. 按 `INT8_BOARD_CHECKLIST.txt` wget  
3. 覆盖或改加载名后跑同一张 `scratches_10.jpg`  
4. 把 detect ms 与 FP32（~3550）对比，写回 `DEV_LOG`

## 注意

- INT8 可能掉点，应用同一批图看召回/误检  
- 板端预处理仍是 `/255`；菜谱里 norm≈`1/255`  
- 无量化工具时，本切片仍算「完整优化方案文档 + 可复现脚本」交付  

详解：[`docs/int8-optimization.md`](../../docs/int8-optimization.md)

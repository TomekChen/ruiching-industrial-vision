# 切片 C：自定义 NEU 模型导出 + 对比切片 A

**目标**：把 GPU 训好的 `best.pt` 转成部署格式，并对**切片 A 同一批工业图**做推理对比，证明「换工业模型后能检出缺陷」。

**本切片可运行信号（已达成）**：

1. ONNX / NCNN 导出成功  
2. PC 上 NCNN 推理 `scratches_10.jpg` 检出 6 框（与 `.pt` 一致）  
3. 8 张切片 A 图共检出 **17** 框；切片 A 通用模型板上几乎漏检  

## 对比结论（写报告可直接用）

| 图片 | 切片 A（板上通用 YOLOv3/COCO） | 切片 C（PC · NEU yolov8n） |
|---|---|---|
| crazing_10.jpg | 无检出 ~3050 ms | 0（该类本子集仍偏弱） |
| inclusion_10.jpg | 无检出 | **3** inclusion（最高 conf 0.75） |
| patches_10.jpg | （未单记） | **2** patches（0.90 / 0.84） |
| scratches_10.jpg | 误检 COCO 类5 | **6** scratches |
| 其余 4 张 | — | 均有检出（合计见 summary） |

→ **链路 + 模型都要用对**：板子能跑 ≠ 通用模型适配工业缺陷；自定义 NEU 模型在同图上明显更好。

## 本目录

| 路径 | 说明 |
|---|---|
| `compare/*_pred.jpg` | 画框图 |
| `summary.json` | 逐张检出明细 |

## 电脑侧产物

| 文件 | 路径 |
|---|---|
| ONNX | `E:\yolo_files\exports\neu-det-mini-gpu\best.onnx` |
| NCNN | `E:\yolo_files\exports\neu-det-mini-gpu\best_ncnn_model\`（`model.ncnn.param` / `.bin`） |
| 上板打包 | `E:\yolo_files\neu_ncnn_board_pack\`（已改名 `neu_yolov8n.param/.bin` + 8 张图 + names.txt） |

## 一键复现

```text
cd /d F:\projects\ruiching-industrial-vision
python tools\compare_slice_a.py
python tools\export_neu_ncnn.py
```

## 关于上板（重要）

板端现有命令 **`mnet_yolov3_test` 只能加载 MobileNetV2-YOLOv3**（输入 `data` / 输出 `detection_out`，VOC 类别）。

本导出的 YOLOv8 NCNN：

- 输入 blob：`in0`
- 输出 blob：`out0`
- 输入尺寸：320×320
- 6 类 NEU 名称见 `names.txt`

**不能**把 `neu_yolov8n.param/.bin` 直接塞进 `mnet_yolov3_test`。  
下一刀（切片 D）：在 RuiChing Studio 里改/加一个 `neu_yolov8_test`（参考本仓库 `board/neu_yolov8_ncnn_notes.md`），再 wget 上板实测时延。

文件已可先传到板子 `/data` 备用：

```text
cd /d E:\yolo_files\neu_ncnn_board_pack
python -m http.server 8000
```

```text
cd /data
wget http://电脑IP:8000/neu_yolov8n.param neu_yolov8n.param
wget http://电脑IP:8000/neu_yolov8n.bin neu_yolov8n.bin
```

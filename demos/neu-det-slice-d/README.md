# 切片 D：板端 `neu_yolov8_test`（工业模型上板）

## 这一阶段要学会什么

| 步骤 | 你学到什么 |
|---|---|
| 1. 读 `board/applications/neu_yolov8.cpp` | YOLOv8 NCNN 与旧 YOLOv3 在输入/输出/后处理上差在哪 |
| 2. 源码进 RuiChing 工程 | 板端应用怎么挂到 `applications/` + 出现 msh 命令 |
| 3. 编译烧录 | Studio 出 `app.img`，替换板上固件 |
| 4. wget 模型+图 | 和切片 A 一样的传文件路径 |
| 5. 跑同图对比 | 通用模型漏检 vs 工业模型有检出 |

## 源码位置（两份必须一致）

| 路径 | 用途 |
|---|---|
| 仓库 `board/applications/neu_yolov8.cpp` | **学习/版本管理**（改这里再复制） |
| `F:\ruiching-workspace\yolo_183\applications\neu_yolov8.cpp` | **真正编译**（你 Studio 里打开的工程） |

同步命令（PowerShell）：

```text
Copy-Item -Force F:\projects\ruiching-industrial-vision\board\applications\neu_yolov8.cpp F:\ruiching-workspace\yolo_183\applications\neu_yolov8.cpp
```

## 编译（RuiChing Studio · 工程名 yolo_183）

1. 打开工程 **`yolo_183`**（路径在 `F:\ruiching-workspace\`）  
2. 在资源管理器里 **右键工程根 `yolo_183` → Refresh（刷新）**  
3. 展开 `applications`，应能看到 **`neu_yolov8.cpp`**（和 `yolov3.cpp` 并列）  
4. **Project → Build Project**（Debug）  
5. 成功后烧录 `app.img`  
6. 串口进 `msh`，输入 `neu` 再按 Tab，应出现 `neu_yolov8_test`

> 已改过 `Debug/applications/subdir.mk`。若刷新后仍看不到文件：在资源管理器空白处右键 → Refresh，或关掉工程再打开。

## 上传模型与图

电脑：

```text
cd /d E:\yolo_files\neu_ncnn_board_pack
python -m http.server 8000
```

板子（IP 换成你的电脑）：

```text
cd /data
wget http://电脑IP:8000/neu_yolov8n.param neu_yolov8n.param
wget http://电脑IP:8000/neu_yolov8n.bin neu_yolov8n.bin
wget http://电脑IP:8000/scratches_10.jpg scratches_10.jpg
wget http://电脑IP:8000/inclusion_10.jpg inclusion_10.jpg
wget http://电脑IP:8000/patches_10.jpg patches_10.jpg
ls /data
```

## 推理

```text
cd /data
neu_yolov8_test scratches_10.jpg out_neu_scratches_10.jpg
neu_yolov8_test inclusion_10.jpg out_neu_inclusion_10.jpg
neu_yolov8_test patches_10.jpg out_neu_patches_10.jpg
```

看串口：

- `out shape w=2100 h=10` → 模型输出形状对  
- `kept=N` 且有 `scratches/inclusion/...` 行 → 检出成功  
- `detect end : xxx ms` → 记进 DEV_LOG 对比切片 A（约 3000 ms）

## 真机结果（2026-09-27）

| 图片 | detect | 结果 |
|---|---|---|
| scratches_10.jpg | 3551 ms | 5× scratches（最高 0.781） |
| inclusion_10.jpg | 3548 ms | 3× inclusion（最高 0.753） |
| patches_10.jpg | 3552 ms | 2× patches（0.895 / 0.843） |

## 成功标准

1. msh 有 `neu_yolov8_test`  
2. 至少 1 张工业图 `execute done` 且 `detections>0`  
3. 类别名是 NEU 六类之一（不是 COCO 的 bus/person）

## 和切片 A/C 的关系

- **A**：板上通用 YOLOv3 → 工业图漏检/误检  
- **C**：PC 上同一权重已证明能检出  
- **D**：把 C 的 NCNN 权重搬到板子，用新命令跑通  

若 D 编译 OOM / 太慢：先保持 `use_vulkan_compute=false`、`num_threads=2`（源码默认已如此）。

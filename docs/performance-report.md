# 适配方案与性能测试报告

> 项目：睿擎工业视觉轻量化适配工具链  
> 赛题：基于睿擎工业开发平台的预训练视觉模型轻量化适配与低代码部署优化（赛题 7）  
> 硬件：睿擎派 RC-Pi-3506（EMMC 8GB / 512MB，三核 Cortex-A7）  
> 软件：RuiChing SDK APP 1.8.3（SMP / RT-Thread）+ NCNN  
> 报告日期：2026-09-28  
> 对应切片：A（基线）→ B（训练）→ C（PC 对比）→ D（板端工业模型）→ E（低代码工具）

---

## 1. 报告目的

回答赛题交付中的「适配方案与性能测试」要求：

1. **模型优化策略**是否清晰、可复现  
2. **端侧推理是否稳定**、时延是否可记录对比  
3. **精度/语义**相对官方通用 YOLOv3 是否有可解释增益  
4. **资源占用**（权重体积、线程与算子路径）是否可控  

本报告数据均来自本仓库 `DEV_LOG.md` 与 `demos/neu-det-slice-*` 真机/PC 回填，可复现。

---

## 2. 测试环境

| 项 | 说明 |
|---|---|
| 开发板 | RC-Pi-3506，512MB RAM，8GB EMMC |
| 系统 | RuiChing / RT-Thread SMP 1.8.3 |
| 推理框架 | NCNN（板端关闭 Vulkan，`num_threads=2`） |
| 对比基线 | 官方例程 `mnet_yolov3_test` + MobileNetV2-YOLOv3（COCO） |
| 工业模型 | 自训 YOLOv8n（NEU-DET 子集）→ ONNX → NCNN → `neu_yolov8_test` |
| 输入尺寸 | 工业模型 letterbox **320**；官方例程按原工程（约 352） |
| 测试图 | NEU-DET 钢表面缺陷样例（切片 A 同图复用） |
| 串口 | 115200；命令在 `/data` 下执行 |

---

## 3. 模型适配与优化策略

### 3.1 问题定义

官方仅提供 **通用目标检测**（COCO 语义）。工业钢表面缺陷（划痕、夹杂、斑块等）在通用模型上表现为 **漏检或乱报类别**，无法作为产线质检语义。

### 3.2 适配路径（不改实时内核）

```text
NEU-DET 子集整理
  → Ultralytics YOLOv8n 训练（GPU，30 epoch）
  → 导出 ONNX + NCNN（imgsz=320）
  → 板端新增 neu_yolov8_test（OpenCV 读图 + letterbox + NMS）
  → 低代码清单 / 网页（切片 E）指导 wget 与推理命令
```

### 3.3 轻量化与兼容要点

| 策略 | 做法 | 目的 |
|---|---|---|
| 小骨干 | YOLOv8**n** | 控制权重体积与算力 |
| 小输入 | **320** letterbox | 降算量，贴合板端 |
| 算子路径 | NCNN CPU，`use_vulkan_compute=false` | 避免板端 Vulkan/驱动不确定因素 |
| 线程 | `num_threads=2` | 与多核实时系统折中，降低抖动 |
| 后处理 | 板端阈值阈值 + NMS | 兼容 Ultralytics NCNN 原始 `out0` 输出 |
| 命名 | 上板文件固定 `neu_yolov8n.param/.bin` | 降低部署出错率 |

### 3.4 实时调度说明（与内核关系）

- **不修改** RT-Thread / 睿擎实时内核调度策略。  
- 推理作为 `msh` 命令同步执行：读图 → `detect` → 画框写盘，便于计时与演示。  
- 产线若需与控制任务并行，可在应用层将推理放到独立线程并限制 `num_threads`，本 Demo 保持「可测、可复现」优先。

---

## 4. 资源占用

| 资产 | 大小（约） | 说明 |
|---|---|---|
| 工业 NCNN `neu_yolov8n.bin` | **11.5 MB**（12,052,728 B） | 板上 `/data` 常驻权重 |
| 工业 NCNN `neu_yolov8n.param` | **16 KB** | 网络结构 |
| 导出 ONNX `best.onnx` | **11.6 MB** | PC 侧中间产物 |
| 官方 `mobilenetv2_yolov3.bin` | **7.1 MB** | 基线对照 |
| 板端 RAM | 设备标称 **512 MB** | 本测试未做精细 RSS 采样；配置上关闭 Vulkan、双线程，实测可稳定完成三张图推理 |

> 说明：主交付路径为 **FP32 NCNN**（真机已验证）。INT8 材料与菜谱见切片 H：`docs/int8-optimization.md`、`python tools/quantize_neu_int8.py`；完成量化后请把同图时延回填本表。

---

## 5. 训练精度（PC / 验证集）

| 阶段 | 配置 | 指标 |
|---|---|---|
| 冒烟 | CPU · 5 epoch | val mAP50 ≈ **0.43** |
| 正式 | 速桥云 RTX 5090 · 30 epoch · yolov8n | val mAP50 ≈ **0.67**（约 epoch 20 最佳） |

数据集：NEU-DET 均衡子集（`neu-det-mini`），6 类缺陷。  
训练产物：`E:\yolo_files\runs\neu-det-mini-gpu\best.pt`。

---

## 6. PC 侧同图对比（切片 C）

条件：同一 `best.pt`，`imgsz=320`，`conf=0.25`；样例 8 张，共检出 **17** 框。

| 图片 | 切片 A 板端（通用 YOLOv3） | 切片 C PC（NEU 模型） |
|---|---|---|
| scratches_10.jpg | ~3027 ms，误检 COCO 类5（conf≈0.42） | **6× scratches** |
| inclusion_10.jpg | ~3026 ms，**无检出** | **3× inclusion** |
| patches_10.jpg | （未单记） | **2× patches** |
| 其余 NEU 样例 | 多为漏检/非工业语义 | 有对应类别检出 |

**结论（PC）**：问题不在「板子跑不动」，而在「必须换成工业语义模型」。

原始汇总：`demos/neu-det-slice-c/summary.json`。

---

## 7. 板端时延与语义对比（切片 A vs D）

### 7.1 官方通用模型（切片 A · `mnet_yolov3_test`）

| 图片 | imread | detect | draw | 语义结果 |
|---|---|---|---|---|
| scratches_10.jpg | 5 ms | **3027 ms** | 30 ms | 误检 COCO 类，非「划痕」 |
| inclusion_10.jpg | 7 ms | **3026 ms** | 23 ms | **无框** |
| bus.jpg（官方样例） | — | **~3072 ms** | — | COCO 正常（证明链路通） |

### 7.2 工业 NEU 模型（切片 D · `neu_yolov8_test`）

| 图片 | imread | detect | draw | 语义结果 |
|---|---|---|---|---|
| scratches_10.jpg | 7 ms | **3551 ms** | 62 ms | **5× scratches**（最高 conf 0.781） |
| inclusion_10.jpg | 6 ms | **3548 ms** | 47 ms | **3× inclusion**（最高 conf 0.753） |
| patches_10.jpg | 9 ms | **3552 ms** | 51 ms | **2× patches**（0.895 / 0.843） |

输出形状校验：`out shape w=2100 h=10 c=1`（与 YOLOv8 NCNN 导出一致）。

### 7.3 对照摘要

| 维度 | 通用 YOLOv3（A） | 工业 YOLOv8n NCNN（D） |
|---|---|---|
| 单帧 detect 时延 | ≈ **3.03 s** | ≈ **3.55 s** |
| 相对基线 | — | 约 **+17%** 时延 |
| 工业语义 | 漏检 / 误检 | **类别正确、置信度可用** |
| 工程代价 | 官方现成 | 新增板端解码 + 权重 ~11.5 MB |

**解读**：时延仍在同一量级（约 3～3.6 s / 帧，当前 Demo 配置）。换来的是 **可交付的工业缺陷语义**，符合赛题「定制场景落地」而非单纯刷 FPS。

---

## 8. 工具链完整性（与性能相关的可复现性）

| 环节 | 状态 | 入口 |
|---|---|---|
| 采图规整 | ✅ | `tools/collect_images.py` / 低代码页 |
| 标注入口 | ✅ | 智标 + YOLO 目录约定 |
| 训练 | ✅ | `tools/train_neu_yolo.py` / GPU 脚本 |
| 导出 NCNN | ✅ | `tools/export_neu_ncnn.py` |
| 低代码部署清单 | ✅ | `tools/lowcode_deploy.py`、`lowcode_app.py` |
| 板端推理 | ✅ | `neu_yolov8_test` |

低代码页：`python tools/lowcode_app.py` → http://127.0.0.1:8765/

---

## 9. 风险、局限与后续优化

| 项 | 现状 | 建议 |
|---|---|---|
| 绝对 FPS | ~0.28 FPS（3.55 s/帧） | 量化 INT8、进一步减输入、或评估板端加速路径 |
| 精度 | mini 子集 mAP50≈0.67 | 扩数据、加难例、标定阈值阈值 |
| 内存精细账 | 未做 RSS 曲线 | 提交前可补一次 `free` / 任务栈观测 |
| 多图吞吐 | 同步命令串行 | 产线版可做队列 + 结果落盘 |

---

## 10. 总评（对应赛题评分点）

| 评分维度 | 本报告证据 |
|---|---|
| 全流程工具完整性 | 采图→标注入口→训练→导出→低代码清单→板端命令已闭环 |
| 工业平台适配性 | 真机 NCNN 稳定出框；不改内核；文件与命令约定清晰 |
| 模型适配优化效果 | 相对通用模型：语义从失败→成功；时延同量级（+17%） |
| 工具易用性 | 网页三步 + `BOARD_CHECKLIST.txt` 可复制上板 |

**一句话结论**：在睿擎派上，用轻量 YOLOv8n + NCNN 完成工业缺陷定制部署是可行的；相对官方通用检测，**时延可接受地略增，语义收益决定性**。

---

## 附录 A · 板端串口原文要点（切片 D）

```text
# scratches_10
out shape w=2100 h=10 c=1
proposals=16 kept=5
detect end : 3551 ms
5 scratches = 0.781 / 0.614 / 0.389 / 0.286 / 0.277

# inclusion_10
proposals=23 kept=3
detect end : 3548 ms
1 inclusion = 0.753 / 0.620 / 0.578

# patches_10
proposals=17 kept=2
detect end : 3552 ms
2 patches = 0.895 / 0.843
```

## 附录 B · 相关路径

| 内容 | 路径 |
|---|---|
| 本报告 | `docs/performance-report.md` |
| 开发日志 | `DEV_LOG.md` |
| 切片 C 汇总 | `demos/neu-det-slice-c/summary.json` |
| 切片 F 摘要 | `demos/neu-det-slice-f/summary.json` |
| 上板包 | `E:\yolo_files\neu_ncnn_board_pack\` |
| 板端源码 | `board/applications/neu_yolov8.cpp` |

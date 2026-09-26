# 开发日志

> 用通俗中文记录「做了什么、为什么、踩过什么坑」。比赛提交时本文件是重要材料。

## 项目信息

- **赛事**：2026 上海开源软件应用创新大赛
- **赛道**：AI+工业软件
- **命题**：睿赛德 · 基于睿擎平台的预训练视觉模型轻量化适配与低代码部署优化（赛题 7）
- **仓库**：https://github.com/TomekChen/ruiching-industrial-vision
- **硬件**：睿擎派 RC-Pi-3506（EMMC 8GB / 512MB）
- **软件**：RuiChing Studio + SDK APP 1.8.3（SMP / RT-Thread）
- **截止日期**：2026-10-11

## 评审对齐（两套分数都要盯）

### 赛题评分

| 维度 | 权重 | 我们的应对 |
|---|---|---|
| 全流程工具完整性 | 40% | 采集→标注→模型适配→端侧部署闭环 |
| 工业平台适配性 | 30% | 真机跑在睿擎派 + NCNN |
| 模型适配优化效果 | 15% | 量化/兼容，精度损耗可控，有对比数据 |
| 工具易用性 | 15% | 低代码、可视化配置 |

### 大赛总评

| 维度 | 权重 | 我们的应对 |
|---|---|---|
| 技术创新 | 30% | 轻量化适配 + 低代码部署相对官方仅 YOLOv3 例程的增量 |
| 场景落地 | 30% | 可部署、可复现 Demo + 实测数据 |
| 开源治理 | 20% | LICENSE、README、贡献说明、依赖合规 |
| 长期发展 | 20% | 路线图、维护计划 |

---

## 赛题痛点与创新点（人话版）

### 痛点（官方缺什么）

睿擎平台本身已经有：**高实时内核 + NCNN + 官方 YOLOv3 通用检测例程**。  
缺的是工业落地整条链：

1. **没法方便采现场图**（工件/缺陷图采集与管理）
2. **没法方便标注**（缺陷框标注 → 训练用标准数据集）
3. **没法方便换自己的工业模型**（只认官方通用 YOLOv3，自定义模型导入难）
4. **全程要写代码**，门槛高，不适合产线快速试错

一句话：**底座很强，工具链空心；能跑通 Demo，难做成工业定制。**

### 创新点 / 我们要补什么

不改实时内核，在上面「轻量补工具」：

| 交付物 | 对应痛点 | 评分权重 |
|---|---|---|
| 工业数据采集与标注工具 | 采图 + 标注 + 数据集导出 | 全流程 40% 的前半 |
| 自定义模型低代码部署工具 | 导入 / 量化 / 一键部署 / 看结果 | 全流程后半 + 易用性 15% |
| 适配方案与性能测试报告 | 时延、资源、精度对比 | 模型优化 15% + 平台适配 30% |
| 可运行工业缺陷 Demo | 稳定可复现 | 场景落地 |

**创新叙事建议**：不是「再做一个 YOLO」，而是「把睿擎从『能跑通用检测』补成『工业缺陷定制闭环』，且贴合高实时端侧」。

---

## 2026-09-14～09-15 · 需求对齐与资料准备

1. 确认赛题仓库侧重点是 **睿擎工业开发平台**（Studio + SDK + 板子），不是单纯 rt-thread 内核仓。
2. 网盘资料核对：保留 SDK `APP_1.8.3`、EMMC 固件、规格书与必要工具。
3. 硬件选型：**RC-Pi-3506（512MB + 8GB EMMC）**，刷机用 EMMC 固件。

---

## 2026-09-16～09-24 · 硬件与环境摸底

1. 板子到货；接口入门（POWER / DEBUG / USB OTG / RESET / RECOVER / USB HOST / ETH）。
2. USB-TTL 接 DEBUG（GND↔GND，TX↔RX 交叉），115200 串口。
3. 安装 CH340、DriverAssitant、RKDevTool；区分 LOADER / ADB 模式。
4. 踩坑摘要：
   - TX/RX 接反 → 无日志
   - 刷 AMP 固件 → 串口是 Linux，不是 `msh`；工业例程要用 **SMP + RT-Thread**
   - 内核/APP 版本必须同为 **1.8.3**
   - Studio 要用「新建例程」而不是随便 Import 空工程（否则缺头文件）

---

## 2026-09-25 · 官方 YOLO 真机跑通（里程碑 ✅）

### 做了什么

1. RuiChing Studio 基于 BSP **1.8.3** 编译 YOLO 例程工程 `yolo_183`，生成 `app.img`。
2. RKDevTool（LOADER）只烧 **app** 分区 → RESET 进 `msh`。
3. 确认命令：`mnet_yolov3_test`；`fw_version` App 编译时间变为当日。
4. **无 SD 卡传模型**：U 盘挂载失败（`sda` 识别但 `mount … elm` 失败）；固件无 `ftp_server`。
5. 改用 **网线 + PC 端 `python -m http.server` + 板端 `wget`**，把文件落到 `/data`：
   - `mobilenetv2_yolov3.param`（~9.5KB）
   - `mobilenetv2_yolov3.bin`（~7.1MB）
   - `bus.jpg`
6. 网段对齐：板子 `e1` 与电脑需同网段；`ifconfig` 改 IP 须四参数：  
   `ifconfig e1 <ip> <gw> <mask>`（只写 IP 无效）。

### 真机结果（成功）

```text
msh /data> mnet_yolov3_test bus.jpg out.jpg
Hello RT-Thread NCNN
execute imread end : 156 ms
execute detect_yolov3 end : 3072 ms
15 = 0.99720 ...
6  = 0.96088 ...
15 = 0.95704 ...
execute draw_objects end : 619 ms
execute done
```

| 阶段 | 耗时 |
|---|---|
| 读图 imread | 156 ms |
| 推理 detect_yolov3 | **3072 ms**（约 3.1 s） |
| 画框 draw_objects | 619 ms |

> 说明：当前是 **COCO 通用模型 + 公交车图**，证明「NCNN 端侧链路通」。下一步必须换成 **工业缺陷图 + 自定义/轻量化模型**，才对齐赛题「工业定制」。

### 板端经验备忘

- `ls` 文件名后的数字是**字节大小**，不是文件名一部分。
- RT-Thread `msh` **多数命令不支持 Ctrl+C**，卡住可 RESET。
- `/data` 对应 userdata 分区，可持久放模型与图片。

---

## 阿里云 DockDeck 可复用资产盘点（2026-09-25）

工作台：http://47.115.223.159:8910/  
原则：**借流程与 UI 思路 / 可选对接源码，不整包搬成「别人的产品交差」**；最终交付必须跑在睿擎板上并开源在本仓库。

| 优先级 | 项目 / 镜像 | 访问 | 能借用什么 | 和赛题关系 |
|---|---|---|---|---|
| **P0** | **智标 / x-anylabeling**（`zhilabel:4.0.6`） | :8903 | 工业级标注 UI、导出 VOC/YOLO | 直接对应「样本标注」交付 |
| **P0** | **智眸 YOLO**（`zhimou-yolo:local`，目录 `xiaohaige-yolo`） | :8807 | 上传图、画框、划分数据集、训练/导出流水线 | 对应采集管理 + 低代码训练侧；导出后需再转 NCNN 上板 |
| **P0** | **MES 视觉缺陷检测**（`mes-vision-detect-app`） | :8090 | .NET + OpenCV + ONNX 缺陷检测 Demo；`wwwroot/samples` 已有 **NEU 钢表面**样例图 | 工业场景 Demo / 对比基线（PC 侧）；板上仍走 NCNN |
| **P1** | **智能制造专区**（`ai-manufacturing-zone-app`） | :8804 | 制造场景 Web 壳、展示页结构 | 可借鉴低代码门户布局，非核心算法 |
| **P2** | **天巡无人机**（含 YOLOv8） | :8905 | 另一套 YOLO 业务集成参考 | 场景偏安防/无人机，工业缺陷贴合度一般 |
| — | DockDeck 本身 | :8910 | 只是运维看板 | **不写入赛题交付** |

### 明确不建议当赛题主干的

FinRobot、高科 MES（业务 MES）、智屏 go-view、Waxberry、Weknora、CAD Studio 等——与「睿擎端侧 NCNN 工业视觉工具链」主线弱相关。

### 建议的「借用 → 自研」路径

```text
采图/管理  ← 参考 智眸上传与项目结构（精简做成 PC 小工具）
标注       ← 可本地/浏览器用 智标(X-AnyLabeling)，导出 YOLO txt
训练(可选) ← PC 上 Ultralytics / 智眸；产出 .pt/.onnx
转换       ← onnx → ncnn（param/bin），做「一键转换」脚本/小 UI
部署       ← 本仓库脚本 + 睿擎 app（已验证 wget→/data→mnet_yolov3_test）
报告       ← 记录时延/内存/精度（通用模型 vs 工业模型）
```

---

## 工业场景图片：去哪里下（手动）

> 目标：替换 `bus.jpg`，用真实工业缺陷图做 Demo 与后续训练。

| 数据集 | 内容 | 推荐下载入口 | 备注 |
|---|---|---|---|
| **NEU-DET**（优先） | 热轧钢带 6 类表面缺陷，1800 张 200×200 | [IEEE DataPort NEU-DET](https://ieee-dataport.org/documents/neu-det)；百度网盘常见镜像码 `pmqx`；或问同学要已下好的包 | 阿里云 `mes-vision-detect` 的 `wwwroot/samples/` 已有若干 `neu_*.jpg`，可先拷几张上板试跑 |
| **DeepPCB** | PCB 缺陷 6 类，带框标注 | [交大页下载 zip](http://www.pami.sjtu.edu.cn/Show/56/77)；[GitHub tangsanli5201/DeepPCB](https://github.com/tangsanli5201/DeepPCB) | 电子制造很贴「工业软件」叙事 |
| **PCB-AoI** | PCB AOI，VOC XML | [KubeEdge Ianvs 说明 / Kaggle](https://ianvs.readthedocs.io/en/latest/proposals/scenarios/industrial-defect-detection/pcb-aoi.html) | 标注格式标准，利于写导出工具 |
| **MVTec AD** | 多种工业异常（偏分割/异常） | [MVTec AD 官网](https://www.mvtec.com/company/research/datasets/mvtec-ad) | 需注册；更适合「有无缺陷」叙事，检测框要额外处理 |
| **GC10-DET** | 金属表面缺陷 | GitHub / 学术网盘检索 `GC10-DET` | 与 NEU 同类，可作扩充 |

**本周最小动作（不用先训练）：** 见下方「切片 A」。

---

## 2026-09-26 · 切片 A：主场景定为 NEU 钢表面

### 决策

- Demo 主场景：**A · NEU-DET 热轧钢表面 6 类缺陷**（DeepPCB 作备选素材，不作为第一切片）。
- 本切片只做「工业图上板 + 通用 YOLO 试跑」，**不训练**。

### 已准备

| 位置 | 内容 |
|---|---|
| `demos/neu-det-slice-a/` | 8 张样例图 + 操作说明 |
| `E:\yolo_files\neu_board_pack\` | 同上，供 `python -m http.server 8000` |
| `E:\yolo_files\data\NEU-DET\` | 完整数据集（YOLO 格式） |

样例覆盖：`crazing / inclusion / patches / pitted_surface / rolled-in_scale / scratches`。

### 你要做的（真机）

按 [demos/neu-det-slice-a/README.md](./demos/neu-det-slice-a/README.md)：上电 → wget 八张图到 `/data` → `mnet_yolov3_test` → 把串口输出回填。

### 切片 A 实测（2026-09-26 ✅）

网络备忘：直连时只用 **e0**（`192.168.2.100`）↔ 电脑以太网 `192.168.2.10`；e1 拔线保持 `LINK_DOWN`。板→电脑不通时优先关 Windows 防火墙再测。

| 图片 | imread | detect | draw | 检出摘要 |
|---|---|---|---|---|
| crazing_10.jpg | 9 ms | **3050 ms** | 31 ms | **无框**（`0 0 0`） |
| scratches_10.jpg | 5 ms | **3027 ms** | 30 ms | 误检 1 框：COCO 类 `5`，置信度仅 **0.42**（非「划痕」语义） |
| inclusion_10.jpg | 7 ms | **3026 ms** | 23 ms | **无框** |

对照：此前 `bus.jpg`（通用场景）能高置信检出；工业图上通用模型基本失效。

> **切片 A 结论**：端侧链路（imread→NCNN→画框）对工业图同样可跑；**缺的是工业缺陷模型**，不是板子跑不动。下一刀做标注/训练/转 NCNN。

---

## 已知限制

- 板端官方例程依赖 RuiChing Studio；本仓库沉淀工具链、适配脚本、文档与日志。
- 当前真机仍是 **通用 YOLOv3**；工业模型适配尚未开始（切片 A 只换图）。
- 固件未编入 `ftp_server`；传文件首选 wget。
- U 盘 `mount … elm` 在本 BSP 上未打通，暂不依赖 U 盘。

## 路线图（更新）

1. **已完成**：串口通 → SMP 1.8.3 → 官方 YOLO + bus.jpg 真机出框（2026-09-25）  
2. **已完成 · 切片 A**：NEU 工业图上板试跑（通用模型漏检/误检，结论成立）  
3. **进行中 · 切片 B**：NEU 子集整理工具 + Ultralytics 训练入口（见 `tools/`）  
4. **其后**：导出 ONNX→NCNN → 上板替换通用模型 → 低代码部署 → 性能报告  
5. **赛前一周**：开源治理、演示脚本、仓库清理  

---

## 2026-09-26 · 切片 B：数据集工具（借用标注，不重复画框）

### 决策

- NEU-DET 仓库内 **已有 YOLO txt 标注**，本切片 **不自研标注 UI**（智标保留给以后自采图）。
- 交付：`tools/prepare_neu_subset.py` 抽样均衡子集 + `tools/train_neu_yolo.py` 训练入口。

### 已完成

| 项 | 结果 |
|---|---|
| 单元测试 | `tests/test_prepare_neu_subset.py` 3 passed |
| 生成子集 | `E:\yolo_files\datasets\neu-det-mini`：train **240**（6×40）+ valid **30** |
| 训练脚本 | `python tools/train_neu_yolo.py`（默认 yolov8n） |

### 你可执行

```text
cd /d F:\projects\ruiching-industrial-vision
python tools\train_neu_yolo.py --epochs 30 --device cpu
```

有 GPU 用 `--device 0`。权重目录：`E:\yolo_files\runs\detect\`。

### 下一刀预告

`best.pt` → ONNX → NCNN（param/bin）→ wget 上板 → 对比切片 A 的漏检。

## 接线备忘（USB-TTL ↔ DEBUG）

| USB-TTL | 板子 DEBUG |
|---|---|
| GND | GND |
| TXD | RX |
| RXD | TX |
| 不接 5V/3V3 | （板子已由 12V 供电） |

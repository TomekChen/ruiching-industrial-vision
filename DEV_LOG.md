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
- 当前真机仍是 **通用 YOLOv3**；工业 `best.pt` 已训好，待转 NCNN 上板。
- 固件未编入 `ftp_server`；传文件首选 wget。
- U 盘 `mount … elm` 在本 BSP 上未打通，暂不依赖 U 盘。

## 路线图（更新）

1. **已完成**：串口通 → SMP 1.8.3 → 官方 YOLO + bus.jpg 真机出框（2026-09-25）  
2. **已完成 · 切片 A**：NEU 工业图上板试跑（通用模型漏检/误检，结论成立）  
3. **已完成 · 切片 B**：NEU 子集 + 速桥云 RTX 5090 训练 30 epoch，`best.pt` 已拉回本地（mAP50≈0.67）  
4. **已完成 · 切片 C**：ONNX/NCNN 导出 + PC 对比切片 A（8 图 17 框）；上板包已打好  
5. **已完成 · 切片 D**：板端 `neu_yolov8_test` 真机三张工业图正确出框  
6. **已完成 · 切片 E**：采图入库 + 智标入口 + 低代码部署清单（网页/CLI）  
7. **已完成 · 切片 F**：性能测试报告（时延/精度/资源，见 `docs/performance-report.md`）  
8. **已完成 · 切片 G**：开源治理（LICENSE/NOTICE/贡献/维护）+ 演示自检与口播稿  
9. **已完成 · 切片 H**：INT8 量化材料 + DeepPCB 第二场景模板  
10. **可选**：真机 INT8 对比数回填、DeepPCB 完整训练上板

---

## 2026-09-28 · 切片 H：INT8 量化 + DeepPCB 模板

### 为什么做

用户确认「两个都要」：量化加速对齐赛题优化项；第二场景证明工具链可复用。

### INT8

| 文件 | 作用 |
|---|---|
| `tools/int8_core.py` / `quantize_neu_int8.py` | 校准列表 + 菜谱 + 可选 ultralytics int8 |
| `docs/int8-optimization.md` | 与板端 /255 对齐的说明 |
| `demos/neu-det-slice-h-int8/` | 使用说明 |
| `E:\yolo_files\exports\neu-int8\` | 本机生成的材料目录 |

```text
python tools\quantize_neu_int8.py
```

有 `ncnn2table/ncnn2bin` 时按 `INT8_RECIPE.txt` 出 int8 权重，再上板对比 FP32≈3550 ms。

### DeepPCB

| 文件 | 作用 |
|---|---|
| `tools/deeppcb_core.py` / `prepare_deeppcb_subset.py` | 原始框 → YOLO 子集 |
| `tools/train_deeppcb_yolo.py` | 训练入口 |
| `board/deeppcb_class_names.snippet.txt` | 板端换类名片段 |
| `demos/deeppcb-slice/README.md` | 全流程说明 |

```text
python tools\prepare_deeppcb_subset.py --src E:\yolo_files\data\DeepPCB
python tools\train_deeppcb_yolo.py --device 0
```

### 自测

```text
python -m pytest tests\test_slice_h.py -q
```

---

## 2026-09-28 · 切片 G：开源治理 + 演示脚本

### 为什么做

大赛总评有 **开源治理 / 长期发展** 权重；提交前还需要「能复述、能自检」的演示路径。

### 交付物

| 文件 | 作用 |
|---|---|
| `LICENSE` / `NOTICE` | Apache-2.0 + 第三方说明 |
| `CONTRIBUTING.md` | 贡献与自检约定 |
| `docs/opensource-governance.md` | 治理、路线图、90 天维护 |
| `tools/demo_smoke.py` | 演示前一键自检 |
| `demos/neu-det-slice-g/DEMO_SCRIPT.md` | 评委口播稿 |

### 怎么用

```text
python tools\demo_smoke.py
```

通过后按口播稿演示低代码页 + 板端 `neu_yolov8_test`。

---

## 2026-09-28 · 切片 F：适配方案与性能测试报告

### 为什么做

赛题四件交付物之一是 **「适配方案与性能测试报告」**。切片 A～D 已有原始数，本切片整理成可提交正文。

### 交付物

| 文件 | 作用 |
|---|---|
| `docs/performance-report.md` | 正式报告（策略 / 时延 / 精度 / 资源） |
| `demos/neu-det-slice-f/summary.json` | 关键数字机器可读摘要 |
| `demos/neu-det-slice-f/README.md` | 切片说明 |

### 核心结论（背诵版）

- 板端工业模型 detect ≈ **3550 ms**；官方通用 ≈ **3030 ms**（约 **+17%**）  
- 语义：漏检/误检 → **scratches / inclusion / patches 正确出框**  
- val mAP50 ≈ **0.67**；NCNN 权重 ≈ **11.5 MB**  
- **不改实时内核**；关闭 Vulkan、`num_threads=2`

### 自测

```text
python -m pytest tests\test_slice_f.py -q
```

## 2026-09-28 · 切片 E：采图 / 标注入口 + 低代码部署

### 为什么做

切片 D 证明「自定义工业模型能上板」。赛题还要：**数据采集与标注工具** + **低代码部署**（全流程 40% + 易用性 15%）。  
本切片用**最小可运行工具**补上，不重造标注 UI（复用智标）。

### 交付物

| 文件 | 作用 |
|---|---|
| `tools/slice_e_core.py` | 建 YOLO 目录、导图、检配对、生成板上清单 |
| `tools/collect_images.py` | CLI 采图 / `--check` / `--howto` |
| `tools/lowcode_deploy.py` | 打包 + `BOARD_CHECKLIST.txt`（可 `--serve`） |
| `tools/lowcode_app.py` | 浏览器点按钮：http://127.0.0.1:8765/ |
| `demos/neu-det-slice-e/README.md` | 使用说明 |

### 怎么用（人话）

```text
python tools\lowcode_app.py
```

打开网页 → 采图入库 → 点智标去画框 → 生成板端命令 → 复制到 msh。

命令行：

```text
python tools\collect_images.py --init --root E:\yolo_files\datasets\my-plant
python tools\lowcode_deploy.py --pc-ip 192.168.2.10
```

板子与电脑须同网段；清单默认写在 `E:\yolo_files\neu_ncnn_board_pack\BOARD_CHECKLIST.txt`。

### 自测

```text
python -m pytest tests\test_slice_e.py -q
```

切片 F 报告已见上文「2026-09-28 · 切片 F」。

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
| 冒烟训练 | 5 epoch / CPU → `E:\yolo_files\runs\neu-det-mini-smoke\weights\best.pt`；val **mAP50≈0.43**（刚起步，可再训 30 epoch） |
| **GPU 正式训练** | 速桥云 RTX 5090 · 30 epoch · yolov8n → `E:\yolo_files\runs\neu-det-mini-gpu\best.pt`；val **mAP50≈0.67**（epoch 20 最佳） |

### GPU 训练（2026-09-26）

- 服务器：`/workspace/apps/ruiching-neu-train/`（数据集 + venv + runs 均在持久盘）
- 编排脚本：`tools/gpu_train_neu.py` / `tools/gpu_fix_train_pull.py`（密码用环境变量 `GPU_SSH_PASS`，勿入库）
- 产物已拉回本地：

| 文件 | 路径 |
|---|---|
| 最佳权重 | `E:\yolo_files\runs\neu-det-mini-gpu\best.pt` |
| 指标 | `E:\yolo_files\runs\neu-det-mini-gpu\results.csv` |
| 训练日志 | `E:\yolo_files\runs\neu-det-mini-gpu\train.log` |

对比切片 A（通用 COCO 模型几乎检不到钢缺陷）→ 自定义 NEU 模型 **mAP50≈0.67**，下一刀转 NCNN 上板。

### 你可执行（正式训练）

```text
cd /d F:\projects\ruiching-industrial-vision
python tools\train_neu_yolo.py --epochs 30 --device cpu --model yolov8n.pt
```

有 GPU 用 `--device 0`。若报 OpenMP 双库错误，脚本已设 `KMP_DUPLICATE_LIB_OK`。

### 下一刀预告

~~`best.pt` → ONNX → NCNN（param/bin）→ wget 上板 → 对比切片 A 的漏检。~~  
→ 见下方「切片 C」。

---

## 2026-09-27 · 切片 C：导出 NCNN + 对比切片 A

### 决策

- 先完成 **PC 可运行信号**（导出 + 同图对比），不硬塞进 `mnet_yolov3_test`（架构不兼容）。
- 板端 YOLOv8 推理命令放到切片 D（改 RuiChing C++）。

### 已完成

| 项 | 结果 |
|---|---|
| 对比推理 | `python tools/compare_slice_a.py` → 8 张图共 **17** 框；见 `demos/neu-det-slice-c/` |
| ONNX | `E:\yolo_files\exports\neu-det-mini-gpu\best.onnx`（~11.6 MB） |
| NCNN | `best_ncnn_model/model.ncnn.param` + `.bin`；PC 上 NCNN 推理 scratches_10 = **6** 框 |
| 上板打包 | `E:\yolo_files\neu_ncnn_board_pack\`（`neu_yolov8n.param/.bin` + 图） |
| 板端说明 | `board/neu_yolov8_ncnn_notes.md`（in0/out0、320、后处理差异） |
| 测试 | `tests/test_slice_c_tools.py` 4 passed |

### 对比摘要（相对切片 A）

| 图 | 切片 A（板上通用） | 切片 C（NEU 模型） |
|---|---|---|
| inclusion_10 | 无检出 | 3× inclusion |
| scratches_10 | 误检 COCO | 6× scratches |
| patches_10 | — | 2× patches |

### 你可执行

```text
cd /d F:\projects\ruiching-industrial-vision
python tools\compare_slice_a.py
python tools\export_neu_ncnn.py
python tools\pack_neu_board.py
```

### 下一刀预告（切片 D）

在 RuiChing Studio 增加 `neu_yolov8_test`，wget `neu_yolov8n.*` 上板，测时延并与切片 A 同图对比。

---

## 2026-09-27 · 切片 D：板端 NEU YOLOv8（分阶段学习日志）

> 目标：让你看懂「每一阶段做了什么」，并留下可学习的本地代码。

### 阶段 0 · 为什么不能直接换 param/bin？

| 对比项 | 旧 `mnet_yolov3_test` | 新 `neu_yolov8_test` |
|---|---|---|
| 模型文件 | `mobilenetv2_yolov3.*` | `neu_yolov8n.*` |
| 输入名 | `data` | `in0` |
| 输出名 | `detection_out`（已解码框） | `out0`（xywh+类分，需 NMS） |
| 输入尺寸 / 归一化 | 352，均值 127.5 | 320，letterbox + /255 |
| 类别 | VOC/COCO | NEU 6 类 |

**结论**：必须新写一个 msh 命令，不能「只换权重文件」。

### 阶段 1 · 弄清 NCNN 输出长什么样（PC 上先验证）

对本导出模型实测：`out0` 形状 **(10, 2100)** = 4 个框参数 (cx,cy,w,h) + 6 类分数；  
2100 = 40²+20²+10²（320 输入下 stride 8/16/32）。  
Ultralytics 导出时已把 DFL 解码融进图里，所以板端 **不必再写 16-bin Softmax**，比官方 ncnn `yolov8.cpp` 更简单。

PC 上用同样解码 + NMS，与 `.pt` 预测对齐（scratches_10 约 5～6 框）。

### 阶段 2 · 写可学习源码（仓库）

新增：

| 文件 | 你读它学什么 |
|---|---|
| `board/applications/neu_yolov8.cpp` | letterbox、推理、解码、NMS、画框、msh 导出（中文注释） |
| `board/README.md` | 仓库代码 vs Studio 工程如何同步 |
| `demos/neu-det-slice-d/README.md` | 编译烧录与上板操作清单 |

关键函数（建议按顺序读）：

1. `letterbox` — 为什么不能直接 resize 成正方形  
2. `detect_neu_yolov8` — `in0`/`out0`、阈值、NMS、坐标还原  
3. `neu_yolov8_test` — 与 `mnet_yolov3_test` 相同的「计时 + imread + detect + draw」骨架  
4. `MSH_CMD_EXPORT` — 命令为何会出现在串口 Tab 里  

### 阶段 3 · 接入本地 RuiChing 工程

已执行：

- 用户实际工程是 **`F:\ruiching-workspace\yolo_183`**（Studio 显示名 yolo_183），不是 `yolo_demo`  
- 已复制 `neu_yolov8.cpp` → `yolo_183\applications\`，并改 OpenCV 头文件（与该工程 `yolov3.cpp` 一致）  
- 已改 `yolo_183\Debug\applications\subdir.mk` 加入编译  

Studio 里需 **右键工程 → Refresh** 后才能在树里看到新文件。

### 阶段 4 · 你需要完成的「可运行信号」（真机）

1. Studio **Build** → 烧录新 `app.img`  
2. `msh` 里 Tab 出 `neu_yolov8_test`  
3. wget `neu_yolov8n.param/.bin`（来自 `E:\yolo_files\neu_ncnn_board_pack\`）  
4. 跑至少：`neu_yolov8_test scratches_10.jpg out_neu_scratches_10.jpg`  
5. 把串口日志回填到下表  

### 真机回填（2026-09-27 · yolo_183 新固件）

工程：`F:\projects\ruiching-workspace\yolo_183`，命令：`neu_yolov8_test`。

| 图片 | detect ms | detections | 备注 |
|---|---|---|---|
| scratches_10.jpg | **3551** | **5× scratches** | conf 最高 0.781；proposals=16 kept=5 |
| inclusion_10.jpg | **3548** | **3× inclusion** | conf 0.753 / 0.620 / 0.578；proposals=23 kept=3 |
| patches_10.jpg | **3552** | **2× patches** | conf 0.895 / 0.843；proposals=17 kept=2 |

串口原文要点：

```text
# scratches
out shape w=2100 h=10 c=1
proposals=16 kept=5
detect end : 3551 ms (ret=0)
5 scratches = 0.781 / 0.614 / 0.389 / 0.286 / 0.277

# inclusion
proposals=23 kept=3
detect end : 3548 ms (ret=0)
1 inclusion = 0.753 / 0.620 / 0.578

# patches
proposals=17 kept=2
detect end : 3552 ms (ret=0)
2 patches = 0.895 / 0.843
execute done, detections=2
```

**对比切片 A**：

| 同图 | 旧 mnet_yolov3 | 新 neu_yolov8 |
|---|---|---|
| scratches_10 | ~3027 ms，误检 COCO 类5 | ~3551 ms，**正确 scratches×5** |
| inclusion_10 | ~3026 ms，**无检出** | ~3548 ms，**正确 inclusion×3** |
| patches_10 | （切片 A 未单记） | ~3552 ms，**正确 patches×2** |

切片 D **闭环完成**：三张工业图均正确出框，detect 约 **3.55 s**，与旧 yolov3 时延同量级，语义从「乱报 COCO」变成「报 NEU 缺陷类」。

**2026-10-16 复测**（重新接线，COM5，`scratches_10.jpg`）：detect **3497 ms**，仍为 **5× scratches**（0.781 / 0.614 / 0.389 / 0.286 / 0.277），与 09-27 结果一致。

**2026-10-16 DeepPCB 上板**（`12100008_test.jpg`）：重烧含 PCB 类名的固件后，detect **3551 ms**，`kept=5`。串口类别名正确：**copper×2**（0.708/0.675）、**spur×2**（0.490/0.282）、**mousebite×1**（0.276）。第二场景闭环。

**INT8 上板对比**（同一张 `12100008_test.jpg`，2026-10-17）：

| 版本 | 权重大小 | detect | 检出 |
|---|---|---|---|
| FP32 | 12.0 MB | **3551 ms** | 5 框：copper×2、spur×2、mousebite×1 |
| INT8 | **3.07 MB** | **1395 ms** | 2 框：copper×2（0.320 / 0.292） |

时延约降到原来的 **39%**（快约 2.5 倍），体积约 **1/4**。置信度较低的 spur、mousebite 在 INT8 下消失，精度有损失。FP32 备份：`neu_yolov8n_fp32.param/.bin`。

### 阶段 5 · 若编译/运行翻车时怎么查

| 现象 | 可能原因 |
|---|---|
| 工程里没有 neu_yolov8.cpp | 未 Refresh；重新 copy；检查 subdir.mk |
| 找不到命令 | 未烧录新固件；或 `MSH_CMD_EXPORT` 未链进 |
| load_param failed | `/data` 下文件名必须是 `neu_yolov8n.param` |
| out.h 不对 | 传错了旧 yolov3 权重 |
| OOM / 很慢 | 保持源码里 `use_vulkan_compute=false` |

## 本地操作手册（不翻聊天记录）

已整理到：

```text
E:\yolo_files\操作手册.md
```

内容包括：Studio 打开/编译、烧录 app.img、串口 msh、关防火墙、wget 传文件、`neu_yolov8_test` / `mnet_yolov3_test`、路径一览。

## 接线备忘（USB-TTL ↔ DEBUG）

| USB-TTL | 板子 DEBUG |
|---|---|
| GND | GND |
| TXD | RX |
| RXD | TX |
| 不接 5V/3V3 | （板子已由 12V 供电） |

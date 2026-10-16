# 睿擎工业视觉轻量化适配工具链

> 仓库：https://github.com/TomekChen/ruiching-industrial-vision  
> 2026 上海开源软件应用创新大赛 · AI+工业软件赛道  
> 赛题：基于睿擎工业开发平台的预训练视觉模型轻量化适配与低代码部署优化

## 项目目标（人话）

在睿擎派 RC-Pi-3506 上，补齐「采图 → 标注 → 自定义模型适配 → 一键部署」这条工业视觉工具链，并交付可复现的缺陷检测 Demo。

## 硬件与环境

| 项目 | 说明 |
|---|---|
| 开发板 | 睿擎派 RC-Pi-3506（512MB + 8GB EMMC） |
| IDE | RuiChing Studio（本机 `D:\RuiChingStudio`） |
| SDK | `RuiChing_RC-Pi-3506_APP_1.8.3` |
| 截止 | 2026-10-11 |

## 仓库结构（规划）

```
├── README.md                 # 本说明书
├── DEV_LOG.md                # 开发日志（比赛提交必看）
├── docs/                     # 方案、测试报告、开源治理说明
├── tools/                    # PC 侧：采集 / 标注 / 模型转换 / 低代码部署
├── board/                    # 板端应用与部署脚本（基于睿擎 SDK）
├── demos/                    # 可复现 Demo 与样例数据说明
├── tests/                    # 测试
└── LICENSE                   # 开源许可证
```

## 当前进度（2026-09-28 · 切片 G）

| 里程碑 | 状态 |
|---|---|
| 板子 SMP 1.8.3 + `msh` | ✅ |
| 官方 NCNN YOLOv3 真机出框 | ✅ |
| 切片 A：NEU 工业图上板（通用模型） | ✅ 漏检/误检 |
| 切片 B：GPU 训练 NEU yolov8n | ✅ mAP50≈0.67 |
| 切片 C：ONNX/NCNN + PC 对比 | ✅ 8 图 17 框 |
| 切片 D：板端 `neu_yolov8_test` | ✅ 真机闭环：scratches×5 / inclusion×3 / patches×2（均 ~3550 ms） |
| 切片 E：采图+标注入口+低代码部署 | ✅ `lowcode_app.py` / `collect_images` / `lowcode_deploy` |
| 切片 F：性能测试报告 | ✅ [`docs/performance-report.md`](./docs/performance-report.md) |
| 切片 G：开源治理 + 演示脚本 | ✅ `LICENSE` / `demo_smoke.py` / 口播稿 |
| 切片 H：INT8 + DeepPCB 模板 | ✅ `quantize_neu_int8` / `prepare_deeppcb_subset` |

### 演示前一键自检

```text
python tools\demo_smoke.py
```

口播稿：[demos/neu-det-slice-g/DEMO_SCRIPT.md](./demos/neu-det-slice-g/DEMO_SCRIPT.md)

### 切片 D 你要做的（编译烧录）

完整步骤：[demos/neu-det-slice-d/README.md](./demos/neu-det-slice-d/README.md)

```text
1. 打开 RuiChing Studio → yolo_demo → Build
2. 烧录 app.img
3. wget neu_yolov8n.param/.bin + 工业图到 /data
4. neu_yolov8_test scratches_10.jpg out.jpg
5. 把串口输出贴回 DEV_LOG「真机回填」
```

学习源码：`board/applications/neu_yolov8.cpp`（中文注释说明与 yolov3 的 5 点差异）


## 快速开始（低代码 · 切片 E）

```text
cd /d F:\projects\ruiching-industrial-vision
python tools\lowcode_app.py
```

浏览器打开 http://127.0.0.1:8765/ ：采图 → 标注入口 → 生成板上命令。  
详解：[demos/neu-det-slice-e/README.md](./demos/neu-det-slice-e/README.md)

## 快速开始（板端已验证）

1. 烧录 YOLO app（RuiChing Studio 编译的 `app.img`）到 EMMC。  
2. 串口 115200 进入 `msh`。  
3. 电脑与板子同网段，PC 执行 `python -m http.server 8000`，板子：

```text
cd /data
wget http://<电脑IP>:8000/mobilenetv2_yolov3.param mobilenetv2_yolov3.param
wget http://<电脑IP>:8000/mobilenetv2_yolov3.bin mobilenetv2_yolov3.bin
wget http://<电脑IP>:8000/你的图.jpg 你的图.jpg
mnet_yolov3_test 你的图.jpg out.jpg
```

工业场景图推荐：**NEU-DET**（钢表面）或 **DeepPCB**（PCB），下载链接写在 `DEV_LOG.md`。

## 模型文件（百度网盘）

训练权重和板上用的模型体积较大，不放进 Git 仓库。压缩包名：`ruiching-industrial-vision-models.zip`。

链接：https://pan.baidu.com/s/1ZzfWyuDE7j0uQknylUKXWw?pwd=bqah  
提取码：`bqah`

| 文件 | 干什么用 |
|---|---|
| `neu-steel/best.pt` | 钢表面缺陷的训练结果。在电脑上继续训练、导出时用它 |
| `neu-steel/neu_yolov8n.param` | 钢表面模型的网络结构。和下面的 `.bin` 一起拷到板子 `/data` |
| `neu-steel/neu_yolov8n.bin` | 钢表面模型的权重。板子命令 `neu_yolov8_test` 读取这一对文件，约 12 MB，已真机检出划痕、夹杂、斑块 |
| `deeppcb/best.pt` | PCB 缺陷的训练结果。在电脑上继续训练、导出时用它 |
| `deeppcb/neu_yolov8n_fp32.param` | PCB 模型的网络结构（未量化）。上板前改名为 `neu_yolov8n.param` |
| `deeppcb/neu_yolov8n_fp32.bin` | PCB 模型的权重（未量化）。上板前改名为 `neu_yolov8n.bin`。约 12 MB，同一张图约 3551 ms，检出伪铜、毛刺、鼠咬 |
| `deeppcb/neu_yolov8n_int8.param` | PCB 模型量化后的网络结构。上板前同样改名为 `neu_yolov8n.param` |
| `deeppcb/neu_yolov8n_int8.bin` | PCB 模型量化后的权重。约 3.1 MB，同一张图约 1395 ms，更快，但只稳定留下伪铜，毛刺和鼠咬会漏 |

板子上的程序固定读取 `/data/neu_yolov8n.param` 和 `/data/neu_yolov8n.bin`。换场景时覆盖这两个文件名即可，不用改命令。PCB 模型还要把固件里的类别名换成 `open`、`short`、`mousebite`、`spur`、`copper`、`pin-hole` 后再烧录。

## 许可证

本仓库代码：**Apache-2.0**（见 [`LICENSE`](./LICENSE)）。  
第三方与数据说明：[`NOTICE`](./NOTICE)。  
开源治理与维护：[`docs/opensource-governance.md`](./docs/opensource-governance.md)。  
贡献方式：[`CONTRIBUTING.md`](./CONTRIBUTING.md)。

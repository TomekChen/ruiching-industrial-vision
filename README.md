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

## 当前进度

见 [DEV_LOG.md](./DEV_LOG.md)。

## 快速开始

（板端例程与 PC 工具就绪后，在此补充启动步骤。）

## 许可证

拟定 Apache-2.0（与 RT-Thread / 睿擎生态常见许可对齐，最终以仓库 LICENSE 为准）。

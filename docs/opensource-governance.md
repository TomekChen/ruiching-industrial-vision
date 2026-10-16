# 开源治理与长期维护说明

> 对应大赛总评「开源治理 / 长期发展」。  
> 日期：2026-09-28 · 切片 G

## 1. 治理目标

让评审与后来者能回答三件事：

1. **能不能合法使用/二次开发？** → `LICENSE` + `NOTICE`  
2. **怎么参与？** → `CONTRIBUTING.md`  
3. **项目会往哪走、谁维护？** → 本文路线图与维护计划  

## 2. 许可与合规

| 项 | 约定 |
|---|---|
| 本仓库代码 | Apache-2.0 |
| 第三方依赖 | 见根目录 `NOTICE`，不宣称「整仓仅一种许可」 |
| 数据集 | NEU-DET 等仅作 Demo/训练素材，再分发需遵守数据方条款 |
| 密钥 | 禁止入库；训练机密码用环境变量 |

与睿擎 / RT-Thread 生态常见做法对齐：**应用层开源，不绑死内核修改**。

## 3. 仓库结构职责

| 目录 | 维护责任 |
|---|---|
| `tools/` | PC 工具链（采图、导出、低代码） |
| `board/` | 板端适配源码与说明（拷入 Studio 工程） |
| `demos/` | 可复现切片说明与摘要 JSON |
| `docs/` | 方案、报告、治理 |
| `tests/` | 无 GPU 冒烟，CI/本地提交前必跑 |
| `DEV_LOG.md` | 过程真相源（比赛材料） |

## 4. 发布与版本

- 主分支保持「可克隆 → 能跑通文档中的最小路径」  
- 比赛节点打 tag 建议：`v0.1-slice-d-board`、`v0.2-slice-e-lowcode`、`v0.3-report`  
- 大文件（权重 `.bin` / `.pt`）默认放本机 `E:\yolo_files\`，仓库只留脚本与小样例图说明  

## 5. 路线图（长期发展）

| 阶段 | 内容 | 状态 |
|---|---|---|
| M1 | 板端工业模型闭环（切片 A～D） | ✅ |
| M2 | 低代码采图/部署 + 性能报告（E～F） | ✅ |
| M3 | 开源治理与演示脚本（本切片 G） | ✅ |
| M4 | INT8 / 更短时延（材料与菜谱） | ✅ 切片 H；真机对比数可选回填 |
| M5 | 产线队列推理、结果上报（可选） | 规划 |
| M6 | 第二场景 DeepPCB 模板复用 | ✅ 切片 H |

## 6. 维护计划（赛后 90 天）

| 频率 | 动作 |
|---|---|
| 每次合并 | `python -m pytest tests -q` + `python tools/demo_smoke.py` |
| 每月 | 核对睿擎 SDK / Ultralytics 大版本是否破坏导出 |
| 每季 | 更新 `NOTICE` 与性能数字（若有新板测） |
| 持续 | Issue 优先修「文档与真机不一致」类问题 |

维护联系人以 GitHub 仓库 Issues 为准：  
https://github.com/TomekChen/ruiching-industrial-vision

## 7. 演示与复现入口

- 一键自检：`python tools/demo_smoke.py`  
- 演示口播稿：`demos/neu-det-slice-g/DEMO_SCRIPT.md`  
- 低代码页：`python tools/lowcode_app.py`  
- 性能报告：`docs/performance-report.md`

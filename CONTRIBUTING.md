# 贡献指南（CONTRIBUTING）

欢迎提交 Issue / PR。本项目面向比赛与工业 Demo，优先「能跑、可复现、文档清楚」。

## 开始前

1. 读 [`README.md`](./README.md) 与 [`DEV_LOG.md`](./DEV_LOG.md)  
2. 板子相关先看 [`docs/hardware-setup.md`](./docs/hardware-setup.md)  
3. 性能数字以 [`docs/performance-report.md`](./docs/performance-report.md) 为准  

## 开发约定

- **垂直小切片**：一次只做一个可演示的小目标（采图 / 导出 / 板端命令 / 文档）  
- **可运行信号**：改工具脚本时尽量补 `tests/` 里不依赖 GPU 的用例  
- **中文优先**：用户可见说明、`DEV_LOG` 用通俗中文  
- **密钥不上库**：SSH 密码、Token 只用环境变量  

## 提 PR 前自检

```text
cd /d F:\projects\ruiching-industrial-vision
python -m pytest tests -q
python tools\demo_smoke.py
```

说明改动「为什么」，而不是只列文件名。

## 行为准则（简版）

友善、就事论事；不提交恶意代码；尊重第三方许可（见 `NOTICE`）。

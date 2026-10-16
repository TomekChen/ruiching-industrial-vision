# 切片 F：性能测试报告

赛题交付物之一：**适配方案与性能测试报告**。

- 正式报告（给人看）：[`docs/performance-report.md`](../../docs/performance-report.md)  
- 机器可读摘要：[`summary.json`](./summary.json)

## 核心数字（背给评委）

| 项 | 数值 |
|---|---|
| 工业模型板端 detect | ≈ **3550 ms** |
| 官方通用模型板端 detect | ≈ **3030 ms** |
| 时延变化 | 约 **+17%** |
| 语义 | 通用：漏检/误检 → 工业：**scratches/inclusion/patches 正确** |
| 验证集 mAP50 | ≈ **0.67** |
| 权重 | NCNN bin ≈ **11.5 MB** |

## 成功标准

1. `docs/performance-report.md` 含策略 / 时延 / 精度 / 资源四块  
2. 数字与 DEV_LOG、切片 C/D 回填一致  
3. 明确「不改实时内核」与后续量化方向  

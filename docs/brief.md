# 赛题摘要与交付清单

## 一句话目标

依托睿擎高实时工业平台，补齐工业视觉「采集 → 标注 → 自定义预训练模型适配 → 端侧低代码部署」工具链，并交付可复现的工件缺陷检测 Demo。

## 必须交付

1. 工业数据采集与标注工具 → 切片 E（`collect_images` / 低代码页 + 智标入口）  
2. 自定义模型低代码部署工具 → 切片 E（`lowcode_deploy` / `lowcode_app`）  
3. 适配方案与性能测试报告 → 切片 F（`docs/performance-report.md`）  
4. 可运行 Demo 工程 → 切片 A～D（`neu_yolov8_test` 真机）  

附加（总评开源治理）：切片 G（`LICENSE` / `NOTICE` / `docs/opensource-governance.md` / 演示脚本）

## 明确先不做

- 自研完整训练框架  
- 复杂多人在线协作标注平台  
- 与赛题无关的工业总线深度集成（CAN/RS485 后期可选）  

# 评委演示口播稿（切片 G）

> 目标：5～8 分钟讲清「痛点 → 工具链 → 真机结果 → 开源」。  
> 演示前先跑：`python tools/demo_smoke.py`

## 开场（30 秒）

「睿擎平台本来就能跑 NCNN 和官方 YOLOv3，但工业产线要的是**自己的缺陷类别**。  
我们不改实时内核，补上采图标注入口、自定义模型适配、低代码部署，并在 RC-Pi-3506 真机跑通钢表面缺陷检测。」

## 痛点（40 秒）

1. 现场图不好管  
2. 标注不好接训练格式  
3. 官方只认通用检测，换工业模型难  
4. 部署靠手写命令，门槛高  

## 工具链演示（2 分钟）

1. 打开低代码页：`python tools/lowcode_app.py`  
2. 点「生成板端命令」，展示 `BOARD_CHECKLIST.txt`  
3. 说明标注走智标，导出 YOLO txt，用 `collect_images --check` 校验  

## 真机结果（2 分钟）

串口（先 `Ctrl+C` 清行）：

```text
neu_yolov8_test scratches_10.jpg out_neu_scratches_10.jpg
```

口播数字：

- 工业模型约 **3550 ms**，官方通用约 **3030 ms**（大约 +17%）  
- 语义：误检 COCO → **5 个 scratches**；inclusion / patches 同样正确  
- 验证集 mAP50 ≈ **0.67**；权重约 **11.5 MB**  

## 开源治理（40 秒）

- 许可：Apache-2.0（`LICENSE`）+ 第三方清单（`NOTICE`）  
- 贡献：`CONTRIBUTING.md`  
- 维护与路线图：`docs/opensource-governance.md`  

## 收尾（20 秒）

「交付四件套都在仓库：采图标注入口、低代码部署、性能测试报告、可复现 Demo。  
下一步可做量化加速和第二场景模板，主链路已经闭环。」

## 应急

| 状况 | 处理 |
|---|---|
| 板子没带 / 没电 | 播预录串口日志 + `docs/performance-report.md` |
| 串口残留乱码 | `Ctrl+C` → `Enter` 再输入 |
| 网页起不来 | `python tools/lowcode_deploy.py --pc-ip 192.168.2.10` |

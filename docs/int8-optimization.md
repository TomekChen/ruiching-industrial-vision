# NCNN INT8 优化说明

> 切片 H · 配套 `tools/quantize_neu_int8.py`  
> 真机主路径仍为 FP32（~3550 ms）；INT8 为加速选项。

## 为何做 INT8

| 目标 | 说明 |
|---|---|
| 降算力 | 卷积用 int8 累加，CPU 上常有收益 |
| 降体积 | 权重量级可接近 1/4（视层而定） |
| 赛题对齐 | 「量化 / 精度损耗可控」 |

## 与板端预处理对齐

板端 `neu_yolov8.cpp`：`RGB`、letterbox 320、像素 **/255**。  
校准 `ncnn2table` 时使用：

- `mean=[0,0,0]`  
- `norm=[1/255,1/255,1/255]` ≈ `0.00392157`  
- `pixel=RGB`，`shape=[320,320,3]`

## 推荐流程

1. `python tools/quantize_neu_int8.py` 生成校准列表与菜谱  
2. 安装 ncnn 工具链，执行 `INT8_RECIPE.txt`  
3. 上板同图对比 FP32 vs INT8 的 detect ms 与框数  
4. 若掉点明显：增加校准图、换 KL/ACQ 方法、或仅部分层量化  

## Ultralytics 路径

```text
python tools/quantize_neu_int8.py --try-ultralytics
```

依赖 `data.yaml` 做校准；失败时回退到 ncnn2table 菜谱。

## 记录模板（贴进 DEV_LOG）

```text
图: scratches_10.jpg
FP32 detect: 3551 ms, kept=5
INT8 detect: ? ms, kept=?
备注: …
```

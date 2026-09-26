# 切片 A：NEU-DET 工业图上板试跑

**目标**：用钢表面缺陷图替换 `bus.jpg`，在睿擎板上跑现有通用 NCNN YOLO，留下「通用模型对工业场景不够」的对比素材。

**不包含**：训练、自定义模型、标注工具（后续切片）。

## 本目录文件

| 路径 | 说明 |
|---|---|
| `images/` | 已挑选的 8 张 NEU 图（6 类各至少 1 张） |
| `MANIFEST.md` | 文件清单与类别 |

电脑侧同步副本（方便 `python -m http.server`）：`E:\yolo_files\neu_board_pack\`

## 类别（NEU-DET 官方 6 类）

`crazing` 龟裂 · `inclusion` 夹杂 · `patches` 斑块 · `pitted_surface` 点蚀 · `rolled-in_scale` 氧化皮压入 · `scratches` 划痕

## 板端操作（约 10 分钟）

### 0. 上电与确认

1. 插 12V 电源、USB-TTL（DEBUG）、网线（与电脑同网段）  
2. 串口 115200，出现 `msh />`  
3. 确认 YOLO 还在：`mnet` 后按 Tab，应有 `mnet_yolov3_test`  
4. 确认模型还在（关机一般不丢 `/data`）：

```text
ls /data
```

应仍有 `mobilenetv2_yolov3.param`、`.bin`。若没有，按 README 根目录「快速开始」用 wget 再传一次模型。

### 1. 电脑开文件服务

```text
cd /d E:\yolo_files\neu_board_pack
python -m http.server 8000
```

查电脑 IP（例如 `192.168.0.12`），并确认能 `ping` 通板子。

### 2. 板子下载工业图

把下面的 `电脑IP` 换成你的：

```text
cd /data
wget http://电脑IP:8000/crazing_10.jpg crazing_10.jpg
wget http://电脑IP:8000/inclusion_10.jpg inclusion_10.jpg
wget http://电脑IP:8000/patches_10.jpg patches_10.jpg
wget http://电脑IP:8000/pitted_surface_10.jpg pitted_surface_10.jpg
wget http://电脑IP:8000/rolled-in_scale_10.jpg rolled-in_scale_10.jpg
wget http://电脑IP:8000/scratches_10.jpg scratches_10.jpg
wget http://电脑IP:8000/scratches_50.jpg scratches_50.jpg
wget http://电脑IP:8000/inclusion_50.jpg inclusion_50.jpg
ls /data
```

### 3. 逐张推理（至少跑 3 张，建议 8 张都跑）

```text
cd /data
mnet_yolov3_test crazing_10.jpg out_crazing_10.jpg
mnet_yolov3_test inclusion_10.jpg out_inclusion_10.jpg
mnet_yolov3_test patches_10.jpg out_patches_10.jpg
mnet_yolov3_test scratches_10.jpg out_scratches_10.jpg
```

把串口完整输出复制保存（或拍照）。关注：

- 是否 `execute done`
- 检出的类别 ID / 置信度（通用 COCO 模型很可能乱检或几乎检不出钢缺陷）
- 推理耗时（`detect_yolov3 end : xxx ms`）

### 4. 回填结果

把输出贴给助手，或自己记到 `DEV_LOG.md`「切片 A 实测」表格。  
**成功标准**：工业图能在板上跑通 + 留下「通用模型不适配」的证据（漏检/错检），不是要求检出正确缺陷类。

## 预期结论（写报告用）

官方 MobileNetV2-YOLOv3 是 **COCO 通用目标**（人、车、公交…），**没有**钢表面 6 类缺陷。  
因此本切片预期：链路通、时延可测，但**语义上对不上工业缺陷** → 证明必须做「自定义工业模型适配」（赛题核心）。

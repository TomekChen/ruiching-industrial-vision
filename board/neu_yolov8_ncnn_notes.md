# 板端接入 YOLOv8-NCNN 备注

配合源码：`board/applications/neu_yolov8.cpp`  
操作手册：`demos/neu-det-slice-d/README.md`

## 模型文件（`E:\yolo_files\neu_ncnn_board_pack\`）

| 文件 | 说明 |
|---|---|
| `neu_yolov8n.param` | 网络结构 |
| `neu_yolov8n.bin` | 权重（约 11.5 MB） |
| `names.txt` | 0..5 → NEU 6 类 |

## 与 YOLOv3 示例的差异

| 项 | MobileNetV2-YOLOv3（现有） | NEU YOLOv8n（本导出） |
|---|---|---|
| load_param | `mobilenetv2_yolov3.param` | `neu_yolov8n.param` |
| 输入名 | `data` | `in0` |
| 输出名 | `detection_out` | `out0` |
| 输入边长 | 352 | **320** |
| 均值/归一化 | 127.5 / 1/127.5 | letterbox + **RGB /255** |
| 输出形状 | 已解码行 | **(10, 2100)** = xywh + 6 类分（图内已含 DFL） |
| 板端后处理 | 几乎不用 | 阈值 + NMS + 去 letterbox |
| 类别 | VOC/COCO | NEU 6 类 |
| msh 命令 | `mnet_yolov3_test` | `neu_yolov8_test` |

## 实现路径（已完成源码部分）

1. ✅ 仓库写好 `neu_yolov8.cpp`（含中文学习注释）  
2. ✅ 复制进 `yolo_demo/applications/`，subdir.mk 已登记  
3. ⏳ Studio Build → 烧录  
4. ⏳ wget 模型 → 真机跑切片 A 同图  

板上内存紧：源码默认 `use_vulkan_compute=false`，`num_threads=2`。

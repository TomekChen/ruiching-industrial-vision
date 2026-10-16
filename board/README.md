# 板端代码（睿擎 / RT-Thread）

本目录放**可学习、可版本管理**的板端源码。真正编译仍在 RuiChing Studio 工程里。

## 文件

| 文件 | 说明 |
|---|---|
| `applications/neu_yolov8.cpp` | 切片 D：NEU YOLOv8n NCNN 推理 + msh 命令 `neu_yolov8_test` |
| `neu_yolov8_ncnn_notes.md` | 与旧 `yolov3.cpp` 的差异对照表 |

## 学习路径（按 DEV_LOG 阶段走）

1. 先读 `yolo_demo/applications/yolov3.cpp`（官方例程，已能跑 bus.jpg）  
2. 再读本目录 `neu_yolov8.cpp` 顶部注释：5 点差异  
3. 对照 `demos/neu-det-slice-d/README.md` 完成编译/烧录/上板  

## 同步到 Studio

```text
copy /Y board\applications\neu_yolov8.cpp D:\RuiChingStudio\workspace\yolo_demo\applications\neu_yolov8.cpp
```

然后在 Studio 里 Build → 烧录 `app.img`。

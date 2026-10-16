# 切片 H-2：DeepPCB 第二工业场景模板

主 Demo 仍是 **NEU 钢表面**。本切片把同一套工具链复用到 **PCB 缺陷（DeepPCB）**。

## 6 类

| id | 名称 | 含义 |
|---|---|---|
| 0 | open | 开路 |
| 1 | short | 短路 |
| 2 | mousebite | 鼠咬 |
| 3 | spur | 毛刺 |
| 4 | copper | 伪铜 / spurious copper |
| 5 | pin-hole | 针孔 |

原始标注：`x1,y1,x2,y2,type`（type=1..6）→ 本工具转为 YOLO `cls cx cy w h`。

## 下载数据

- GitHub：https://github.com/tangsanli5201/DeepPCB  
- 交大页：http://www.pami.sjtu.edu.cn/Show/56/77  

解压到例如：`E:\yolo_files\data\DeepPCB\`（目录里能搜到 `*_test.jpg`）。

## 转子集 + 训练

```text
python tools\prepare_deeppcb_subset.py --src E:\yolo_files\data\DeepPCB
python tools\train_deeppcb_yolo.py --device 0
```

CPU 冒烟可：`--device cpu --epochs 3`。

## 导出上板（与 NEU 相同）

```text
python tools\export_neu_ncnn.py --weights E:\yolo_files\runs\deeppcb-mini\weights\best.pt --out-dir E:\yolo_files\exports\deeppcb-mini
python tools\pack_neu_board.py --ncnn-dir E:\yolo_files\exports\deeppcb-mini\best_ncnn_model --out E:\yolo_files\deeppcb_ncnn_board_pack
```

## 板端换类名（必做）

`neu_yolov8.cpp` 里 `kClassNames[]` 默认是 NEU 六类。换 DeepPCB 权重时，改成：

```cpp
static const char *kClassNames[] = {
    "open", "short", "mousebite", "spur", "copper", "pin-hole"
};
```

或直接拷贝子集里的 `BOARD_CLASS_NAMES.txt` 对照修改。  
`kNumClass` 仍为 6。改完重新编译烧录。

## 成功标准

1. `prepare_deeppcb_subset` 生成 `data.yaml` + train/valid  
2. 单元测试：`tests/test_slice_h.py` 通过（不依赖完整下载）  
3. 文档说明与 NEU 路径平行，评委能看懂「第二场景可复用」  

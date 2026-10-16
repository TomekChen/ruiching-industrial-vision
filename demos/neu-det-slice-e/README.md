# 切片 E：采图 / 标注入口 + 低代码部署

> 目标：补齐赛题「全流程工具」前半与「低代码部署」——普通人不用翻聊天记录也能走通。

## 你已经有的（A～D）

训练好的工业模型 + 板端 `neu_yolov8_test` 真机出框。

## 本切片交付

| 工具 | 作用 |
|---|---|
| `tools/slice_e_core.py` | 核心逻辑（建目录、导图、检标注、生成板上清单） |
| `tools/collect_images.py` | 命令行：采图入库 + 标注校验 |
| `tools/lowcode_deploy.py` | 命令行：打包 + 写出 `BOARD_CHECKLIST.txt` |
| `tools/lowcode_app.py` | **浏览器低代码页**（点按钮） |

## 三步用法（推荐网页）

```text
cd /d F:\projects\ruiching-industrial-vision
python tools\lowcode_app.py
```

浏览器打开：http://127.0.0.1:8765/

1. **采图入库**：创建骨架 / 导入现场图  
2. **在线标注**：点开智标，导出 YOLO txt 到 `train/labels`  
3. **部署清单**：打包（复用已有 NCNN）→ 生成板端 `wget` + `neu_yolov8_test` 命令  

把清单里的命令贴到板子 `msh` 即可（串口乱码时先 `Ctrl+C` 再 `Enter`）。

## 命令行等价操作

```text
:: 1) 采图
python tools\collect_images.py --init --root E:\yolo_files\datasets\my-plant
python tools\collect_images.py --import-from D:\photos\line1 --root E:\yolo_files\datasets\my-plant
python tools\collect_images.py --howto --root E:\yolo_files\datasets\my-plant
python tools\collect_images.py --check --root E:\yolo_files\datasets\my-plant

:: 2) 部署（默认不重新导出；需要重导加 --export）
python tools\lowcode_deploy.py
python tools\lowcode_deploy.py --serve
```

清单输出：`E:\yolo_files\neu_ncnn_board_pack\BOARD_CHECKLIST.txt`

## 成功标准

1. 网页或 CLI 能创建数据集目录 + `data.yaml`  
2. `--check` 能发现缺标注  
3. 能生成含 `neu_yolov8n.param` wget 与 `neu_yolov8_test` 的清单  
4. 自测：`python -m pytest tests\test_slice_e.py -q`

## 和赛题交付的对应

| 赛题要求 | 本切片 |
|---|---|
| 工业数据采集与规整 | `collect_images` / 网页「采图入库」 |
| 在线标注 | 智标入口 + YOLO 目录约定 + `--check` |
| 低代码部署 | `lowcode_deploy` / 网页「生成板端命令」 |
| 自定义模型适配 | 复用切片 C/D 的导出与 `neu_yolov8_test` |

下一刀（切片 F）：把 A/C/D 实测整理成正式《性能测试报告》。

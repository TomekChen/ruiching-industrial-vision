# 硬件接线与首次上电

## 套件

- 睿擎派 RC-Pi-3506（512MB + 8GB EMMC）
- 12V 电源
- USB TO TTL 串口模块 + 杜邦线
- （可选）JLINK 转接板 —— 前期不用

## 首次看日志

1. USB-TTL：GND↔GND，TXD↔RX，RXD↔TX（不接 5V/3V3）
2. USB 插入电脑，设备管理器确认 COMx
3. 串口工具：115200 8N1 无流控，打开端口
4. 板子 12V 供电或按 RESET
5. 看到启动日志即成功

## 刷机提示

本板为 **EMMC** 版本，使用网盘中 `Firmware_EMMC_*_V1.8.3.img`；不要用 NAND 固件。

# ESP32-S3 health monitor (reference firmware)

这个固件是可选的健康监控模块：读取 NTC 温度、风扇转速，控制 PWM 风扇，并把 JSON POST 到具身数据驿的 `/api/telemetry`。

它**不参与数据路径**；固件掉线不影响采集、质检、分层与交付。

## 接线

| ESP32-S3 | 连接 |
|---|---|
| GPIO5 | 4-pin 风扇 PWM |
| GPIO4 | 风扇 TACH（内部上拉） |
| GPIO1 | NTC 10k 分压中点（NTC 接 3.3V，10k 接 GND） |
| 5V / GND | USB 5V（来自小主机/UPS） |

详见 [../WIRING.md](../WIRING.md)。

## 构建

```bash
cd hardware/firmware
cp include/secrets.h.example include/secrets.h
# 编辑 include/secrets.h：WiFi SSID/密码、服务器地址
pio run -t upload
pio device monitor
```

没有 PlatformIO 时，可用 Arduino IDE：选择 ESP32-S3 DevKitC-1，安装 ESP32 core，打开 `src/main.cpp`，把 `secrets.h.example` 复制为 `secrets.h`。

## API 契约

POST `/api/telemetry`：

```json
{
  "temperature_c": 42.5,
  "fan_rpm": 1200,
  "fan_duty": 160,
  "rssi": -55,
  "uptime_s": 12345
}
```

Dashboard 会显示 `temperature_c`、`fan_rpm`、`power_w`（如果提供）。当前固件不测功率；如需功率，可加 INA226 并在 JSON 中增加 `power_w`。

## 安全

- 不要把 `secrets.h` 提交到仓库（已在 `.gitignore`）。
- 不要把 12V 接到 ESP32。
- 风扇 PWM 是 3.3V 信号；确认风扇兼容。
- 固件只读传感器、控制风扇、发 HTTP；不执行任何远程命令。

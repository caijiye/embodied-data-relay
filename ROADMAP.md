# Roadmap

## v0.1 — Competition MVP（2026-10）

- 单机边缘节点：会话发现、质量门禁、H.264 减量、hot/cold 分层、local/S3 交付。
- 合成多相机数据 + 缺陷注入；baseline vs pipeline benchmark。
- Dashboard：吞吐、减量、质量分布、分层、交付延迟。
- 开源治理：Apache-2.0 / CERN-OHL-S-2.0、BOM、接线、外壳、CI。

## v0.2 — Real-data pilot（2026-11 → 2026-12）

- 接入真实 rosbag2/MCAP 会话与 2-4 路相机；发布实测 benchmark。
- LeRobotDataset v3 exporter（Parquet + MP4 + meta）。
- 会话级 append-only 写入日志；UPS/掉电恢复测试。
- ESP32-S3 健康监控：温度、风扇、电流；OLED 本地状态页。
- 交付：带宽限速、优先级队列、断点续传校验。
- 文档：真实数据 pilot 报告、部署手册、故障排查。

## v0.3 — Multi-node & cartridge（2027 Q1）

- 多节点注册、集中索引、跨站点交付调度。
- 「数据胶囊」：可热插拔 NVMe 载体 + dock，物理寄送替代慢速上行。
- RBAC、审计日志、租户隔离。
- 2.5GbE/10GbE 实测；ZNS/SLC SSD 写入缓冲适配。

## v1.0 — Production（2027 Q2）

- 生产级安装包、升级/回滚、监控告警。
- 与主流具身数据平台/训练框架的格式适配。
- 硬件套件（open BOM）与商业支持。

## 非目标

- 不做机器人本体、不做数据标注众包平台。
- 不做通用 NAS/超融合；只解决具身数据采集现场的减量、分层与交付。
- 不在 MVP 阶段做自动删除；所有删除必须人工确认并可审计。

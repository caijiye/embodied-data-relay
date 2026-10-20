# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes (competition MVP) |

## Reporting a vulnerability

请不要在公开 issue 中披露安全问题。使用 GitHub 的 **Private vulnerability reporting / Security advisory** 功能联系维护者，或通过仓库维护者的 GitHub 主页找到私下联系方式。

我们会在 72 小时内确认收到，并在 7 天内给出初步评估。修复前请不要公开利用细节。

## Scope

重点关注：

- 路径穿越：`/api/episodes/{id}/file/{filename}` 必须限制在 package 目录内。
- 任意文件写入/删除：质量门禁与分层只允许在配置的目录内操作。
- 交付凭证泄漏：S3 access key / secret 不得写入仓库、日志或 dashboard。
- 不可信输入：MCAP/视频/图像解析、文件名、meta.json、telemetry POST。
- 供应链：新增依赖的许可证与来源；CI 不执行外部下载的脚本。
- 数据完整性：checksum、半成品会话、掉电恢复。

## Threat model（MVP）

部署在数据采集现场的边缘节点，可能面对：

- 不可信的采集文件（损坏、恶意命名、超大文件）。
- 局域网内未授权的 telemetry/dashboard 访问。
- 配置错误的 S3 目标或过宽的凭证权限。
- 现场断电、磁盘故障、USB 硬盘被拔。

当前 MVP 的边界：

- Dashboard 默认只监听 `127.0.0.1`；对外部署必须加反向代理与认证。
- 不自动删除原始数据；隔离区只是逻辑标记。
- 交付使用部署方提供的 S3/MinIO 凭证；建议最小权限桶策略。
- 不做多租户隔离；不要在同一实例上处理互不信任的客户数据。

## Hardening checklist

- [ ] Dashboard 不直接暴露公网；使用 VPN / reverse proxy + auth。
- [ ] S3 凭证使用环境变量（`EDR_S3_ACCESS_KEY` / `EDR_S3_SECRET_KEY`）或密钥管理，不写入 `config.yaml` 提交。
- [ ] 采集目录与交付目录使用独立磁盘/权限。
- [ ] 开启 UPS；定期做掉电恢复演练。
- [ ] 定期校验 manifest 中的 sha256。
- [ ] 对外发送 telemetry 时只发送聚合指标，不包含原始数据路径/内容。

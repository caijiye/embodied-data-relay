# 部署手册（单机 MVP）

目标：在一台 x86 小主机上部署具身数据驿，接入采集目录，跑完「质检 → 减量 → 分层 → 交付」。

## 1. 硬件

- x86 小主机（N100/i5 级别），至少 1 个 M.2 NVMe + 1 个 SATA/USB3。
- NVMe 建议 ≥1 TB（热层/缓冲）；HDD 建议 ≥8 TB（冷层）。
- UPS 600 VA；ESP32-S3 健康监控可选。
- 接线见 [../hardware/WIRING.md](../hardware/WIRING.md)，BOM 见 [../hardware/BOM.md](../hardware/BOM.md)。

## 2. 系统

Ubuntu 22.04/24.04 优先：

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg python3.12-venv curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

挂载示例（**不要盲目照抄设备名，先 `lsblk` 确认**）：

```bash
sudo mkfs.ext4 /dev/nvme0n1p1        # 仅新盘；会清空数据
sudo mkdir -p /srv/edr/hot
sudo mount /dev/nvme0n1p1 /srv/edr/hot

sudo mkfs.ext4 /dev/sdb1             # 仅新盘；会清空数据
sudo mkdir -p /srv/edr/cold
sudo mount /dev/sdb1 /srv/edr/cold
```

写入 `/etc/fstab` 前先用 `blkid` 获取 UUID，并做一次重启验证。

## 3. 安装

```bash
sudo useradd -r -m -d /opt/edr edr
sudo -u edr git clone <repo> /opt/edr/app
cd /opt/edr/app
sudo -u edr uv venv --python 3.12
sudo -u edr uv pip install -e ".[dev]"
```

## 4. 配置

复制 `config.yaml` 到 `/etc/edr/config.yaml`，把路径改成绝对路径：

```yaml
paths:
  incoming: /srv/edr/incoming
  hot: /srv/edr/hot
  cold: /srv/edr/cold
  quarantine: /srv/edr/quarantine
  db: /srv/edr/meta/edr.db
  logs: /srv/edr/logs
```

交付到 S3/MinIO 时：

```yaml
delivery:
  enabled: true
  target: s3
  endpoint: http://127.0.0.1:9000
  bucket: edr-delivery
  prefix: embodied
```

失败恢复与资源保护：

```yaml
pipeline:
  max_attempts: 3      # 失败 episode 最多重试次数，超过后置为 failed
  min_free_gb: 2.0     # 转码前 hot 层最低剩余空间
```

`pipeline` 使用 `data/edr.db.lock` 文件锁，禁止两个进程同时处理同一批数据。修复 FFmpeg/权限/磁盘问题后，可以重排失败项：

```bash
uv run python -m edr.cli --config /etc/edr/config.yaml requeue
```

**不要把 access key / secret 写进仓库。** 用环境变量：

```bash
export EDR_S3_ENDPOINT=http://127.0.0.1:9000
export EDR_S3_ACCESS_KEY=...
export EDR_S3_SECRET_KEY=...
export EDR_S3_BUCKET=edr-delivery
```

## 5. 运行

```bash
cd /opt/edr/app
uv run python -m edr.cli --config /etc/edr/config.yaml scan
uv run python -m edr.cli --config /etc/edr/config.yaml pipeline --limit 200
uv run python -m edr.cli --config /etc/edr/config.yaml serve --host 127.0.0.1 --port 8080
```

生产建议用 systemd 跑 dashboard，用 cron/timer 每分钟跑 pipeline：

```ini
# /etc/systemd/system/edr-dashboard.service
[Unit]
Description=Embodied Data Relay dashboard
After=network.target

[Service]
User=edr
WorkingDirectory=/opt/edr/app
Environment=EDR_S3_ENDPOINT=http://127.0.0.1:9000
EnvironmentFile=/etc/edr/secrets.env
ExecStart=/opt/edr/app/.venv/bin/python -m edr.cli --config /etc/edr/config.yaml serve --host 127.0.0.1 --port 8080
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now edr-dashboard
```

```cron
* * * * * /opt/edr/app/.venv/bin/python -m edr.cli --config /etc/edr/config.yaml pipeline --limit 200 >> /srv/edr/logs/cron.log 2>&1
```

## 6. 安全

- Dashboard 只监听 `127.0.0.1`；对外使用 Nginx/Caddy + Basic Auth/OIDC。
- S3 凭证用环境变量或 systemd `EnvironmentFile`，权限 600。
- 采集目录只允许采集服务写入；EDR 只读。
- 定期校验 manifest 的 sha256；不要自动删除原始数据。
- 详见 [../SECURITY.md](../SECURITY.md)。

## 7. 故障排查

| 现象 | 排查 |
|---|---|
| 会话一直不处理 | 是否有 `_COMPLETE`？`scanner.require_complete_marker` 是否为 true？ |
| 质量门禁全 quarantine | 检查 `quality_json` 的 metrics/reasons；用真实帧校准阈值 |
| FFmpeg 失败 | `ffmpeg -version`；路径含中文/空格时用绝对路径；查看事件日志 |
| 交付失败 | S3 端点/桶/凭证；本地模式先验证 `target: local` |
| Dashboard 无数据 | 是否跑了 pipeline？DB 路径是否与 dashboard 一致？ |
| NVMe/HDD 分层没动 | `hot_sessions` 与 `tiering.auto_tier`；只有 delivered/packaged 才会迁移 |

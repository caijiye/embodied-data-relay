# 演示视频脚本（3-5 分钟）

> 目标：让评委在 5 分钟内看懂「问题真实、方案有差异、东西能跑、开源可复现」。

## 录制前准备

```bash
# 1. 清空演示数据（只清 data/，不要动代码）
rm -rf data/incoming data/hot data/cold data/delivered data/edr.db data/edr.db-wal data/edr.db-shm

# 2. 生成 2 个 session / 14 个 episode 的合成数据（含缺陷）
uv run python scripts/synth_recorder.py --out data/incoming --sessions 2 --episodes 7 --cameras 2 --frames 30

# 3. 启动 dashboard
uv run python -m edr.cli --config config.yaml serve --host 127.0.0.1 --port 8080
```

浏览器打开 `http://127.0.0.1:8080`，窗口 1440×900 以上；终端字号调大。

## 分镜

### 0:00-0:30 问题

- 画面：采集现场/机器人 b-roll，或数据目录里大量文件。
- 旁白：具身数据一天 TB 级；8 路 1080p 未压缩 1.5 GB/s；1 TB 走 10 Mbps 要 9 天；大量素材不可用。
- 字幕：**不是存不下，是存了大量不可用数据 + 传不走。**

### 0:30-1:15 方案

- 画面：README 架构图 / dashboard 首页。
- 旁白：采集现场边缘节点：会话感知写入 → 质量门禁 → H.264 减量 → NVMe/HDD 分层 → 可恢复交付。
- 强调：只隔离不删除；按 episode 随机读；数据到训练延迟可观测。

### 1:15-2:45 现场 Demo

1. 终端运行 `uv run python -m edr.cli --config config.yaml pipeline --limit 20`。
2. 切到 dashboard，刷新：
   - Sessions/Episodes 增加；
   - Quality gate 出现 Pass/Review/Quarantine；
   - Compact 远小于 Raw；
   - Storage tiers 出现 Hot/Cold；
   - Recent events 显示 packaged/delivered/quarantined。
3. 点开/展示 session 表：正常片段 delivered，模糊/黑帧/重复片段 quarantined。
4. 终端展示 `data/hot`、`data/cold`、`data/delivered` 目录。
5. 展示 `/api/episodes/{id}/file/camera_front.mp4` 可直接按 episode 取用。

### 2:45-3:30 证据

- 画面：`docs/BENCHMARKS.md` 或 dashboard Benchmark 卡片。
- 旁白：10 Mbps 下 123.9 s → 9.2 s，13.53×；质量门禁剔除 29.4%；合成数据编码减量 99.3% 是上界。
- 强调：真实数据 pilot 会更新；不夸大。

### 3:30-4:15 硬件与开源

- 画面：小主机 + NVMe + HDD + UPS + ESP32/风扇；BOM/接线/SCAD 文件。
- 旁白：<5000 元；BOM、接线、外壳、固件全部开源；Apache-2.0 + CERN-OHL-S-2.0；CI/测试/治理文档齐全。
- 字幕：仓库地址、许可证、赛道二。

### 4:15-4:30 收尾

- 一句话：让具身数据在采集现场就变少、变可用、变得可交付。
- 展示二维码/仓库链接。

## 录制建议

- 用 OBS 或 Windows Xbox Game Bar；1080p 60fps；麦克风降噪。
- 先彩排一遍，确保 `pipeline` 在 10 秒内跑完；必要时减少 episodes/frames。
- 不要录到密钥、客户数据、个人信息。
- 视频上传 B 站/YouTube（不公开列出亦可），提交链接；保留原始文件。

# 架构

## 数据流

```
incoming/session_x/episode_y/
  camera_*/frames/*.png | camera_*/video.mp4
  state.jsonl
  meta.json
        │
        ▼
  scanner  ──►  SQLite (sessions/episodes/events)
        │
        ▼
  quality  ──►  quality_json + status(pass/review/quarantine)
        │
        ▼
  transcode ──►  hot/session/episode/{camera}.mp4 + state.jsonl + manifest.json
        │
        ▼
  tiering  ──►  cold/session/episode/...  (按策略迁移)
        │
        ▼
  delivery ──►  MinIO/S3  (重试、断点、延迟统计)
```

## 组件

| 模块 | 职责 |
|---|---|
| `scanner.py` | 发现完整会话；写入 sessions/episodes；避免半成品被处理 |
| `quality.py` | 抽样帧，计算模糊/曝光/重复/黑帧指标；给出 0-100 分与处置建议 |
| `transcode.py` | FFmpeg 封装；图像序列或视频统一转 H.264；生成 manifest 与校验和 |
| `tiering.py` | hot/cold 路径与迁移策略；SQLite 记录当前层 |
| `delivery.py` | S3/MinIO 上传；multipart/重试；记录 attempts、bytes、延迟 |
| `pipeline.py` | 串联各阶段；幂等；失败可重跑 |
| `api.py` | FastAPI 仪表盘与 JSON API |
| `db.py` | SQLite schema 与查询 |

## 存储分层

- **hot**：NVMe。最近会话、待交付、被训练端标记为优先的 episode。
- **cold**：HDD。已交付的历史原始/压缩数据。
- **quarantine**：逻辑标记，不物理删除。原始数据仍在 cold，质量报告指向它。
- **metadata**：SQLite 常驻 NVMe；记录路径、校验和、质量分、层、交付状态。

## 无损写入

MVP 用「会话完成标记 + 校验和 + 重试」保证可恢复；生产版路线图：

1. NVMe 追加日志（append-only），会话未封存不迁移。
2. UPS + 超级电容/PLP SSD，掉电时刷盘。
3. 写前校验、写后 checksum、manifest 双份。
4. 失败会话进入 `incomplete`，不参与交付。

## 质量门禁

| 指标 | 方法 | 处置 |
|---|---|---|
| 模糊 | Laplacian 方差 | 低于阈值 → review/quarantine |
| 过暗/过曝 | 灰度均值/直方图 | 越界 → review |
| 黑帧 | 均值 < 5 的帧占比 | 超阈值 → quarantine |
| 重复帧 | 均值哈希/帧差 | 超阈值 → review |
| 时长/帧数 | 与 meta 对比 | 不足 → incomplete |

原则：**只标记，不删除**。数据采集现场最怕「自动删了不该删的」。

## 交付

- 目标：S3 兼容（MinIO 本地演示）。
- 策略：按会话优先级排序；失败指数退避；记录 bytes 与时间。
- 指标：`data_to_training_latency = delivery_finished_at - session_completed_at`。
- 生产路线图：带宽限速、断点续传、数据胶囊（物理寄送）。

## 为什么不用 bcache/dm-cache

- 通用块层缓存不感知「录制会话」；bcache 默认跳过顺序 IO，而具身数据正是大块顺序写。
- writeback 模式下 SSD 故障可能丢脏数据。
- 我们的做法：会话级 append-only 暂存 + 封存后再分层，质量门禁在封存时执行；缓存策略围绕 episode 交付优先级，而不是通用块热度。

## 安全与合规

- 不上传原始数据到第三方；交付目标由部署方配置。
- 质量隔离不删除数据；删除需要人工确认。
- 依赖许可证在 `NOTICE` 中列出；软件 Apache-2.0，硬件 CERN-OHL-S-2.0。

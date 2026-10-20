# Benchmarks

## 测试环境

- Windows 11 / x86_64（开发机）
- Python 3.12.13（uv）
- FFmpeg 7.1.1
- 单机，无 GPU；NVMe/HDD 分层逻辑在目录层模拟
- 测试日期：2026-10-20

## 数据集

合成多相机采集会话（`scripts/synth_recorder.py`）：

| 项 | 值 |
|---|---|
| sessions | 2 |
| episodes | 14（每 session 7） |
| cameras | 2 |
| frames / camera | 30 |
| resolution | 320×240 |
| 原始大小 | 153.3 MB |
| 注入缺陷 | normal ×4、blur ×2、dark ×2、duplicate ×2、black ×2、bright ×2 |

缺陷比例高于真实场景，用于验证质量门禁；真实数据的可用率需用 pilot 重新测量。

## 真实数据 pilot：lerobot/pusht

| 项 | 值 |
|---|---|
| 数据集 | `lerobot/pusht`（MIT，206 episodes / 25,650 frames / 96×96 / 10fps） |
| 样本 | 2 episodes × 100 frames |
| 原始 PNG 帧 | 427,173 B |
| 压缩后（MP4 + state + manifest） | 65,785 B |
| 编码减量 | **84.6%（6.5×）** |
| 质量门禁 | 2/2 pass（校准后） |
| 数据集主页 | https://huggingface.co/datasets/lerobot/pusht |

复现：

```bash
# 需要 pyarrow
uv pip install -e ".[pilot]"
# 从 HF 镜像下载少量文件（约 10 MB），或使用你自己的 LeRobot 数据集
python scripts/import_lerobot.py --dataset data/public/pusht --out data/real_pilot/incoming --episodes 2 --frames 100
python -m edr.cli --config config.real.yaml pipeline --limit 20
python -m edr.cli --config config.real.yaml report
```

**校准发现：** pusht 是白底高亮场景，平均亮度约 249；默认 `bright_threshold: 220` 会把正常帧误判为过曝。pilot 配置将阈值调到 253。这说明质量阈值必须按传感器/场景校准，不能一套阈值打天下。

**局限：** 96×96、单相机、短片段；不代表 1080p 多相机真实场景。下一步用更大分辨率的公开/真实数据复测。

## 结果

### 合成数据（缺陷覆盖）10 Mbps 上行（采集现场常见弱网）

| 指标 | 基线：全存全传 | 具身数据驿 |
|---|---:|---:|
| 原始数据 | 153.3 MB | 153.3 MB |
| 交付数据 | 153.3 MB | 0.75 MB |
| 质量门禁剔除 | 0 | 6 / 14 episodes |
| 本地处理时间 | 1.22 s（复制） | 8.56 s |
| 建模上传时间 | 122.67 s | 0.60 s |
| 数据到训练总时间 | 123.89 s（0.034 h） | 9.16 s（0.0025 h） |
| 加速比 | 1.00× | **13.53×** |

### 100 Mbps 上行

在另一次 100 Mbps 运行中，基线上传时间降到约 12.3 s，处理时间开始占主导；端到端从约 14 s 降到约 8-9 s，加速比收敛到约 1.5×。该数字随文件缓存与转码波动，不作为主指标。

### 减量拆解

| 指标 | 值 | 说明 |
|---|---:|---|
| 质量门禁剔除比例 | 29.4% | 原始字节中被隔离、不交付的部分 |
| 编码减量比例 | 99.3% | 可用片段 raw → H.264，合成 PNG 数据的上界 |
| 总减量比例 | 99.5% | 交付字节 / 全部原始字节 |

**重要：** 合成数据把原始帧存为 PNG，而 H.264 对静态合成纹理压缩率极高，因此 99.3% 是**上界**，不代表真实相机数据。真实数据上应分别报告：

- 质量门禁剔除比例（可用率）；
- 可用片段的编码减量（raw frames/MCAP → H.264/ZSTD）；
- 总交付字节 / 总原始字节。

真实数据 pilot 计划使用 AgiBot World / LeRobot 公开样本，并在 PDF 中更新。

## 指标定义

- **数据到训练时间**：会话完成 → 交付完成（本地复制 + 建模上传）。
- **建模上传时间**：`bytes × 8 / uplink_mbps`；本地复制时间单独测量。
- **质量门禁剔除比例**：`1 - usable_raw_bytes / raw_bytes`。
- **编码减量比例**：`1 - compact_bytes / usable_raw_bytes`。
- **总减量比例**：`1 - compact_bytes / raw_bytes`。
- **加速比**：基线总时间 / 管线总时间。

## 复现

```bash
# 安装
uv venv --python 3.12
uv pip install -e ".[dev]"

# 10 Mbps 上行 benchmark
python scripts/benchmark.py --clean --sessions 2 --episodes 7 --cameras 2 --frames 30 --uplink-mbps 10

# 100 Mbps 上行 benchmark
python scripts/benchmark.py --clean --sessions 2 --episodes 7 --cameras 2 --frames 30 --uplink-mbps 100
```

结果写入 `data/benchmark/benchmark_results.json`，并同步到 dashboard 的 Benchmark 卡片。

## 局限

- 合成数据、单机、目录层模拟 NVMe/HDD；未测真实磁盘 IOPS、掉电恢复、2.5GbE/10GbE。
- 未包含人工审核、标注、模型训练时间；只覆盖「采集现场 → 训练可用包」这一段。
- 编码减量是上界；真实相机噪声、运动模糊、长尾场景会降低压缩率。
- 质量门禁目前只做图像质量指标，不做任务成功判定。
- S3/MinIO 交付未在本次 benchmark 中验证（开发环境 Docker Desktop 未运行）；本地交付已验证。
- 并发/重试/磁盘不足等失败路径已有测试覆盖，但未做长时间稳定性与故障演练。

## 下一步

1. 真实 1080p 多相机会话（2-4 路）pilot。
2. 2.5GbE ingest 与 NVMe/HDD 真实分层测试。
3. 训练端随机读延迟（按 episode 读取 vs 整包下载）。
4. 掉电恢复与 checksum 一致性测试。

# 演示视频（最终版）

- 成片（Gitee）：https://gitee.com/yhy196/embodied-data-relay/blob/master/docs/submission/demo.mp4
- GitHub 镜像：https://github.com/caijiye/embodied-data-relay
- 时长：2 分 11 秒；1920×1080 / 30fps / H.264 + AAC
- 旁白：腾讯云 TTS 402002（云大围，磁性男声），Speed 0，24k；19 段逐句音频
- 字幕：每条字幕对应一段独立音频，显示时长 = 音频时长；句间/场景间 0.3s；不裁静音
- 形式：9 页 PPT 式分镜；真实 dashboard 截图 + 现有图表重排，不做假实物、不夸大合成数据
- 字幕：每行 ≤30 字、最多 2 行；字幕与音频同长，不存在推算错位

## 分镜

| # | 时间 | 页面 | 内容 |
|---|---|---|---|
| 1 | 0:00 | 封面 | 具身数据驿；13.53× / 84.6% / ¥192/TB |
| 2 | 0:08 | 问题 | 1.5 GB/s、9 天、≈30% 可用；字节去向 |
| 3 | 0:23 | 方案 | 五层链路：写入、质检、减量、分层、交付 |
| 4 | 0:40 | Demo 1 | 真实 dashboard：48.6 MB → 239.7 KB，99.5%，0.0h |
| 5 | 0:55 | Demo 2 | 质量门禁 2/1/4、Hot 3 / Incoming 4、交付队列 |
| 6 | 1:07 | Benchmark | 13.53×；真实 pilot 84.6%；99.3% 为合成上界 |
| 7 | 1:28 | 硬件 + 成本 | ¥3,453 / 18TB / ¥192/TB；USB 3.0 与 HDD |
| 8 | 1:46 | 开源 | Apache-2.0 + CERN-OHL-S；12 pytest；CI |
| 9 | 2:02 | 收尾 | 仓库地址；三个数字回扣 |

## 复现

```bash
# 1. 生成 9 张 1920x1080 分镜
python scripts/make_video_slides.py

# 2. 逐句生成 TTS、字幕和时间轴（需要环境变量）
export TENCENTCLOUD_SECRET_ID=...
export TENCENTCLOUD_SECRET_KEY=...
python scripts/make_video_v2.py
```

`scripts/make_video_v2.py` 会把每条字幕文本单独合成音频，按音频时长累加时间轴，再烧录字幕；字幕和音频不会错位。

产物：`data/video/demo_full.mp4`（`data/` 已 gitignore；成片在 GitHub Release）。
密钥只通过环境变量传入，不写入仓库。

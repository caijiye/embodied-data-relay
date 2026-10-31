# 演示视频（7 页工程版）

- 成片（Gitee）：https://gitee.com/yhy196/embodied-data-relay/raw/master/docs/submission/demo.mp4
- GitHub 镜像：https://github.com/caijiye/embodied-data-relay
- 时长：2 分 28 秒；1920×1080 / 30fps / H.264 + AAC
- 旁白：腾讯云 TTS 402002（云大围），Speed 0；每页一整段音频，页间 0.3 秒
- 字幕：不做逐句字幕；页面本身写清关键数字
- 风格：白底工程说明，不做暗色发光、英文 kicker、大口号

## 页面

| 页 | 时间 | 页面 | 内容 |
|---|---|---|---|
| 1 | 0:00 | 封面 | 具身数据驿；SSD + HDD 分工，降低每 TB 存储成本 |
| 2 | 0:16 | 采集端的数据压力 | 1.5 GB/s、9 天、≈30% 可用 |
| 3 | 0:38 | 全闪存和云存储的成本 | 2 TB SSD ¥1,009；18 TB 全闪 ¥9,081；云首年 ¥25,920 |
| 4 | 0:58 | SSD + HDD 分工 | 采集 → SSD → 质检/压缩 → HDD → 交付/训练 |
| 5 | 1:21 | 速度会不会下降 | USB 3.0 约 400 MB/s；HDD 200–260 MB/s |
| 6 | 1:39 | 实际效果 | 123.9 s → 9.2 s（13.53×）；427 KB → 66 KB（84.6%） |
| 7 | 2:03 | 成本对比 | ¥3,453/18TB/¥192；全闪 ¥9,081/¥505；云 ¥25,920/年 |

## 复现

```bash
# 1. 生成 7 张 1920x1080 白底幻灯片
python scripts/make_video_v4_slides.py

# 2. 逐页生成 TTS、拼接音频并合成视频（需要环境变量）
export TENCENTCLOUD_SECRET_ID=...
export TENCENTCLOUD_SECRET_KEY=...
python scripts/make_video_v4.py
```

产物：`data/video/v4/demo.mp4`（`data/` 已 gitignore；成片同时提交到仓库 `docs/submission/demo.mp4`）。
密钥只通过环境变量传入，不写入仓库。

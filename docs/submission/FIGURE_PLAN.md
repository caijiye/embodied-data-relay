# PDF 结构与图计划（v4 最终版）

最终文件：`docs/submission/EDR-proposal.pdf`（17 页，2026-10-31 提交版）。
源文件：`docs/submission/proposal_v4.html`；由 `scripts/build_proposal_v4.py` 从 `proposal.html` 重组生成。

## 一、最终目录

```text
封面
目录（Part I–IV + 图 1–12）

开篇 · 一页看懂
Part I 为什么现在做
  01 具身数据的三重成本
  02 现有方案的缺口
Part II 我们怎么做
  03 五层数据链路
  04 硬件与可复现
Part III 凭什么信
  05 Benchmark
  06 成本账
  07 开源治理
Part IV 长期性
  08 路线图
  09 团队
  10 参考资料
```

## 二、图计划（按页序）

| 编号 | 图名 | 类型 | 内容与数据 | 放置 |
|---|---|---|---|---|
| 图 1 | Dashboard | 实际截图 | 质量门禁、减量、热冷分层、交付延迟、benchmark | 开篇 |
| 图 2 | 字节去向 | 堆叠条形 | 合成数据：质检剔除 29.4%、编码减量 70.1%、交付 0.5%；真实 pilot 编码减量 84.6% | 01 |
| 图 3 | 数据链路 | 横向流程图 | 采集 → 会话写入 → 质量门禁 → 模态减量 → 冷热分层 → 弱网交付 → 训练端 | 03 |
| 图 4 | 质量门禁 | 堆叠条形 | 14 episodes：pass 4 / review 4 / quarantine 6；原始字节剔除 29.4% | 03 |
| 图 5 | 模态减量 | 横向条形（对数轴） | RGB 实测 6.5×；Depth/ToF 4–20×（待实测）；IMU/Pose 3–8×（预期） | 03 |
| 图 6 | 存储经济学 | 2×2 示意曲线 | 全 HDD / 混合 / 全 NVMe：成本 per TB × 热路径性能；混合拐点 | 03 |
| 图 7 | 弱网交付 | 横向条形（对数时间） | 1 TB@10 Mbps ≈ 9.3 天；@100 Mbps ≈ 22.2 小时；153 MB 端到端 9.2 s | 03 |
| 图 8 | 硬件参考套件 | 产品拼版（同级示意） | x86 小主机、2 TB NVMe、16 TB HDD、UPS、ESP32-S3、系统连接 | 04 |
| 图 9 | Benchmark 总览 | 三栏柱 | 10 Mbps：123.9 s → 9.2 s（13.53×）；真实 pilot 427 KB → 66 KB（84.6%）；质检剔除 29.4% | 05 |
| 图 10 | 成本对比 | 双栏条形 | 18TB 方案成本（元）与每 TB 成本（元/TB；云为年） | 06 |
| 图 11 | 仓库与治理 | 树状图 | `edr/`、`hardware/`、`docs/`、`tests/`、`.github/`；Apache-2.0 / CERN-OHL-S；CI | 07 |
| 图 12 | 路线图 | 时间线 | v0.1 MVP → v0.2 真实 pilot → v0.3 多节点/数据胶囊 → v1.0 生产 | 08 |

## 三、数据口径

- 合成 benchmark：2 sessions / 14 episodes / 2 cameras / 30 frames / 320×240 / 153.3 MB；10 Mbps 下行模型 123.89 s → 9.16 s（13.53×）。
- 真实 pilot：`lerobot/pusht`，2 episodes × 100 frames，96×96；427,173 B → 65,785 B（84.6%，6.5×）。
- 图 5 的 Depth/ToF 与 IMU/Pose 为预期范围，标「待实测 / 预期」，不参与结论。
- 图 8 为同级产品示意，不是实拍；最终型号、价格与接口以 `hardware/BOM.md` 为准。
- 图 10 价格抓取 2026-10-31；全闪仅介质，云为首年存储、不含流量。

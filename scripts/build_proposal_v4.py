# -*- coding: utf-8 -*-
"""Build the integrated v4 proposal HTML from the current proposal.html.

- Reorders sections into Part I-IV
- Adds the table of contents and figure index
- Inserts figures 1-12 and the cost section
- Keeps the current visual style
"""

from __future__ import annotations

import re
from pathlib import Path

BASE = Path(r"D:\MyProject\开放原子")
SRC = BASE / "docs" / "submission" / "proposal.html"
DST = BASE / "docs" / "submission" / "proposal_v4.html"

s = SRC.read_text(encoding="utf-8")

marker_re = re.compile(r"<!-- ============ (.*?) ============ -->")
matches = list(marker_re.finditer(s))
head = s[: matches[0].start()]
parts: dict[str, str] = {}
for i, m in enumerate(matches):
    name = m.group(1)
    start = m.end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(s)
    parts[name] = s[start:end]

required = ["COVER", "TOC", "1. ONE PAGE", "2. PROBLEM", "3. SOLUTION", "4. HARDWARE",
            "5. DIFFERENTIATION", "6. BENCHMARK", "7. OPEN SOURCE", "8. LONG TERM",
            "9. TEAM", "10. REFERENCES"]
for name in required:
    assert name in parts, name

# ---------------------------------------------------------------- CSS
head = head.replace(
    "</style>",
    """  .figure { margin: 10px auto 12px; page-break-inside: avoid; }
  .figure img { display: block; width: 100%; border: 1px solid #d9e2ec; border-radius: 6px; margin: 0 auto; }
  .figure figcaption { font-size: 8.2pt; color: #52606d; margin-top: 4px; text-align: center; }
</style>""",
    1,
)


def fig(num: int, file: str, caption: str, width: str = "100%") -> str:
    return f"""
  <figure class="figure">
    <img src="../assets/figures/{file}" alt="图 {num}" style="width:{width};">
    <figcaption><b>图 {num}</b> {caption}</figcaption>
  </figure>
"""


def replace(text: str, old: str, new: str) -> str:
    assert old in text, f"missing: {old[:80]}"
    return text.replace(old, new, 1)


# ---------------------------------------------------------------- TOC
toc = """
<!-- ============ TOC ============ -->
<section class="page-break">
  <div class="kicker">目录</div>
  <h2>目录</h2>
  <div class="toc">
    <div><b>开篇</b> 一页看懂：问题、方案与四个数字</div>
    <div><b>Part I</b> 为什么现在做</div>
    <div>01 具身数据的三重成本</div>
    <div>02 现有方案的缺口</div>
    <div><b>Part II</b> 我们怎么做</div>
    <div>03 五层数据链路</div>
    <div>04 硬件与可复现</div>
    <div><b>Part III</b> 凭什么信</div>
    <div>05 Benchmark：合成 + 真实 pilot</div>
    <div>06 成本账：每 TB 与减量收益</div>
    <div>07 开源治理：可复现、可协作</div>
    <div><b>Part IV</b> 长期性</div>
    <div>08 路线图</div>
    <div>09 团队</div>
    <div>10 参考资料</div>
  </div>
  <h3 style="margin-top: 16px;">图 表</h3>
  <div class="toc small">
    <div>图 1 Dashboard</div>
    <div>图 2 字节去向</div>
    <div>图 3 数据链路</div>
    <div>图 4 质量门禁</div>
    <div>图 5 模态减量</div>
    <div>图 6 存储经济学</div>
    <div>图 7 弱网交付</div>
    <div>图 8 硬件参考套件</div>
    <div>图 9 Benchmark</div>
    <div>图 10 成本对比</div>
    <div>图 11 仓库治理</div>
    <div>图 12 路线图</div>
  </div>
  <p class="small" style="margin-top: 16px;">项目名称：具身数据驿｜边缘减量 · 冷热分层 · 弱网快传</p>
</section>
"""

# ---------------------------------------------------------------- one page
one = parts["1. ONE PAGE"]
one = replace(one, "01 · 一页看懂", "开篇 · 一页看懂")
one = replace(one, "完成会话级无损写入", "完成会话级原样落盘")
old_stats = """  <div class="grid-3" style="margin-top: 12px;">
    <div class="stat"><strong>13.53×</strong><span>10 Mbps 上行下端到端加速<br>（123.9 s → 9.2 s，合成数据）</span></div>
    <div class="stat"><strong>29.4%</strong><span>质量门禁剔除的原始字节<br>（合成缺陷数据：模糊/过暗/重复/黑帧/过曝）</span></div>
    <div class="stat"><strong>84.6%</strong><span>真实 LeRobot 样本编码减量<br>（427 KB → 66 KB，6.5×）</span></div>
  </div>"""
new_stats = """  <div class="grid-3" style="margin-top: 12px; grid-template-columns: repeat(4, minmax(0, 1fr));">
    <div class="stat"><strong>13.53×</strong><span>10 Mbps 上行端到端加速<br>（123.9 s → 9.2 s，合成数据）</span></div>
    <div class="stat"><strong>29.4%</strong><span>质量门禁剔除的原始字节<br>（合成缺陷数据）</span></div>
    <div class="stat"><strong>84.6%</strong><span>真实 LeRobot 编码减量<br>（427 KB → 66 KB，6.5×）</span></div>
    <div class="stat"><strong>¥3,453</strong><span>18TB 混合节点<br>复用现有 HDD ≈ ¥192/TB</span></div>
  </div>"""
one = replace(one, old_stats, new_stats)

# remove the text flow + old screenshot, insert dashboard figure
pattern = re.compile(
    r"\n  <div class=\"flow\"[\s\S]*?<div class=\"caption\">.*?</div>\n", re.S
)
one, n = pattern.subn(
    "\n" + fig(1, "fig01_dashboard.png",
               "仪表盘：质量门禁、减量、热冷分层、交付延迟与 benchmark 一屏可见。", "74%"),
    one,
    count=1,
)
assert n == 1

# ---------------------------------------------------------------- problem
problem = parts["2. PROBLEM"]
problem = replace(problem, "02 · 问题", "01 · 问题")
problem = replace(problem, "这比「再买一台更快的 NAS」更接近问题根因。", "这比再买一台更快的 NAS 更能降低总成本。")
problem = replace(
    problem,
    "  <h3>现有方案为什么不够</h3>\n  <table>",
    "  <h3>现有方案为什么不够</h3>\n  <table>",
)
# remove the old comparison table; the next section covers it in detail
pattern = re.compile(r"\n  <h3>现有方案为什么不够</h3>\n  <table>[\s\S]*?</table>", re.S)
problem, n = pattern.subn(
    "\n" + fig(2, "fig02_bytes.png",
               "合成缺陷数据与真实 pilot 的字节去向：质量门禁先剔除不可用片段，编码再压缩可用片段。"),
    problem,
    count=1,
)
assert n == 1

# ---------------------------------------------------------------- differentiation (moved before solution)
diff = parts["5. DIFFERENTIATION"]
diff = replace(diff, "05 · 技术差异", "02 · 现有方案的缺口")
diff = replace(diff, "边界与诚实声明：", "边界与限制：")
diff = replace(diff, "工作负载感知的分层设计", "现有方案的缺口与工作负载错配")

# ---------------------------------------------------------------- solution
sol = parts["3. SOLUTION"]
sol = replace(sol, "03 · 方案", "03 · 五层数据链路")
sol = replace(
    sol,
    "  <h2>五层能力，把数据治理前移到采集现场</h2>\n",
    "  <h2>五层能力，把数据治理前移到采集现场</h2>\n"
    + fig(3, "fig03_pipeline.png",
          "从采集到训练的数据链路：会话写入、质量门禁、模态减量、冷热分层、弱网交付。"),
)
sol = replace(
    sol,
    "  <p>对每个 episode 抽样帧，计算 Laplacian 方差（模糊）、灰度均值（过暗/过曝）、黑帧比例、连续帧差异（重复）。输出 0-100 分与 <code>pass / review / quarantine</code>；<b>只隔离，不删除</b>，隔离数据仍可在冷层追溯。</p>\n",
    "  <p>对每个 episode 抽样帧，计算 Laplacian 方差（模糊）、灰度均值（过暗/过曝）、黑帧比例、连续帧差异（重复）。输出 0-100 分与 <code>pass / review / quarantine</code>；<b>只隔离，不删除</b>，隔离数据仍可在冷层追溯。</p>\n"
    + fig(4, "fig04_quality.png",
          "质量门禁：14 个合成 episode 中 pass 4、review 4、quarantine 6；原始字节剔除 29.4%。"),
)
sol = replace(
    sol,
    "  <p>图像序列/视频统一转 H.264 MP4；状态保留 JSONL/Parquet；生成含 sha256 的 manifest。输出是「训练就绪包」：更少的字节、更明确的 episode 边界、可直接按 episode 随机读。</p>\n",
    "  <p>图像序列/视频统一转 H.264 MP4；状态保留 JSONL/Parquet；生成含 sha256 的 manifest。输出是「训练就绪包」：更少的字节、更明确的 episode 边界、可直接按 episode 随机读。</p>\n"
    + fig(5, "fig05_modality.png",
          "模态减量：RGB 为实测 6.5×；Depth/ToF 与 IMU/pose 为预期范围，标「待实测」，不参与结论。"),
)
sol = replace(
    sol,
    "  <p>热层 NVMe 保存最近会话、待交付与优先 episode；冷层 HDD 保存已交付历史数据；SQLite 常驻元数据。训练端按 episode 取用，不需要整包下载。</p>\n",
    "  <p>热层 NVMe 保存最近会话、待交付与优先 episode；冷层 HDD 保存已交付历史数据；SQLite 常驻元数据。训练端按 episode 取用，不需要整包下载。</p>\n"
    + fig(6, "fig06_storage.png",
          "存储经济学：混合分层位于成本-性能拐点；冷层介质可替换，不绑定 HDD。"),
)
sol = replace(
    sol,
    "  <p>本地目录或 S3/MinIO：本地交付已实测；S3 路径已实现（环境变量凭证、重试、checkpoint），需在部署环境验证。按 quality pass → review 的简单优先级交付，记录每次交付的 bytes、attempts、开始/完成时间，计算「数据到训练」延迟。路线图：带宽限速、更复杂队列、断点续传、物理数据胶囊。</p>\n",
    "  <p>本地目录或 S3/MinIO：本地交付已实测；S3 路径已实现（环境变量凭证、重试、checkpoint），需在部署环境验证。按 quality pass → review 的简单优先级交付，记录每次交付的 bytes、attempts、开始/完成时间，计算「数据到训练」延迟。路线图：带宽限速、更复杂队列、断点续传、物理数据胶囊。</p>\n"
    + fig(7, "fig07_delivery.png",
          "弱网交付：1 TB@10 Mbps 约 9.3 天；本项目 153 MB 在 10 Mbps 下端到端约 9.2 秒。"),
)

# ---------------------------------------------------------------- hardware
hw = parts["4. HARDWARE"]
hw = replace(hw, "04 · 硬件设计", "04 · 硬件与可复现")
hw = replace(hw, "一台 &lt; 5000 元的可复现边缘数据站", "一台可复现的混合存储节点（复用现有 HDD，约 ¥3,453）")

old_table = """  <table>
    <thead><tr><th>部件</th><th>规格</th><th class="num">数量</th><th class="num">参考价（元）</th><th>作用</th></tr></thead>
    <tbody>
      <tr><td>x86 小主机</td><td>N100/i5，M.2 NVMe + SATA/USB3</td><td class="num">1</td><td class="num">已有</td><td>计算与 I/O</td></tr>
      <tr><td>NVMe SSD</td><td>2 TB TLC，PCIe 3.0/4.0</td><td class="num">1</td><td class="num">700</td><td>写入缓冲 / 热层</td></tr>
      <tr><td>HDD</td><td>16 TB CMR，SATA</td><td class="num">1</td><td class="num">2500</td><td>冷层</td></tr>
      <tr><td>HDD 连接</td><td>SATA 线/电源或 USB3 硬盘盒</td><td class="num">1</td><td class="num">100</td><td>容量扩展</td></tr>
      <tr><td>UPS</td><td>600 VA 后备式</td><td class="num">1</td><td class="num">300</td><td>掉电保护</td></tr>
      <tr><td>ESP32-S3</td><td>NTC + PWM 风扇 + OLED（可选）</td><td class="num">1</td><td class="num">150</td><td>温度/风扇健康监控</td></tr>
      <tr><td>外壳</td><td>3D 打印/亚克力 + 铜柱</td><td class="num">1</td><td class="num">300</td><td>固定/风道</td></tr>
      <tr><td>线材/散热</td><td>SATA 电源、风扇、导热垫</td><td class="num">1</td><td class="num">100</td><td>装配</td></tr>
      <tr><td colspan="3"><b>合计（不含已有主机/硬盘）</b></td><td class="num"><b>≈ 4150</b></td><td></td></tr>
    </tbody>
  </table>"""
new_table = """  <table>
    <thead><tr><th>部件</th><th>参考型号</th><th class="num">价格（元）</th><th>作用</th></tr></thead>
    <tbody>
      <tr><td>x86 小主机</td><td>Beelink EQ12：N100 / 16GB / 双 2.5GbE / M.2 + 2.5" SATA</td><td class="num">1,199</td><td>计算 / 网络</td></tr>
      <tr><td>NVMe</td><td>Lexar NQ790 2TB（PCIe 4.0，M.2 2280）</td><td class="num">1,009</td><td>热层 / 写入缓冲</td></tr>
      <tr><td>HDD</td><td>Seagate IronWolf Pro 16TB（CMR；已有 / 可选）</td><td class="num">0</td><td>冷层</td></tr>
      <tr><td>硬盘盒</td><td>ORICO 7688U3：3.5" SATA→USB 3.0，UASP，12V/2A</td><td class="num">148</td><td>3.5" HDD 外接</td></tr>
      <tr><td>UPS</td><td>APC Back-UPS BX650CI（650VA）</td><td class="num">459</td><td>掉电保护</td></tr>
      <tr><td>健康监控</td><td>ESP32-S3-DevKitC-1 + DHT22 + INA226 + OLED</td><td class="num">179</td><td>温度 / 风扇 / 电流</td></tr>
      <tr><td>风扇</td><td>Arctic P12 PWM 120mm</td><td class="num">59</td><td>风道</td></tr>
      <tr><td>外壳</td><td>3D 打印 / 亚克力开放托盘</td><td class="num">300</td><td>固定 / 风道</td></tr>
      <tr><td>线材</td><td>USB 3.0 / 风扇 / 导热垫</td><td class="num">100</td><td>装配</td></tr>
      <tr><td colspan="2"><b>合计（复用现有 HDD）</b></td><td class="num"><b>3,453</b></td><td>18TB，≈ ¥192/TB</td></tr>
      <tr><td colspan="2"><b>合计（新购 16TB HDD）</b></td><td class="num"><b>6,992</b></td><td>超 5000；建议复用现有盘</td></tr>
    </tbody>
  </table>"""
hw = replace(hw, old_table, new_table)
hw = hw.replace("冷层不是瓶颈", "冷层带宽有余量")
hw = replace(
    hw,
    "  <div class=\"grid-2\">\n    <div class=\"card\">\n      <h4>开源硬件交付物</h4>",
    """  <h3>接口与链路</h3>
  <p>NVMe 走 M.2 PCIe；3.5" HDD 走 SATA → USB 3.0-to-SATA（UASP）→ EQ12 USB 3.0，硬盘盒独立 12V/2A 供电。USB 3.0 5Gbps 实测约 400MB/s，单块 HDD 顺序约 200–260MB/s，接口带宽高于磁盘本身，冷层带宽有余量。EQ12 没有多余 PCIe 插槽，不做 PCIe 转 SATA；需要原生 SATA 时改用 N100 mini-ITX + 3.5" 机箱。</p>
  <h3>功耗与供电</h3>
  <p>N100 小主机满载约 25–30W，3.5" HDD 读写约 8–9W，整机峰值约 40W；600VA UPS 在 40W 负载下可支撑数十分钟，足够完成安全关机。3.5" HDD 的 12V 由硬盘盒电源提供，UPS 同时给主机和硬盘盒供电。</p>
"""
    + fig(8, "fig08_hardware.png",
          "硬件参考套件（示意）：x86 小主机、2TB NVMe、16TB HDD、UPS、ESP32-S3、风扇；产品图为同级示意，最终以 BOM 为准。")
    + """
  <div class="grid-2">
    <div class="card">
      <h4>开源硬件交付物</h4>""",
)

# ---------------------------------------------------------------- benchmark
bench = parts["6. BENCHMARK"]
bench = replace(bench, "06 · 证据", "05 · Benchmark")
bench = replace(bench, "不要把 99.3% 当成真实世界数字。", "99.3% 是合成数据上界，不代表真实世界。")
bench = replace(bench, "会显著降低编码减量", "会降低编码减量")
bench = replace(
    bench,
    "  <h3>复现</h3>\n",
    fig(9, "fig09_benchmark.png",
        "Benchmark 汇总：10 Mbps 端到端 13.53×；真实 pilot 427KB→66KB（84.6%）；质量门禁剔除 29.4%。")
    + """\n  <h3>结果解读</h3>
  <ul>
    <li>13.53× 主要来自两段：质量门禁先剔除 29.4% 的原始字节，编码再把剩余字节压到约 0.7%；10 Mbps 上行下，上传时间从 123 s 降到 0.6 s。</li>
    <li>本地处理 8.56 s 是固定成本；上行越快，这部分占比越高。100 Mbps 时上传约 12 s，加速比收敛到约 1.5×，处理时间成为主导。</li>
    <li>真实 pilot 的 84.6% 低于合成数据，因为样本保留全部帧、场景更复杂；这也是 99.3% 只能作为合成上界的原因。</li>
  </ul>

  <h3>复现</h3>\n""",
)

# ---------------------------------------------------------------- cost
cost = """
<!-- ============ 6. COST ============ -->
<section class="page-break">
  <div class="kicker">06 · 成本账</div>
  <h2>每 TB 成本与减量收益</h2>
  <p>按 2026-10-31 公开价格，18TB 混合节点（复用现有 16TB HDD）约 <b>¥3,453</b>，折合 <b>≈¥192/TB</b>；同容量全闪仅介质约 <b>¥9,081</b>（≈¥505/TB，不含主机）；云 OSS 18TB 首年约 <b>¥25,920</b>（不含流量/请求）。</p>

  <table>
    <thead><tr><th>方案</th><th class="num">一次性 / 首年</th><th class="num">容量</th><th class="num">成本 / TB</th><th>说明</th></tr></thead>
    <tbody>
      <tr><td>混合（复用现有 HDD）</td><td class="num">¥3,453</td><td class="num">18 TB</td><td class="num">¥192</td><td>推荐；5000 预算内</td></tr>
      <tr><td>混合（新购 16TB HDD）</td><td class="num">¥6,992</td><td class="num">18 TB</td><td class="num">¥388</td><td>HDD 涨价时超预算</td></tr>
      <tr><td>全闪 18TB（仅介质）</td><td class="num">¥9,081</td><td class="num">18 TB</td><td class="num">¥505</td><td>不含主机；热路径最好</td></tr>
      <tr><td>云 OSS 18TB</td><td class="num">¥2,160/月<br>¥25,920/年</td><td class="num">18 TB</td><td class="num">¥120/月</td><td>不含流量 / 请求</td></tr>
    </tbody>
  </table>

  <figure class="figure">
    <img src="../assets/figures/fig10_cost.png" alt="图 10">
    <figcaption><b>图 10</b> 成本对比：混合、全闪与云；云为首年存储，不含流量；全闪仅介质。</figcaption>
  </figure>

  <div class="note"><b>减量收益：</b>100TB 原始数据 → 质量门禁后 70.6TB → 按真实 pilot 6.5× 编码后约 10.9TB 落盘/上传。需要买的 HDD、上传时间和云存储费用按这个比例下降；该外推仅作示意，真实比例随模态变化。</div>
  <p class="small">价格抓取 2026-10-31；SSD/HDD 价格随行情波动；HDD 复用现有盘；全闪仅介质、云不含流量与请求；实际采购以当天报价为准。</p>
</section>
"""

# ---------------------------------------------------------------- open source
osrc = parts["7. OPEN SOURCE"]
pattern = re.compile(r"\n  <h3>仓库结构</h3>\n  <pre>[\s\S]*?</pre>", re.S)
osrc, n = pattern.subn(
    "\n  <h3>仓库结构</h3>\n"
    + fig(11, "fig11_repo.png",
          "代码、硬件、文档、测试同仓；Apache-2.0 + CERN-OHL-S；CI 与模板随仓库交付。"),
    osrc,
    count=1,
)
assert n == 1

# ---------------------------------------------------------------- long term
long = parts["8. LONG TERM"]
long = replace(long, "08 · 长期发展", "08 · 路线图")
long = replace(
    long,
    "  </table>\n\n  <h3>目标客户</h3>",
    "  </table>\n"
    + fig(12, "fig12_roadmap.png",
          "路线图：v0.1 单机 MVP → v0.2 真实 pilot → v0.3 多节点/数据胶囊 → v1.0 生产。")
    + "\n  <h3>目标客户</h3>",
)
long = replace(
    long,
    "  <h3>商业模式</h3>",
    """  <h3>风险与应对</h3>
  <ul>
    <li>真实数据减量低于合成：已用 pusht pilot 校准预期，v0.2 做 1080p 多相机复测。</li>
    <li>S3/MinIO 未在部署环境验证：v0.2 增加 MinIO 集成测试与部署脚本。</li>
    <li>硬件价格波动：BOM 复用现有 HDD，整机控制在 ¥5,000 内。</li>
    <li>单人团队：核心已开源，治理文档先行，赛后招募 2-3 名 co-maintainer。</li>
  </ul>

  <h3>商业模式</h3>""",
)

# ---------------------------------------------------------------- team
team = parts["9. TEAM"]
team = replace(
    team,
    "当前为高校团队 MVP，团队 ≤8 人；赛后计划招募 2-3 名 co-maintainer（嵌入式/数据工程/文档社区）。",
    "当前为 1 人高校团队 MVP；赛后计划招募 2-3 名 co-maintainer（嵌入式/数据工程/文档社区）。",
)
team = replace(
    team,
    "  <h3>赛事期间投入</h3>",
    """  <h3>已有基础</h3>
  <table>
    <thead><tr><th>交付物</th><th>状态</th></tr></thead>
    <tbody>
      <tr><td>公开代码仓库</td><td>Apache-2.0；CI 通过；12 个 pytest</td></tr>
      <tr><td>可运行 MVP</td><td>采集 → 质检 → 转码 → 分层 → 交付全链路</td></tr>
      <tr><td>真实数据 pilot</td><td>lerobot/pusht：427 KB → 66 KB（84.6%）</td></tr>
      <tr><td>硬件资料</td><td>BOM、接线、OpenSCAD 托盘、ESP32 固件</td></tr>
      <tr><td>参赛材料</td><td>本 PDF、12 张图、演示视频</td></tr>
    </tbody>
  </table>

  <h3>赛事期间投入</h3>""",
)

# ---------------------------------------------------------------- references
refs = parts["10. REFERENCES"]
refs = refs.replace(
    '    <li>从具身智能到桌面小装置：硬件赛道范围：https://m.sohu.com/a/1078976540_827544/</li>\n',
    "",
)
refs = refs.replace(
    '    <li>Intel Optane 停产始末（2022）：https://news.qq.com/rain/a/20260816A04X3F00</li>\n',
    "",
)
extra_refs = """    <li>TrendForce：SSD 合约价一年 +303%，Q4 预计再涨 15–20%（2026-10-26）：https://k.sina.cn/article_5953190046_162d6789e06703ve4c.html</li>
    <li>2TB NVMe 零售价与趋势（2026-10-30）：https://memoryindex.io/zh/ssd-prices</li>
    <li>阿里云 OSS 官方定价（标准 LRS 0.12 元/GB/月，外网流出 0.25–0.50 元/GB）：http://www.aliyun.com/price/detail/oss</li>
    <li>IronWolf Pro 16TB 公开价（2026）：https://wiki.m.smzdm.com/p/gy1r9yd/</li>
    <li>USB 3.0 5Gbps / UASP 实测与 SATA 转 USB 损耗：https://3g.pconline.com.cn/ask/121272.html</li>
    <li>3.5" HDD 需要 12V/5V 供电，USB 口无法提供 12V：https://m.blog.csdn.net/xiong_xin/article/details/145661457</li>
    <li>ORICO 7688U3 规格（USB 3.0 / 16TB / UASP / 12V 2A）：https://wap.zol.com.cn/list/82.html</li>
"""
refs = replace(refs, "  </ol>", extra_refs + "  </ol>")

# ---------------------------------------------------------------- rebuild
new = (
    head
    + "\n<!-- ============ COVER ============ -->\n" + parts["COVER"].strip() + "\n"
    + toc
    + "\n<!-- ============ 1. ONE PAGE ============ -->\n" + one.strip() + "\n"
    + "\n<!-- ============ 2. PROBLEM ============ -->\n" + problem.strip() + "\n"
    + "\n<!-- ============ 3. DIFFERENTIATION ============ -->\n" + diff.strip() + "\n"
    + "\n<!-- ============ 4. SOLUTION ============ -->\n" + sol.strip() + "\n"
    + "\n<!-- ============ 5. HARDWARE ============ -->\n" + hw.strip() + "\n"
    + "\n<!-- ============ 6. BENCHMARK ============ -->\n" + bench.strip() + "\n"
    + cost
    + "\n<!-- ============ 7. OPEN SOURCE ============ -->\n" + osrc.strip() + "\n"
    + "\n<!-- ============ 8. LONG TERM ============ -->\n" + long.strip() + "\n"
    + "\n<!-- ============ 9. TEAM ============ -->\n" + team.strip() + "\n"
    + "\n<!-- ============ 10. REFERENCES ============ -->\n" + refs.strip() + "\n"
)

DST.write_text(new, encoding="utf-8")
print("wrote", DST, len(new), "chars")

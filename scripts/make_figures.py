# -*- coding: utf-8 -*-
"""Generate the v4 figure set for the EDR proposal.

Run with the existing conda environment that has matplotlib:
  C:/Users/y0h1y/anaconda3/envs/memecoins/python.exe scripts/make_figures.py

Outputs PNG + SVG to docs/assets/figures/.
"""

from __future__ import annotations

import math
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

BASE = Path(r"D:\MyProject\开放原子")
OUT = BASE / "docs" / "assets" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

FONT = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
FONT_B = FontProperties(fname=r"C:\Windows\Fonts\msyhbd.ttc")

NAVY = "#1F3864"
TEAL = "#2C6E8F"
ORANGE = "#E36C09"
LIGHT = "#8FB0CB"
PALE = "#DCE6F1"
GRAY = "#595959"
GRID = "#D9D9D9"
GREEN = "#2F855A"
RED = "#C00000"
AMBER = "#C9A227"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none",
    "axes.linewidth": 0.7,
    "xtick.major.size": 2.2,
    "ytick.major.size": 2.2,
})

SYN = {"raw_mb": 153.3, "baseline_s": 123.89, "pipeline_s": 9.16,
       "speedup": 13.53, "quality_drop": 0.294, "pass": 4, "review": 4,
       "quarantine": 6, "codec_drop": 0.993, "delivered_share": 0.0048}
REAL = {"raw_kb": 427, "compact_kb": 66, "reduction": 84.6, "multiple": 6.5}


def save(fig, name: str) -> None:
    fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white")
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", pad_inches=0.05, facecolor="white")
    plt.close(fig)
    print("saved", name)


def canvas(height: float = 2.9):
    fig, ax = plt.subplots(figsize=(7.2, height))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig, ax


def txt(ax, x, y, s, size=8, color=NAVY, weight="normal", ha="center", va="center", **kw):
    fp = FONT_B if weight == "bold" else FONT
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
            fontproperties=fp, **kw)


def box(ax, x, y, w, h, title, sub="", fc="#F7FAFD", ec=TEAL, fs=8.2,
        subfs=6.6, title_y=0.64, sub_y=0.30, lw=1.0, shadow=False):
    if shadow:
        ax.add_patch(FancyBboxPatch((x + 1.2, y - 1.2), w, h,
                                    boxstyle="round,pad=0.02,rounding_size=1.2",
                                    facecolor="#E8EDF3", edgecolor="none", zorder=1))
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.02,rounding_size=1.2",
                                linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2))
    txt(ax, x + w / 2, y + h * title_y, title, size=fs, color=NAVY, weight="bold")
    if sub:
        txt(ax, x + w / 2, y + h * sub_y, sub, size=subfs, color=GRAY, linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, color=TEAL, lw=1.1, rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=9, linewidth=lw, color=color,
                                 shrinkA=1, shrinkB=1,
                                 connectionstyle=f"arc3,rad={rad}",
                                 linestyle=ls, zorder=1))


def style_axis(ax, grid_axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#BFBFBF")
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, lw=0.5, ls=(0, (2, 2)), zorder=0)
        ax.set_axisbelow(True)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(FONT)
        label.set_color(GRAY)


# ---------------------------------------------------------------- 01 pipeline
def fig01_pipeline() -> None:
    fig, ax = canvas(3.0)
    txt(ax, 2, 95, "从采集到训练：一条边缘数据链路", size=10, color=NAVY, weight="bold", ha="left")
    steps = [
        ("采集", "RGB / Depth / ToF\nIMU / Pose"),
        ("会话写入", "NVMe 缓冲\nmanifest / sha256"),
        ("质量门禁", "模糊 / 曝光 / 重复\n黑帧 / 无效片段"),
        ("模态减量", "RGB H.264\nDepth/ToF\nIMU/Pose"),
        ("冷热分层", "NVMe 热\nHDD 冷\nS3 / 胶囊"),
        ("弱网交付", "优先级 / 重试\n延迟可观测"),
        ("训练端", "按 episode\n随机读 / 解压"),
    ]
    n = len(steps)
    w, gap = 11.4, 2.4
    total = n * w + (n - 1) * gap
    x0 = (100 - total) / 2
    y, h = 38, 36
    for i, (title, sub) in enumerate(steps):
        x = x0 + i * (w + gap)
        fc, ec = ("#F2F8FC", TEAL) if i < 4 else ("#FBF6EF", ORANGE)
        box(ax, x, y, w, h, title, sub, fc=fc, ec=ec, fs=8.0, subfs=6.3)
        if i < n - 1:
            arrow(ax, x + w, y + h / 2, x + w + gap, y + h / 2,
                  color=TEAL if i < 4 else ORANGE, lw=1.0)
    bx = x0 - 1.6
    bw = 4 * w + 3 * gap + 3.2
    ax.add_patch(FancyBboxPatch((bx, y - 4), bw, h + 8,
                                boxstyle="round,pad=0.02,rounding_size=1.6",
                                fill=False, edgecolor=TEAL, linewidth=1.0,
                                linestyle=(0, (3, 2)), zorder=0))
    txt(ax, bx + bw / 2, y + h + 6.8, "采集现场（边缘节点）", size=7.2, color=TEAL, weight="bold")
    txt(ax, x0 + 4 * (w + gap) + w / 2, y + h + 6.8, "交付 / 训练侧", size=7.2, color=ORANGE, weight="bold")
    metrics = [
        ("质量门禁剔除", "29.4% 原始字节"),
        ("真实 pilot 编码", "84.6%（6.5×）"),
        ("10 Mbps 端到端", "13.53×"),
    ]
    for i, (a, b) in enumerate(metrics):
        mx = 6 + i * 31
        ax.add_patch(FancyBboxPatch((mx, 8), 28, 10,
                                    boxstyle="round,pad=0.02,rounding_size=1.0",
                                    facecolor="#F7FAFD", edgecolor=PALE, lw=0.8, zorder=2))
        txt(ax, mx + 14, 14.8, a, size=6.4, color=GRAY)
        txt(ax, mx + 14, 11.6, b, size=7.4, color=TEAL, weight="bold")
    txt(ax, 2, 3.2, "实线：数据流；虚线：控制 / 元数据；数字来自现有 benchmark（合成 + 真实 pilot）",
        size=6.0, color=GRAY, ha="left")
    save(fig, "fig01_pipeline")


# ---------------------------------------------------------------- 02 dashboard
def fig02_dashboard() -> None:
    src = BASE / "docs" / "assets" / "dashboard.png"
    dst = OUT / "fig02_dashboard.png"
    shutil.copyfile(src, dst)
    print("saved fig02_dashboard")


# ---------------------------------------------------------------- 03 bytes
def fig03_bytes() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.45))
    fig.subplots_adjust(left=0.15, right=0.98, top=0.78, bottom=0.19)
    rows = [
        ("合成缺陷数据\n153.3 MB", [("质量门禁剔除", 29.4, ORANGE), ("编码减量", 70.1, LIGHT), ("交付", 0.5, GREEN)]),
        ("真实 pilot\n427 KB", [("编码减量", 84.6, LIGHT), ("交付", 15.4, GREEN)]),
    ]
    for i, (label, segs) in enumerate(rows):
        y = 1 - i * 0.68
        left = 0.0
        for name, val, color in segs:
            ax.barh(y, val, left=left, height=0.42, color=color,
                    edgecolor="white", linewidth=0.8, zorder=3)
            if val >= 8:
                fg = NAVY if color == LIGHT else "white"
                ax.text(left + val / 2, y, f"{name}\n{val:.1f}%", ha="center", va="center",
                        fontsize=6.8, color=fg, fontproperties=FONT_B, linespacing=1.2)
            else:
                ax.annotate(f"{name} {val:.1f}%", xy=(left + val / 2, y),
                            xytext=(left + val / 2 + 8, y + 0.32),
                            ha="left", va="center", fontsize=6.2, color=GREEN,
                            fontproperties=FONT,
                            arrowprops=dict(arrowstyle="-", color=GREEN, lw=0.7))
            left += val
    ax.set_yticks([1, 0.32])
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.0, color=GRAY)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.12, 1.48)
    ax.set_xlabel("原始字节占比（%）", fontsize=7.0, color=GRAY, fontproperties=FONT)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xticklabels(["0", "20", "40", "60", "80", "100"])
    style_axis(ax, "x")
    ax.set_title("字节去向：先减量，再交付", fontsize=9.0, color=NAVY,
                 fontproperties=FONT_B, loc="left", pad=8)
    ax.text(0, 1.37, "质量门禁剔除 29.4% 原始字节；合成数据编码减量为上界，真实 pilot 为实测。",
            fontsize=6.1, color=GRAY, fontproperties=FONT)
    save(fig, "fig03_bytes")


# ---------------------------------------------------------------- 04 quality
def fig04_quality() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.1))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.73, bottom=0.22)
    segs = [("Pass", 4, GREEN), ("Review", 4, AMBER), ("Quarantine", 6, RED)]
    left = 0
    for name, val, color in segs:
        ax.barh(0, val, left=left, height=0.5, color=color,
                edgecolor="white", linewidth=1.0, zorder=3)
        ax.text(left + val / 2, 0, f"{name}\n{val}", ha="center", va="center",
                fontsize=7.4, color="white", fontproperties=FONT_B, linespacing=1.2)
        left += val
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.62, 0.82)
    ax.set_yticks([])
    ax.set_xticks(range(0, 15, 2))
    ax.set_xticklabels([str(i) for i in range(0, 15, 2)])
    ax.set_xlabel("episodes（合成缺陷数据，14 个）", fontsize=7.0, color=GRAY, fontproperties=FONT)
    style_axis(ax, "x")
    ax.set_title("质量门禁：不可用片段在边缘被隔离", fontsize=9.0, color=NAVY,
                 fontproperties=FONT_B, loc="left", pad=8)
    ax.text(0, 0.66, "原始字节剔除 29.4%；隔离数据保留在冷层，不进入交付。",
            fontsize=6.2, color=GRAY, fontproperties=FONT)
    ax.text(0, -0.44, "缺陷注入：模糊 / 过暗 / 重复 / 黑帧 / 过曝",
            fontsize=6.2, color=GRAY, fontproperties=FONT)
    save(fig, "fig04_quality")


# ---------------------------------------------------------------- 05 modality
def fig05_modality() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    fig.subplots_adjust(left=0.24, right=0.98, top=0.78, bottom=0.18)
    rows = [
        ("RGB / H.264\n（实测）", 1.0, 6.5, TEAL, "6.5×（84.6%）", "solid"),
        ("Depth / ToF\n（待实测）", 4.0, 20.0, LIGHT, "4–20×（待实测）", "hatch"),
        ("IMU / Pose\n（预期）", 3.0, 8.0, LIGHT, "3–8×（预期）", "hatch"),
    ]
    for i, (label, lo, hi, color, note, kind) in enumerate(rows):
        y = len(rows) - 1 - i
        if kind == "solid":
            ax.barh(y, hi - lo, left=lo, height=0.44, color=color,
                    edgecolor="white", linewidth=0.8, zorder=3)
        else:
            ax.barh(y, hi - lo, left=lo, height=0.44, color=color,
                    edgecolor=NAVY, linewidth=0.8, hatch="///", alpha=0.55, zorder=3)
        ax.text(hi * 1.10, y, note, va="center", fontsize=7.0,
                color=NAVY if kind == "solid" else GRAY,
                fontproperties=FONT_B if kind == "solid" else FONT)
    ax.set_xscale("log")
    ax.set_xlim(1, 32)
    ax.set_xticks([1, 2, 5, 10, 20])
    ax.set_xticklabels(["1", "2", "5", "10", "20"])
    ax.set_yticks([2, 1, 0])
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.0, color=GRAY)
    ax.set_xlabel("压缩倍数（×，对数轴）", fontsize=7.0, color=GRAY, fontproperties=FONT)
    ax.axvline(1, color=GRAY, lw=0.8, ls=(0, (3, 2)), zorder=1)
    style_axis(ax, "x")
    ax.set_title("模态减量：RGB 已实测，Depth/ToF 待实测", fontsize=9.0, color=NAVY,
                 fontproperties=FONT_B, loc="left", pad=8)
    handles = [Patch(facecolor=TEAL, label="实测"), Patch(facecolor=LIGHT, hatch="///", edgecolor=NAVY, label="待实测 / 预期")]
    ax.legend(handles=handles, loc="upper right", frameon=False, fontsize=6.4, prop=FONT)
    save(fig, "fig05_modality")


# ---------------------------------------------------------------- 06 storage
def fig06_storage() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    fig.subplots_adjust(left=0.13, right=0.98, top=0.80, bottom=0.17)
    pts = [
        ("全 HDD", 1.0, 1.1, GRAY, 130),
        ("混合分层", 1.45, 2.55, TEAL, 300),
        ("全 NVMe", 3.0, 3.0, ORANGE, 170),
    ]
    for name, x, y, color, s in pts:
        ax.scatter(x, y, s=s, color=color, edgecolor="white", linewidth=1.3, zorder=4)
        ax.annotate(name, (x, y), xytext=(0, 13 if name != "混合分层" else 17),
                    textcoords="offset points", ha="center", fontsize=8.0,
                    color=color, fontproperties=FONT_B)
    ax.annotate("2 TB NVMe + 16 TB HDD\n热比例 ~11%", xy=(1.45, 2.55),
                xytext=(1.62, 1.72), fontsize=6.6, color=TEAL, fontproperties=FONT,
                arrowprops=dict(arrowstyle="-", color=TEAL, lw=0.8))
    ax.annotate("", xy=(2.95, 2.95), xytext=(1.05, 1.15),
                arrowprops=dict(arrowstyle="->", color=PALE, lw=1.6,
                                connectionstyle="arc3,rad=-0.25"))
    ax.set_xlim(0.7, 3.3)
    ax.set_ylim(0.7, 3.3)
    ax.set_xlabel("相对成本 / TB（示意）", fontsize=7.0, color=GRAY, fontproperties=FONT)
    ax.set_ylabel("热路径性能\n（写入突发 / 随机读）", fontsize=7.0, color=GRAY, fontproperties=FONT)
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(["低", "中", "高"])
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(["低", "中", "高"])
    style_axis(ax, None)
    ax.set_title("存储经济学：混合分层位于成本-性能拐点", fontsize=9.0, color=NAVY,
                 fontproperties=FONT_B, loc="left", pad=8)
    ax.text(0.72, 3.18, "按实际报价；冷层可替换为 HDD / NVMe / 网络挂载 / S3 / 数据胶囊。",
            fontsize=5.9, color=GRAY, fontproperties=FONT)
    save(fig, "fig06_storage")


# ---------------------------------------------------------------- 07 delivery
def fig07_delivery() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.55))
    fig.subplots_adjust(left=0.25, right=0.98, top=0.78, bottom=0.18)
    rows = [
        ("1 TB @ 10 Mbps", 800000, "9.3 天", GRAY),
        ("1 TB @ 100 Mbps", 80000, "22.2 小时", GRAY),
        ("153 MB 原始\n@ 10 Mbps", 122.7, "123 s", LIGHT),
        ("153 MB 本管线\n@ 10 Mbps", 9.2, "9.2 s", ORANGE),
    ]
    for i, (label, val, note, color) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.barh(y, val, height=0.44, color=color, edgecolor="white", linewidth=0.8, zorder=3)
        ax.text(val * 1.15, y, note, va="center", fontsize=7.0,
                color=NAVY if color != GRAY else GRAY,
                fontproperties=FONT_B if color == ORANGE else FONT)
    ax.set_xscale("log")
    ax.set_xlim(1, 2_000_000)
    ax.set_yticks([3, 2, 1, 0])
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.0, color=GRAY)
    ax.set_xlabel("时间（秒，对数轴）", fontsize=7.0, color=GRAY, fontproperties=FONT)
    ax.set_xticks([1, 10, 100, 1000, 10000, 100000, 1000000])
    ax.set_xticklabels(["1", "10", "100", "1k", "10k", "100k", "1M"])
    ax.axvline(9.2, color=ORANGE, lw=0.8, ls=(0, (3, 2)), zorder=1)
    style_axis(ax, "x")
    ax.set_title("弱网交付：先减量，再按优先级传", fontsize=9.0, color=NAVY,
                 fontproperties=FONT_B, loc="left", pad=8)
    save(fig, "fig07_delivery")


# ---------------------------------------------------------------- 08 hardware
def fig08_hardware() -> None:
    fig, ax = canvas(3.1)
    txt(ax, 2, 95, "硬件参考设计：把分层放进一台边缘节点", size=10, color=NAVY, weight="bold", ha="left")
    txt(ax, 2, 89, "成本目标 < ¥5000（不含已有主机 / 硬盘）", size=6.4, color=GRAY, ha="left")

    def comp(x, y, w, h, title, sub, fc, ec):
        box(ax, x, y, w, h, title, sub, fc=fc, ec=ec, fs=7.8, subfs=6.2, shadow=True)

    comp(35, 72, 30, 9, "120 mm 风扇", "风道 / 防尘网", PALE, TEAL)
    comp(30, 52, 40, 15, "x86 小主机 (N100/i5)", "2 TB NVMe · 热层", "#F2F8FC", TEAL)
    comp(27, 34, 46, 11, "16 TB HDD · 冷层", "减震 + 间距 ≥10 mm", "#FBF6EF", ORANGE)
    comp(16, 16, 27, 10, "UPS 600 VA", "掉电保护", "#FFF7E6", AMBER)
    comp(56, 16, 27, 10, "ESP32-S3", "温度 / 风扇 / 电流", "#F2F8FC", TEAL)

    arrow(ax, 50, 72, 50, 67, color=TEAL)
    arrow(ax, 50, 52, 50, 45, color=ORANGE)
    arrow(ax, 29, 26, 38, 52, color=AMBER, rad=-0.12)
    arrow(ax, 69, 26, 61, 52, color=TEAL, rad=0.12)
    arrow(ax, 70, 59, 89, 59, color=GRAY)
    txt(ax, 89.5, 62, "2.5GbE → 训练端", size=6.4, color=GRAY, ha="left")

    txt(ax, 2, 77, "热层：NVMe", size=6.4, color=TEAL, weight="bold", ha="left")
    txt(ax, 2, 70, "冷层：HDD", size=6.4, color=ORANGE, weight="bold", ha="left")
    txt(ax, 2, 63, "保护：UPS", size=6.4, color=AMBER, weight="bold", ha="left")
    txt(ax, 2, 56, "监控：ESP32", size=6.4, color=TEAL, weight="bold", ha="left")

    ax.add_patch(FancyBboxPatch((12, 5), 76, 4,
                                boxstyle="round,pad=0.02,rounding_size=1.0",
                                fill=False, edgecolor=GRAY, linewidth=0.9,
                                linestyle=(0, (3, 2)), zorder=0))
    txt(ax, 50, 7, "reference design · open BOM / 接线 / SCAD / 固件", size=6.2, color=GRAY)
    save(fig, "fig08_hardware")


# ---------------------------------------------------------------- 09 benchmark
def fig09_benchmark() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5),
                             gridspec_kw={"width_ratios": [1.1, 1.0, 1.0]})
    fig.subplots_adjust(left=0.08, right=0.98, top=0.77, bottom=0.20, wspace=0.48)

    ax = axes[0]
    vals = [SYN["baseline_s"], SYN["pipeline_s"]]
    bars = ax.bar(["基线", "本管线"], vals, color=[LIGHT, ORANGE], width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 4, f"{v:.1f}s", ha="center",
                fontsize=7.0, color=NAVY, fontproperties=FONT_B)
    ax.set_ylim(0, 145)
    ax.set_title("端到端时间 @10 Mbps（13.53×）", fontsize=7.8, color=NAVY, fontproperties=FONT_B, pad=6)
    style_axis(ax)

    ax = axes[1]
    vals = [REAL["raw_kb"], REAL["compact_kb"]]
    bars = ax.bar(["原始", "压缩"], vals, color=[LIGHT, GREEN], width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 12, f"{v} KB", ha="center",
                fontsize=7.0, color=NAVY, fontproperties=FONT_B)
    ax.set_ylim(0, 500)
    ax.set_title("真实 pilot 字节（84.6% / 6.5×）", fontsize=7.6, color=NAVY, fontproperties=FONT_B, pad=6)
    style_axis(ax)

    ax = axes[2]
    segs = [("Pass", SYN["pass"], GREEN), ("Review", SYN["review"], AMBER),
            ("Quarantine", SYN["quarantine"], RED)]
    left = 0
    for name, val, color in segs:
        ax.barh(0, val, left=left, height=0.5, color=color,
                edgecolor="white", linewidth=1.0, zorder=3)
        ax.text(left + val / 2, 0, f"{name}\n{val}", ha="center", va="center",
                fontsize=6.8, color="white", fontproperties=FONT_B, linespacing=1.2)
        left += val
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.55, 0.55)
    ax.set_yticks([])
    ax.set_xticks([0, 7, 14])
    ax.set_xticklabels(["0", "7", "14"])
    ax.set_title("质量门禁（29.4% 剔除）", fontsize=7.8, color=NAVY, fontproperties=FONT_B, pad=6)
    style_axis(ax, "x")

    fig.text(0.08, 0.03, "合成缺陷数据 + 真实 LeRobot pilot；编码减量为合成数据上界。",
             fontsize=6.0, color=GRAY, fontproperties=FONT)
    save(fig, "fig09_benchmark")


# ---------------------------------------------------------------- 10 repo
def fig10_repo() -> None:
    fig, ax = canvas(3.0)
    txt(ax, 2, 95, "仓库与治理：代码、硬件、文档、测试同仓", size=10, color=NAVY, weight="bold", ha="left")
    box(ax, 2, 45, 20, 12, "embodied-data-relay", "公开仓库", fc="#F2F8FC", ec=TEAL, fs=7.6, subfs=6.2)
    branches = [
        ("edr/", 77, "扫描 / 质检 / 转码 / 分层 / 交付", TEAL),
        ("hardware/", 64, "BOM / 接线 / 外壳 / 固件", ORANGE),
        ("docs/", 51, "架构 / 基准 / 参赛材料", TEAL),
        ("tests/", 38, "12 pytest", GRAY),
        (".github/", 25, "CI / issue / PR 模板", GRAY),
    ]
    for i, (name, y, sub, color) in enumerate(branches):
        box(ax, 30, y, 26, 9, name, sub, fc="#F7FAFD", ec=color, fs=7.5, subfs=6.2)
        ax.plot([22, 26, 26, 30], [51, 51, y + 4.5, y + 4.5], color=color, lw=0.9, zorder=0)
    badges = [("Apache-2.0", 77, TEAL), ("CERN-OHL-S-2.0", 66, ORANGE),
              ("GitHub Actions", 55, TEAL), ("12 pytest", 44, GRAY)]
    for text, y, color in badges:
        ax.add_patch(FancyBboxPatch((63, y), 29, 6,
                                    boxstyle="round,pad=0.02,rounding_size=1.0",
                                    facecolor="white", edgecolor=color, linewidth=0.8, zorder=2))
        txt(ax, 77.5, y + 3, text, size=6.8, color=color, weight="bold")
    txt(ax, 63, 36, "可复现：bootstrap\n合成数据 / benchmark\n硬件文件 + 部署手册",
        size=6.2, color=GRAY, ha="left", va="top", linespacing=1.35)
    txt(ax, 2, 8, "代码 / 硬件 / 文档 / 测试同仓；许可证、CI 与模板随仓库交付。",
        size=6.2, color=GRAY, ha="left")
    save(fig, "fig10_repo")


# ---------------------------------------------------------------- 11 roadmap
def fig11_roadmap() -> None:
    fig, ax = canvas(1.95)
    txt(ax, 2, 90, "路线图：从单机链路到数据基础设施", size=10, color=NAVY, weight="bold", ha="left")
    y = 50
    ax.plot([8, 92], [y, y], color=PALE, lw=4, solid_capstyle="round", zorder=1)
    pts = [
        (15, "2026-10", "v0.1 MVP", "单机链路"),
        (38, "2026-11/12", "v0.2 真实 pilot", "LeRobot / 掉电"),
        (62, "2027 Q1", "v0.3 多节点", "数据胶囊"),
        (86, "2027 Q2", "v1.0 生产", "安装 / 支持"),
    ]
    for i, (x, date, title, sub) in enumerate(pts):
        color = TEAL if i < 2 else NAVY
        ax.scatter(x, y, s=180, color=color, edgecolor="white", linewidth=1.5, zorder=3)
        up = i % 2 == 0
        txt(ax, x, y + 10 if up else y - 12, date, size=6.6, color=GRAY)
        txt(ax, x, y + 19 if up else y - 21, title, size=7.8, color=color, weight="bold")
        txt(ax, x, y + 26 if up else y - 28, sub, size=6.0, color=GRAY)
    save(fig, "fig11_roadmap")


# ---------------------------------------------------------------- contact sheet
def contact_sheet() -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:  # pragma: no cover
        print("skip contact sheet:", exc)
        return
    files = [
        ("fig01_pipeline.png", "图 01 · 数据链路总览"),
        ("fig02_dashboard.png", "图 02 · Dashboard"),
        ("fig03_bytes.png", "图 03 · 字节去向"),
        ("fig04_quality.png", "图 04 · 质量门禁"),
        ("fig05_modality.png", "图 05 · 模态减量"),
        ("fig06_storage.png", "图 06 · 存储经济学"),
        ("fig07_delivery.png", "图 07 · 弱网交付"),
        ("fig08_hardware.png", "图 08 · 硬件参考设计"),
        ("fig09_benchmark.png", "图 09 · Benchmark"),
        ("fig10_repo.png", "图 10 · 仓库治理"),
        ("fig11_roadmap.png", "图 11 · 路线图"),
    ]
    cols = 3
    cell_w, img_w, label_h, pad = 720, 680, 44, 24
    rows = math.ceil(len(files) / cols)
    cell_h = 430
    canvas_w = cols * cell_w + (cols + 1) * pad
    canvas_h = rows * cell_h + (rows + 1) * pad
    sheet = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 24)
    for idx, (name, label) in enumerate(files):
        path = OUT / name
        if not path.exists():
            continue
        img = Image.open(path).convert("RGB")
        ratio = min(img_w / img.width, (cell_h - label_h - 20) / img.height)
        img = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.LANCZOS)
        r, c = divmod(idx, cols)
        x = pad + c * (cell_w + pad) + (cell_w - img.width) // 2
        y = pad + r * (cell_h + pad)
        sheet.paste(img, (x, y))
        draw.text((pad + c * (cell_w + pad), y + cell_h - label_h), label, fill="#1F3864", font=font)
    out = OUT / "contact_sheet.png"
    sheet.save(out)
    print("saved contact_sheet")


def main() -> None:
    fig01_pipeline()
    fig02_dashboard()
    fig03_bytes()
    fig04_quality()
    fig05_modality()
    fig06_storage()
    fig07_delivery()
    fig08_hardware()
    fig09_benchmark()
    fig10_repo()
    fig11_roadmap()
    contact_sheet()


if __name__ == "__main__":
    main()

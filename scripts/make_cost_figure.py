# -*- coding: utf-8 -*-
"""Cost comparison figure (fig12) using prices captured 2026-10-31."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

BASE = Path(r"D:\MyProject\开放原子")
OUT = BASE / "docs" / "assets" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

FONT = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")
FONT_B = FontProperties(fname=r"C:\Windows\Fonts\msyhbd.ttc")

NAVY = "#1F3864"
TEAL = "#2C6E8F"
ORANGE = "#E36C09"
LIGHT = "#8FB0CB"
GRAY = "#595959"
GRID = "#D9D9D9"


def money(v: float) -> str:
    return f"¥{v:,.0f}"


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#BFBFBF")
    ax.grid(axis="x", color=GRID, lw=0.5, ls=(0, (2, 2)), zorder=0)
    ax.set_axisbelow(True)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(FONT)
        label.set_color(GRAY)


def main() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0),
                             gridspec_kw={"width_ratios": [1.15, 1.0]})
    fig.subplots_adjust(left=0.22, right=0.97, top=0.78, bottom=0.18, wspace=0.55)

    # Panel A: total cost
    labels_a = ["混合\n（现有 HDD）", "混合\n（新 HDD）", "全闪 18TB\n（仅介质）", "云 OSS 18TB\n（首年）"]
    vals_a = [3453, 6992, 9081, 25920]
    colors_a = [TEAL, ORANGE, LIGHT, GRAY]
    y = list(range(len(vals_a)))[::-1]
    ax = axes[0]
    ax.barh(y, vals_a, height=0.55, color=colors_a, edgecolor="white", linewidth=0.8, zorder=3)
    for yi, v in zip(y, vals_a):
        ax.text(v * 1.015, yi, money(v), va="center", fontsize=7.4,
                color=NAVY, fontproperties=FONT_B)
    ax.set_yticks(y)
    ax.set_yticklabels(labels_a, fontsize=7.0, color=GRAY)
    ax.set_xlim(0, 30000)
    ax.set_xticks([0, 10000, 20000, 30000])
    ax.set_xticklabels(["0", "1万", "2万", "3万"])
    ax.set_title("18TB 方案成本（元）", fontsize=8.8, color=NAVY, fontproperties=FONT_B, pad=6)
    style(ax)
    ax.text(0, -0.72, "混合为整机；全闪仅介质；云为首年存储，不含流量。",
            fontsize=5.9, color=GRAY, fontproperties=FONT)
    ax.set_ylim(-0.9, len(vals_a) - 0.3)

    # Panel B: per TB
    labels_b = ["混合（现有）", "混合（新 HDD）", "全闪（介质）", "云（首年）"]
    vals_b = [192, 388, 505, 1440]
    colors_b = [TEAL, ORANGE, LIGHT, GRAY]
    y2 = list(range(len(vals_b)))[::-1]
    ax = axes[1]
    ax.barh(y2, vals_b, height=0.55, color=colors_b, edgecolor="white", linewidth=0.8, zorder=3)
    for yi, v in zip(y2, vals_b):
        ax.text(v * 1.08, yi, f"¥{v:,.0f}", va="center", fontsize=7.2,
                color=NAVY, fontproperties=FONT_B)
    ax.set_xscale("log")
    ax.set_xlim(40, 3000)
    ax.set_xticks([50, 100, 200, 500, 1000, 2000])
    ax.set_xticklabels(["50", "100", "200", "500", "1k", "2k"])
    ax.set_yticks(y2)
    ax.set_yticklabels(labels_b, fontsize=7.0, color=GRAY)
    ax.set_title("每 TB 成本（元/TB；云为年）", fontsize=8.8, color=NAVY, fontproperties=FONT_B, pad=6)
    style(ax)
    ax.text(0, -0.72, "混合为整机；全闪为介质；云为一年存储。",
            fontsize=5.9, color=GRAY, fontproperties=FONT)
    ax.set_ylim(-0.9, len(vals_b) - 0.3)

    fig.suptitle("成本对比：混合、全闪与云", x=0.06, y=0.96, ha="left",
                 fontsize=10, color=NAVY, fontproperties=FONT_B)
    fig.text(0.06, 0.02, "价格抓取 2026-10-31；HDD 复用现有盘；实际采购价随行情波动。",
             fontsize=6.0, color=GRAY, fontproperties=FONT)
    fig.savefig(OUT / "fig12_cost.png", dpi=300, bbox_inches="tight", pad_inches=0.05, facecolor="white")
    fig.savefig(OUT / "fig12_cost.svg", bbox_inches="tight", pad_inches=0.05, facecolor="white")
    plt.close(fig)
    print("saved fig12_cost")


if __name__ == "__main__":
    main()

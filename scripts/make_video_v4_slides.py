# -*- coding: utf-8 -*-
"""7-page white engineering deck for the EDR demo video."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE = Path(r"D:\MyProject\开放原子")
FIG = BASE / "docs" / "assets" / "figures"
DASH = BASE / "data" / "video" / "dashboard_raw.png"
OUT = BASE / "data" / "video" / "v4" / "slides"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1920, 1080
FONT_R = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_N = r"C:\Windows\Fonts\bahnschrift.ttf"

INK = (17, 24, 39)
GRAY = (75, 85, 99)
MUTED = (107, 114, 128)
LINE = (209, 213, 219)
BG = (247, 249, 252)
WHITE = (255, 255, 255)
TEAL = (44, 110, 143)
GREEN = (47, 133, 90)
ORANGE = (194, 84, 10)
BLUE = (59, 130, 246)
SOFT_TEAL = (235, 245, 249)
SOFT_ORANGE = (255, 247, 237)


def f(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def fn(size: int):
    return ImageFont.truetype(FONT_N, size)


def wrap(d, text, font, max_w):
    lines, line = [], ""
    for ch in text:
        test = line + ch
        if d.textlength(test, font=font) <= max_w:
            line = test
        else:
            lines.append(line)
            line = ch
    if line:
        lines.append(line)
    return lines


def text_block(img, xy, text, font, fill, max_w, gap=1.35):
    d = ImageDraw.Draw(img)
    x, y = xy
    lines = wrap(d, text, font, max_w)
    lh = int(font.size * gap)
    for i, line in enumerate(lines):
        d.text((x, y + i * lh), line, font=font, fill=fill)
    return y + len(lines) * lh


def header(img, page, section):
    d = ImageDraw.Draw(img)
    for i, c in enumerate((TEAL, GREEN, ORANGE)):
        d.rounded_rectangle((72 + i * 14, 38, 82 + i * 14, 70), radius=2, fill=c)
    d.text((126, 32), "具身数据驿", font=f(26, True), fill=INK)
    d.text((W - 72 - d.textlength(section, font=f(16)), 44), section, font=f(16), fill=MUTED)
    d.line((72, 92, W - 72, 92), fill=LINE, width=1)
    d.text((72, 1016), "第四届开放原子大赛 · 2026 · 赛道二", font=f(14), fill=MUTED)
    pn = f"{page:02d} / 07"
    d.text((W - 72 - d.textlength(pn, font=f(14)), 1016), pn, font=f(14), fill=MUTED)


def card(img, box, fill=WHITE, outline=LINE, radius=12):
    x, y, w, h = box
    ImageDraw.Draw(img).rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=outline, width=1)


def paste_rounded(canvas, im, box, radius=10):
    x, y, w, h = box
    im = ImageOps.contain(im.convert("RGB"), (w, h), Image.LANCZOS)
    layer = Image.new("RGB", (w, h), "white")
    layer.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    canvas.paste(layer, (x, y), mask)


def title(img, text, sub=None):
    d = ImageDraw.Draw(img)
    d.text((108, 132), text, font=f(46, True), fill=INK)
    if sub:
        d.text((110, 198), sub, font=f(24), fill=GRAY)
    d.rectangle((108, 178, 168, 182), fill=TEAL)


def flow_box(img, x, y, w, h, label, desc, color, fill):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=fill, outline=color, width=2)
    d.text((x + 20, y + 22), label, font=f(26, True), fill=color)
    text_block(img, (x + 20, y + 72), desc, f(17), GRAY, w - 40, 1.4)


def arrow(img, x1, y, x2, color=GRAY):
    d = ImageDraw.Draw(img)
    d.line((x1, y, x2 - 8, y), fill=color, width=3)
    d.polygon((x2, y, x2 - 12, y - 7, x2 - 12, y + 7), fill=color)


def arrow_v(img, x, y1, y2, color=GRAY):
    d = ImageDraw.Draw(img)
    d.line((x, y1, x, y2 - 8), fill=color, width=3)
    d.polygon((x, y2, x - 7, y2 - 12, x + 7, y2 - 12), fill=color)


def page_cover():
    img = Image.new("RGB", (W, H), BG)
    header(img, 1, "封面")
    d = ImageDraw.Draw(img)
    d.rectangle((108, 270, 114, 560), fill=TEAL)
    d.text((140, 255), "具身数据驿", font=f(92, True), fill=INK)
    d.text((142, 375), "SSD + HDD 分工，降低每 TB 存储成本", font=f(34, True), fill=INK)
    d.text((142, 435), "面向具身数据采集现场的存储方案", font=f(26), fill=GRAY)
    d.text((142, 520), "先存得下，再谈训练。", font=f(28, True), fill=TEAL)

    # simple flow on the right
    bx, bw, bh = 1130, 620, 120
    for i, (label, desc, color, fill) in enumerate([
        ("采集", "多相机 / 状态数据", GRAY, WHITE),
        ("SSD", "常用数据 · 热路径", TEAL, SOFT_TEAL),
        ("HDD", "历史数据 · 大容量", GRAY, WHITE),
    ]):
        y = 280 + i * 190
        flow_box(img, bx, y, bw, bh, label, desc, color, fill)
        if i < 2:
            arrow_v(img, bx + bw // 2, y + bh + 10, y + bh + 55, TEAL)
    img.save(OUT / "01_cover.png")


def page_problem():
    img = Image.new("RGB", (W, H), BG)
    header(img, 2, "采集端")
    title(img, "采集端的数据压力", "数据量大、回传慢、可用率低，存储和回传成本被放大。")
    d = ImageDraw.Draw(img)

    stats = [("1.5 GB/s", "8 路 1080p 原始写入", TEAL, fn(60)),
             ("9 天", "1 TB 走 10 Mbps 上行", ORANGE, f(56, True)),
             ("≈30%", "原始素材能进入训练", GREEN, f(56, True))]
    for i, (num, lab, color, nf) in enumerate(stats):
        x = 108 + i * 580
        card(img, (x, 280, 520, 190))
        d.text((x + 28, 300), num, font=nf, fill=color)
        d.text((x + 28, 390), lab, font=f(19), fill=GRAY)

    # availability bar
    d.text((108, 530), "原始数据 100%", font=f(18), fill=MUTED)
    d.rounded_rectangle((108, 565, 1708, 605), radius=6, fill=(229, 231, 235))
    d.rounded_rectangle((108, 565, 108 + int(1600 * 0.30), 605), radius=6, fill=GREEN)
    d.text((108 + int(1600 * 0.30) + 14, 565), "可用约 30%", font=f(18, True), fill=GREEN)

    d.rounded_rectangle((108, 690, 1708, 780), radius=10, fill=SOFT_ORANGE, outline=(253, 186, 116), width=1)
    d.rectangle((108, 690, 114, 780), fill=ORANGE)
    d.text((140, 712), "如果采集端不处理，无效数据会同时占用存储、带宽和清洗人力。",
           font=f(24, True), fill=(124, 45, 18))
    d.text((112, 830), "数据来源：AgiBot World Alpha、NVIDIA Open Physical AI Dataset、公开行业访谈。",
           font=f(14), fill=MUTED)
    img.save(OUT / "02_problem.png")


def page_cost_problem():
    img = Image.new("RGB", (W, H), BG)
    header(img, 3, "成本")
    title(img, "全闪存和云存储的成本", "以 18 TB 为例，全闪存和云存储都难以支撑大规模采集。")
    d = ImageDraw.Draw(img)

    x0, y0, w = 108, 300, 1700
    row_h = 92
    d.rounded_rectangle((x0, y0, x0 + w, y0 + row_h), radius=8, fill=(240, 244, 248))
    cols = [(x0 + 24, "方案"), (x0 + 720, "容量"), (x0 + 980, "成本"), (x0 + 1360, "折合每 TB")]
    for x, t in cols:
        d.text((x, y0 + 28), t, font=f(20, True), fill=INK)
    rows = [
        ("2 TB SSD（单盘）", "2 TB", "¥1,009", "¥505 / TB", False),
        ("18 TB 全闪（仅介质）", "18 TB", "¥9,081", "¥505 / TB", True),
        ("云 OSS（首年）", "18 TB", "¥25,920", "¥1,440 / TB/年", False),
    ]
    for i, (a, b, c, e, hi) in enumerate(rows):
        y = y0 + row_h + i * row_h
        if hi:
            d.rounded_rectangle((x0, y, x0 + w, y + row_h), radius=0, fill=SOFT_ORANGE)
        d.line((x0, y, x0 + w, y), fill=LINE, width=1)
        d.text((x0 + 24, y + 28), a, font=f(22, True if hi else False), fill=INK)
        d.text((x0 + 720, y + 28), b, font=f(22), fill=GRAY)
        d.text((x0 + 980, y + 28), c, font=f(24, True), fill=ORANGE if hi else INK)
        d.text((x0 + 1360, y + 28), e, font=f(22), fill=GRAY)
    d.line((x0, y0 + row_h * (len(rows) + 1), x0 + w, y0 + row_h * (len(rows) + 1)), fill=LINE, width=1)

    d.text((108, 730), "全闪存仅计介质，不含主机；云存储不含流量。", font=f(16), fill=MUTED)
    d.rounded_rectangle((108, 800, 1708, 880), radius=10, fill=WHITE, outline=LINE, width=1)
    d.rectangle((108, 800, 114, 880), fill=ORANGE)
    d.text((140, 820), "对大规模采集来说，关键不是单块盘的价格，而是每 TB 的长期成本。",
           font=f(24, True), fill=(124, 45, 18))
    img.save(OUT / "03_cost_problem.png")


def page_design():
    img = Image.new("RGB", (W, H), BG)
    header(img, 4, "方案")
    title(img, "SSD + HDD 分工", "热路径走 SSD，历史数据进 HDD。")
    d = ImageDraw.Draw(img)

    boxes = [
        ("采集", "多相机 / 状态数据", GRAY, WHITE),
        ("SSD", "常用数据 · 热路径", TEAL, SOFT_TEAL),
        ("质检 / 压缩", "剔除不可用片段", BLUE, (239, 246, 255)),
        ("HDD", "历史数据 · 大容量", GRAY, WHITE),
        ("交付 / 训练", "按 episode 读取", GREEN, (240, 253, 244)),
    ]
    bw, gap, y = 300, 35, 300
    for i, (label, desc, color, fill) in enumerate(boxes):
        x = 108 + i * (bw + gap)
        flow_box(img, x, y, bw, 200, label, desc, color, fill)
        if i < 4:
            arrow(img, x + bw + 6, y + 100, x + bw + gap - 4, color=GRAY)

    d.text((108, 580), "采集先写 SSD；会话结束、质检后，历史数据迁到 HDD。",
           font=f(24), fill=INK)
    d.text((108, 630), "常用数据留在 SSD，交付和训练读取仍然发生在热路径。",
           font=f(24), fill=INK)
    d.rounded_rectangle((108, 720, 1708, 810), radius=10, fill=SOFT_TEAL, outline=(147, 197, 221), width=1)
    d.rectangle((108, 720, 114, 810), fill=TEAL)
    d.text((140, 742), "SSD 负责速度和常用数据，HDD 负责容量和历史归档。",
           font=f(24, True), fill=(21, 94, 117))
    d.text((112, 860), "质检和压缩在数据迁入 HDD 前完成。",
           font=f(16), fill=MUTED)
    img.save(OUT / "04_design.png")


def page_speed():
    img = Image.new("RGB", (W, H), BG)
    header(img, 5, "速度")
    title(img, "速度会不会下降？", "热路径仍在 SSD 上；HDD 只做顺序归档。")
    d = ImageDraw.Draw(img)

    def bar(y, name, value, width, color, note):
        d.text((108, y + 12), name, font=f(24, True), fill=INK)
        d.rounded_rectangle((360, y, 360 + width, y + 56), radius=8, fill=color)
        d.text((360 + width + 20, y + 8), value, font=f(24, True), fill=color)
        d.text((360, y + 68), note, font=f(16), fill=MUTED)

    bar(300, "USB 3.0", "约 400 MB/s", 1200, TEAL, "实测接口带宽")
    bar(470, "单块 HDD", "200–260 MB/s", 780, ORANGE, "顺序读写")
    d.line((360, 610, 1560, 610), fill=LINE, width=1)
    for i, v in enumerate((0, 100, 200, 300, 400)):
        x = 360 + int(1200 * v / 400)
        d.line((x, 610, x, 620), fill=LINE, width=1)
        d.text((x - 10, 628), str(v), font=f(14), fill=MUTED)
    d.text((360 + 1200 - 80, 628), "MB/s", font=f(14), fill=MUTED)

    d.rounded_rectangle((108, 740, 1708, 840), radius=10, fill=SOFT_TEAL, outline=(147, 197, 221), width=1)
    d.rectangle((108, 740, 114, 840), fill=TEAL)
    d.text((140, 762), "接口带宽高于磁盘本身，因此 HDD 不会成为热路径的瓶颈。",
           font=f(24, True), fill=(21, 94, 117))
    d.text((140, 802), "交付和训练读取仍然发生在 SSD 上。", font=f(20), fill=GRAY)
    img.save(OUT / "05_speed.png")


def page_results():
    img = Image.new("RGB", (W, H), BG)
    header(img, 6, "效果")
    title(img, "实际效果", "10 Mbps 上行下，数据到训练时间从 123.9 秒降到 9.2 秒。")
    d = ImageDraw.Draw(img)

    card(img, (108, 280, 900, 570))
    dash = Image.open(DASH).convert("RGB").crop((0, 0, 1440, 900))
    paste_rounded(img, dash, (124, 296, 868, 538), radius=8)

    callouts = [
        ("48.6 MB → 239.7 KB", "原始数据 → 训练就绪包", TEAL),
        ("99.5%", "边缘减量", GREEN),
        ("0.0 h", "平均交付延迟", ORANGE),
    ]
    for i, (big, small, color) in enumerate(callouts):
        y = 288 + i * 160
        card(img, (1050, y, 660, 130))
        d.text((1074, y + 18), big, font=f(36, True), fill=color)
        d.text((1074, y + 78), small, font=f(18), fill=GRAY)

    d.text((1050, 752), "13.53×", font=fn(54), fill=ORANGE)
    d.text((1198, 772), "端到端加速", font=f(18), fill=MUTED)
    img.save(OUT / "06_results.png")


def page_cost_compare():
    img = Image.new("RGB", (W, H), BG)
    header(img, 7, "成本对比")
    title(img, "成本对比", "同样 18 TB，混合方案约为全闪存的 38%，云存储首年的 13%。")
    d = ImageDraw.Draw(img)

    rows = [
        ("SSD + HDD 混合", 3453, "¥3,453", "¥192 / TB", TEAL),
        ("全闪存（仅介质）", 9081, "¥9,081", "¥505 / TB", ORANGE),
        ("云存储（首年）", 25920, "¥25,920", "¥1,440 / TB/年", MUTED),
    ]
    maxv = 25920
    x0, bar_x, bar_max = 108, 560, 1000
    for i, (name, v, money, per, color) in enumerate(rows):
        y = 300 + i * 150
        d.text((x0, y + 12), name, font=f(22, True), fill=INK)
        d.rounded_rectangle((bar_x, y, bar_x + int(bar_max * v / maxv), y + 52), radius=8, fill=color)
        d.text((bar_x + int(bar_max * v / maxv) + 18, y + 4), money, font=f(24, True), fill=color)
        d.text((bar_x + int(bar_max * v / maxv) + 18, y + 38), per, font=f(16), fill=MUTED)
    for i, v in enumerate((0, 10000, 20000, 30000)):
        x = bar_x + int(bar_max * v / maxv)
        d.line((x, 760, x, 770), fill=LINE, width=1)
        d.text((x - 14, 778), ["0", "1万", "2万", "3万"][i], font=f(14), fill=MUTED)

    d.text((108, 820), "混合含主机、UPS、外壳；全闪仅介质；云为首年存储，不含流量。", font=f(15), fill=MUTED)
    img.save(OUT / "07_cost.png")


def main():
    page_cover()
    page_problem()
    page_cost_problem()
    page_design()
    page_speed()
    page_results()
    page_cost_compare()
    print("slides ->", OUT)


if __name__ == "__main__":
    main()

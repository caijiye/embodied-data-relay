# -*- coding: utf-8 -*-
"""Generate 1920x1080 slides for the EDR demo video."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE = Path(r"D:\MyProject\开放原子")
FIG = BASE / "docs" / "assets" / "figures"
DASH = BASE / "data" / "video" / "dashboard_raw.png"
OUT = BASE / "data" / "video" / "slides"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1920, 1080
FONT_R = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_N = r"C:\Windows\Fonts\bahnschrift.ttf"

NAVY = (8, 24, 38)
NAVY2 = (14, 39, 64)
WHITE = (240, 246, 252)
MUTED = (159, 179, 200)
TEAL = (44, 110, 143)
GREEN = (47, 133, 90)
MINT = (125, 211, 176)
ORANGE = (227, 108, 9)
BLUE = (142, 202, 230)
LINE = (30, 58, 86)
CARD = (18, 43, 68)
CARD2 = (21, 51, 78)


def f(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def fn(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_N, size)


def gradient_bg() -> Image.Image:
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(NAVY[i] + (NAVY2[i] - NAVY[i]) * t) for i in range(3))
        d.line((0, y, W, y), fill=c)
    # dot grid
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for y in range(24, H, 42):
        for x in range(24, W, 42):
            ld.ellipse((x, y, x + 2, y + 2), fill=(120, 170, 210, 16))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    # soft glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((980, -260, 1900, 620), fill=(44, 110, 143, 38))
    gd.ellipse((-260, 700, 640, 1500), fill=(47, 133, 90, 24))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    return img


def load_rgb(path: Path) -> Image.Image:
    im = Image.open(path)
    if im.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


def wrap(d: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        line = ""
        for ch in para:
            test = line + ch
            if d.textlength(test, font=font) <= max_w:
                line = test
            else:
                if ch in "，。；：、）》”" and line:
                    line += ch
                else:
                    lines.append(line)
                    line = ch
        if line:
            lines.append(line)
    return lines


def text_block(img, xy, text, font, fill, max_w, line_gap=1.3):
    d = ImageDraw.Draw(img)
    x, y = xy
    lines = wrap(d, text, font, max_w)
    lh = int(font.size * line_gap)
    for i, line in enumerate(lines):
        d.text((x, y + i * lh), line, font=font, fill=fill)
    return y + len(lines) * lh


def spaced(d, xy, text, font, fill, gap=3):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + gap


def header(img, idx: int, label: str):
    d = ImageDraw.Draw(img)
    # logo
    for i, c in enumerate((TEAL, MINT, ORANGE)):
        d.rounded_rectangle((80 + i * 16, 38, 90 + i * 16, 76), radius=3, fill=c)
    d.text((140, 34), "具身数据驿", font=f(28, True), fill=WHITE)
    spaced(d, (142, 70), "EMBODIED DATA RELAY", f(11), MUTED, 2)
    d.text((W - 80 - d.textlength("TRACK 02 · 开源智能硬件", font=f(17)), 46),
           "TRACK 02 · 开源智能硬件", font=f(17), fill=MUTED)
    d.line((80, 104, W - 80, 104), fill=LINE, width=1)
    d.text((80, 1012), "第四届开放原子大赛 · 2026", font=f(14), fill=MUTED)
    right = f"{idx:02d} / 09"
    d.text((W - 80 - d.textlength(right, font=f(14)), 1012), right, font=f(14), fill=MUTED)


def paste_rounded(canvas: Image.Image, im: Image.Image, box, radius=14):
    x, y, w, h = box
    im = ImageOps.contain(im.convert("RGB"), (w, h), Image.LANCZOS)
    layer = Image.new("RGB", (w, h), "white")
    layer.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    canvas.paste(layer, (x, y), mask)


def card(img, box, fill=CARD, outline=LINE, radius=18, shadow=True):
    d = ImageDraw.Draw(img)
    x, y, w, h = box
    if shadow:
        d.rounded_rectangle((x + 8, y + 10, x + w + 8, y + h + 10), radius=radius, fill=(4, 13, 22))
    d.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=outline, width=1)


def chip(img, xy, text, color, size=18):
    d = ImageDraw.Draw(img)
    x, y = xy
    tw = d.textlength(text, font=f(size, True))
    d.rounded_rectangle((x, y, x + tw + 34, y + size + 18), radius=(size + 18) // 2,
                        fill=(color[0] // 5, color[1] // 5, color[2] // 5),
                        outline=color, width=1)
    d.text((x + 17, y + 8), text, font=f(size, True), fill=color)
    return x + tw + 34


def stat(img, xy, num, label, color, nsize=64, lsize=20, nfont=None):
    d = ImageDraw.Draw(img)
    x, y = xy
    d.text((x, y), num, font=nfont or fn(nsize), fill=color)
    d.text((x, y + nsize + 8), label, font=f(lsize), fill=MUTED)


def slide_cover():
    img = gradient_bg()
    header(img, 1, "cover")
    d = ImageDraw.Draw(img)
    d.rectangle((80, 172, 86, 560), fill=TEAL)
    spaced(d, (122, 170), "TRACK 02 · OPEN-SOURCE SMART HARDWARE", f(17, True), MINT, 2)
    d.text((116, 206), "具身数据驿", font=f(110, True), fill=WHITE)
    spaced(d, (122, 350), "EMBODIED DATA RELAY", f(24), MUTED, 6)
    d.text((118, 410), "边缘减量 · 冷热分层 · 弱网快传", font=f(42, True), fill=WHITE)
    d.text((120, 482), "在采集现场，把原始 TB 变成可训练小时。", font=f(26), fill=BLUE)

    # stats
    stats = [("13.53×", "10 Mbps 端到端加速", MINT),
             ("84.6%", "真实样本编码减量", BLUE),
             ("¥192", "每 TB 混合存储成本", ORANGE)]
    for i, (n, lab, c) in enumerate(stats):
        x = 118 + i * 280
        card(img, (x, 690, 250, 150), fill=(15, 36, 58), outline=(33, 65, 95), radius=14, shadow=False)
        d.text((x + 24, 710), n, font=fn(52), fill=c)
        d.text((x + 24, 780), lab, font=f(18), fill=MUTED)

    # dashboard card
    dash = Image.open(DASH).convert("RGB").crop((0, 0, 1440, 430))
    card(img, (1040, 178, 790, 268), fill=(8, 22, 36), outline=(42, 74, 106), radius=16)
    paste_rounded(img, dash, (1052, 190, 766, 244), radius=10)
    d.text((1052, 452), "真实 dashboard · 边缘节点", font=f(16), fill=MUTED)
    d.text((1040, 520), "采集现场", font=f(22, True), fill=MINT)
    d.text((1040, 558), "会话封存后再分层；\n质量门禁只隔离，不删除。", font=f(20), fill=WHITE, spacing=8)
    d.text((80, 1012), "第四届开放原子大赛 · 2026", font=f(14), fill=MUTED)
    right = "01 / 09"
    d.text((W - 80 - d.textlength(right, font=f(14)), 1012), right, font=f(14), fill=MUTED)
    img.save(OUT / "01_cover.png")


def slide_problem():
    img = gradient_bg()
    header(img, 2, "problem")
    d = ImageDraw.Draw(img)
    d.text((110, 142), "大量数据不可用，", font=f(50, True), fill=WHITE)
    d.text((110, 204), "弱网上行又慢，交付被拖住。", font=f(50, True), fill=WHITE)

    rows = [("1.5 GB/s", "8 路 1080p 原始数据", ORANGE, fn(66)),
            ("9 天", "1 TB 走 10 Mbps 上行", ORANGE, f(62, True)),
            ("≈30%", "原始素材能真正用于训练", MINT, f(62, True))]
    for i, (n, lab, c, nf) in enumerate(rows):
        y = 320 + i * 150
        d.text((116, y), n, font=nf, fill=c)
        d.text((116, y + 82), lab, font=f(22), fill=MUTED)

    card(img, (960, 300, 850, 300), fill=(250, 252, 255), outline=(210, 222, 234), radius=14)
    fig = load_rgb(FIG / "fig02_bytes.png")
    paste_rounded(img, fig, (980, 322, 810, 225), radius=8)
    d.text((980, 558), "质量门禁先剔除不可用片段，编码再压缩可用片段。", font=f(18), fill=(72, 101, 129))

    d.rounded_rectangle((110, 800, 1810, 900), radius=14, fill=(38, 28, 16), outline=(120, 75, 20), width=1)
    d.rectangle((110, 800, 118, 900), fill=ORANGE)
    d.text((146, 826), "如果不在现场处理，这些字节会同时占用存储、带宽和清洗人力。", font=f(25, True), fill=(255, 214, 165))
    d.text((116, 940), "数据来源：AgiBot World Alpha、NVIDIA Open Physical AI Dataset、公开行业访谈。", font=f(14), fill=MUTED)
    img.save(OUT / "02_problem.png")


def slide_solution():
    img = gradient_bg()
    header(img, 3, "solution")
    d = ImageDraw.Draw(img)
    d.text((110, 140), "五层链路，把治理前移到采集现场", font=f(50, True), fill=WHITE)
    d.text((112, 206), "会话封存后才分层；质量门禁只隔离，不删除。", font=f(22), fill=BLUE)

    cards = [
        ("01", "会话感知写入", "NVMe 追加暂存；\n封存后才进入分层。", "NVMe", TEAL),
        ("02", "边缘质量门禁", "模糊、过暗、过曝、\n黑帧、重复；三档结果。", "只隔离", ORANGE),
        ("03", "训练格式减量", "图像序列转 H.264；\n状态保留 JSONL；\n生成 sha256 manifest。", "H.264", MINT),
        ("04", "热冷分层", "热层 NVMe 存最近会话；\n冷层 HDD 存已交付历史。", "NVMe / HDD", BLUE),
        ("05", "可恢复交付", "local / S3；按 pass → review\n优先；重试与延迟可观测。", "local / S3", ORANGE),
    ]
    for i, (num, title, body, tag, c) in enumerate(cards):
        x = 110 + i * 350
        card(img, (x, 280, 320, 400), fill=CARD, outline=(33, 65, 95), radius=16)
        d.text((x + 26, 300), num, font=fn(44), fill=c)
        d.text((x + 26, 360), title, font=f(28, True), fill=WHITE)
        text_block(img, (x + 26, 420), body, f(18), MUTED, 268, 1.45)
        d.rounded_rectangle((x + 26, 620, x + 26 + d.textlength(tag, font=f(16, True)) + 24, 652),
                            radius=16, fill=(20, 50, 44), outline=(45, 100, 84), width=1)
        d.text((x + 38, 626), tag, font=f(16, True), fill=MINT)
        if i < 4:
            ax = x + 326
            d.line((ax, 330, ax + 18, 330), fill=(70, 100, 130), width=2)
            d.polygon((ax + 18, 330, ax + 10, 324, ax + 10, 336), fill=(70, 100, 130))

    d.line((110, 740, 1810, 740), fill=LINE, width=1)
    points = ["会话级状态机，每步幂等可重跑",
              "质检不删除原始数据，隔离可追溯",
              "交付记录 bytes / attempts / 延迟"]
    for i, p in enumerate(points):
        x = 110 + i * 560
        d.ellipse((x, 770, x + 14, 784), fill=MINT)
        d.text((x + 26, 764), p, font=f(21), fill=WHITE)
    img.save(OUT / "03_solution.png")


def slide_demo_1():
    img = gradient_bg()
    header(img, 4, "demo1")
    d = ImageDraw.Draw(img)
    d.text((110, 140), "现场 Demo：一屏看到数据去向", font=f(48, True), fill=WHITE)
    d.text((112, 204), "原始 48.6 MB → 训练就绪 239.7 KB；减量 99.5%。", font=f(24), fill=BLUE)

    card(img, (1080, 190, 730, 800), fill=(8, 22, 36), outline=(42, 74, 106), radius=16)
    dash = Image.open(DASH).convert("RGB")
    paste_rounded(img, dash, (1092, 202, 706, 776), radius=10)

    stats = [("99.5%", "边缘减量比", MINT),
             ("245.0 KB", "已交付", BLUE),
             ("0.0 h", "平均交付延迟", ORANGE)]
    for i, (n, lab, c) in enumerate(stats):
        y = 270 + i * 180
        d.text((116, y), n, font=fn(70), fill=c)
        d.text((116, y + 82), lab, font=f(22), fill=MUTED)

    d.text((116, 800), "1 session / 7 episodes 演示运行", font=f(17), fill=MUTED)
    d.text((110, 900), "这是实际跑出来的 dashboard，不是示意图。", font=f(22), fill=WHITE)
    img.save(OUT / "04_demo1.png")


def slide_demo_2():
    img = gradient_bg()
    header(img, 5, "demo2")
    d = ImageDraw.Draw(img)
    d.text((110, 140), "质量门禁、冷热层、交付队列，一屏可见", font=f(44, True), fill=WHITE)

    card(img, (110, 210, 1080, 590), fill=(8, 22, 36), outline=(42, 74, 106), radius=16)
    dash = Image.open(DASH).convert("RGB").crop((0, 430, 1440, 1220))
    paste_rounded(img, dash, (122, 222, 1056, 566), radius=10)

    callouts = [
        ("Pass 2  ·  Review 1  ·  Quarantine 4", "质量门禁", MINT),
        ("Hot 3  ·  Cold 0  ·  Incoming 4", "热冷分层", BLUE),
        ("Delivered 245.0 KB  ·  0.0 h", "交付队列", ORANGE),
    ]
    for i, (txt, lab, c) in enumerate(callouts):
        y = 260 + i * 160
        card(img, (1230, y, 560, 116), fill=(15, 36, 58), outline=(33, 65, 95), radius=14, shadow=False)
        d.text((1252, y + 18), lab, font=f(18, True), fill=c)
        d.text((1252, y + 50), txt, font=f(21, True), fill=WHITE)

    d.text((110, 840), "只隔离，不删除；失败自动重试；按 episode 优先交付。", font=f(23), fill=WHITE)
    d.text((110, 890), "隔离数据仍保留在原始 / 冷层，可人工复查。", font=f(19), fill=MUTED)
    img.save(OUT / "05_demo2.png")


def slide_benchmark():
    img = gradient_bg()
    header(img, 6, "benchmark")
    d = ImageDraw.Draw(img)
    d.text((110, 138), "10 Mbps 上行，端到端 13.53×", font=f(50, True), fill=WHITE)
    d.text((116, 230), "13.53×", font=fn(104), fill=MINT)
    d.text((118, 350), "数据到训练总时间：123.9 s → 9.2 s", font=f(23), fill=WHITE)
    d.text((700, 260), "真实 pilot", font=f(20, True), fill=BLUE)
    d.text((700, 294), "427 KB → 66 KB", font=f(38, True), fill=WHITE)
    d.text((700, 348), "84.6% 减量 · 6.5×", font=f(24, True), fill=MINT)

    card(img, (110, 430, 1700, 440), fill=(250, 252, 255), outline=(210, 222, 234), radius=14)
    fig = load_rgb(FIG / "fig09_benchmark.png")
    paste_rounded(img, fig, (130, 450, 1660, 400), radius=8)

    d.rounded_rectangle((110, 900, 1810, 980), radius=12, fill=(38, 28, 16), outline=(120, 75, 20), width=1)
    d.rectangle((110, 900, 118, 980), fill=ORANGE)
    d.text((146, 922), "99.3% 是合成 PNG 上界；真实 pilot 84.6% 更可信。", font=f(24, True), fill=(255, 214, 165))
    img.save(OUT / "06_benchmark.png")


def slide_hardware():
    img = gradient_bg()
    header(img, 7, "hardware")
    d = ImageDraw.Draw(img)
    d.text((110, 138), "一台 ¥3,453 的混合节点，18 TB ≈ ¥192/TB", font=f(44, True), fill=WHITE)

    card(img, (110, 220, 860, 573), fill=(250, 252, 255), outline=(210, 222, 234), radius=14)
    hw = load_rgb(FIG / "fig08_hardware.png")
    paste_rounded(img, hw, (128, 238, 824, 537), radius=8)
    d.text((128, 800), "硬件参考套件（同级示意）", font=f(16), fill=MUTED)

    card(img, (1020, 220, 790, 347), fill=(250, 252, 255), outline=(210, 222, 234), radius=14)
    cost = load_rgb(FIG / "fig10_cost.png")
    paste_rounded(img, cost, (1038, 238, 754, 311), radius=8)

    bullets = [("¥3,453", "整机 / 18 TB（复用现有 HDD）", MINT),
               ("¥9,081", "全闪仅介质（不含主机）", BLUE),
               ("¥25,920", "云 OSS 18 TB 首年", ORANGE)]
    for i, (n, lab, c) in enumerate(bullets):
        y = 610 + i * 92
        d.text((1020, y), n, font=fn(36), fill=c)
        d.text((1180, y + 8), lab, font=f(19), fill=MUTED)

    d.text((110, 880), "USB 3.0 约 400 MB/s；单盘 HDD 200–260 MB/s；BOM / 接线 / 外壳 / 固件开源。",
           font=f(21), fill=WHITE)
    img.save(OUT / "07_hardware.png")


def slide_open():
    img = gradient_bg()
    header(img, 8, "open")
    d = ImageDraw.Draw(img)
    d.text((110, 140), "可复现、可协作的开源交付", font=f(50, True), fill=WHITE)
    d.text((112, 204), "代码、硬件、文档、测试同仓；CI 与模板随仓库交付。", font=f(22), fill=BLUE)

    card(img, (110, 250, 1060, 450), fill=(250, 252, 255), outline=(210, 222, 234), radius=14)
    repo = load_rgb(FIG / "fig11_repo.png")
    paste_rounded(img, repo, (128, 268, 1024, 414), radius=8)

    licenses = [("Apache-2.0", "软件"), ("CERN-OHL-S-2.0", "硬件设计"), ("CC BY 4.0", "文档")]
    for i, (name, lab) in enumerate(licenses):
        y = 250 + i * 130
        card(img, (1220, y, 590, 105), fill=(15, 36, 58), outline=(33, 65, 95), radius=12, shadow=False)
        d.text((1242, y + 18), name, font=f(24, True), fill=WHITE)
        d.text((1242, y + 58), lab, font=f(17), fill=MUTED)

    d.text((110, 760), "12 pytest · GitHub Actions CI · issue/PR 模板 · DCO", font=f(22), fill=WHITE)
    d.text((110, 812), "https://github.com/caijiye/embodied-data-relay", font=f(26, True), fill=MINT)
    img.save(OUT / "08_open.png")


def slide_close():
    img = gradient_bg()
    header(img, 9, "close")
    d = ImageDraw.Draw(img)
    # large watermark
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((1180, 180), "EDR", font=fn(420), fill=(80, 140, 180, 18))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    d = ImageDraw.Draw(img)

    d.text((110, 250), "让数据在采集现场，", font=f(62, True), fill=WHITE)
    d.text((110, 330), "就变少、变可用、变得可交付。", font=f(62, True), fill=WHITE)
    d.text((114, 440), "具身数据驿 · Embodied Data Relay", font=f(26), fill=BLUE)

    stats = [("13.53×", "10 Mbps 端到端加速", MINT),
             ("84.6%", "真实样本编码减量", BLUE),
             ("¥192", "每 TB 混合存储成本", ORANGE)]
    for i, (n, lab, c) in enumerate(stats):
        x = 114 + i * 300
        d.text((x, 560), n, font=fn(58), fill=c)
        d.text((x, 638), lab, font=f(19), fill=MUTED)

    d.text((110, 780), "https://github.com/caijiye/embodied-data-relay", font=f(28, True), fill=WHITE)
    d.text((110, 835), "第四届开放原子大赛 · 2026 · 赛道二", font=f(20), fill=MUTED)
    img.save(OUT / "09_close.png")


def main():
    slide_cover()
    slide_problem()
    slide_solution()
    slide_demo_1()
    slide_demo_2()
    slide_benchmark()
    slide_hardware()
    slide_open()
    slide_close()
    print("slides saved to", OUT)


if __name__ == "__main__":
    main()

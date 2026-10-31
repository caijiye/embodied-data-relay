# -*- coding: utf-8 -*-
"""Compose the hardware reference kit panel (fig08).

Uses official/CC illustrative product images in docs/assets/figures/hardware/.
Run with the conda environment that has Pillow:
  C:/Users/y0h1y/anaconda3/envs/memecoins/python.exe scripts/make_hardware_panel.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE = Path(r"D:\MyProject\开放原子")
FIG = BASE / "docs" / "assets" / "figures"
HW = FIG / "hardware"
OUT = FIG / "fig08_hardware_v3.png"

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"

NAVY = "#1F3864"
TEAL = "#2C6E8F"
ORANGE = "#E36C09"
GRAY = "#595959"
LIGHT = "#F2F8FC"
BORDER = "#D9E2EC"
PALE = "#DCE6F1"
WHITE = "#FFFFFF"


def F(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def fit_image(path: Path, w: int, h: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    return ImageOps.contain(img, (w, h), Image.LANCZOS)


def draw_card(canvas: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int,
              w: int, h: int, image: Path | None, title: str, spec1: str,
              spec2: str, role: str, tag: str, accent: str = TEAL) -> None:
    # shadow + card
    draw.rounded_rectangle((x + 6, y + 8, x + w + 6, y + h + 8), radius=18, fill="#E8EDF3")
    draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=WHITE, outline=BORDER, width=2)

    img_x, img_y, img_w, img_h = x + 24, y + 24, w - 48, 300
    draw.rounded_rectangle((img_x, img_y, img_x + img_w, img_y + img_h), radius=12, fill="#FBFCFF", outline="#EDF2F7", width=1)
    if image is not None and image.exists():
        im = fit_image(image, img_w - 24, img_h - 24)
        canvas.paste(im, (img_x + (img_w - im.width) // 2, img_y + (img_h - im.height) // 2))
    else:
        # simple system icon for the connection card
        cx, cy = img_x + img_w // 2, img_y + img_h // 2
        for i, (label, color) in enumerate([("风扇", PALE), ("小主机", TEAL), ("HDD", ORANGE), ("UPS", "#C9A227")]):
            bw, bh = 190, 38
            bx = cx - bw // 2
            by = cy - 90 + i * 48
            draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=8, fill=color, outline="white", width=2)
            draw.text((bx + 12, by + 8), label, font=F(20, True), fill=WHITE if color != PALE else NAVY)
        draw.text((cx + 110, cy - 36), "2.5GbE\n→ 训练端", font=F(18), fill=GRAY, spacing=4)

    # tag
    tw = draw.textlength(tag, font=F(18, True))
    draw.rounded_rectangle((x + w - tw - 26, y + 14, x + w - 12, y + 44), radius=10, fill="#FFF7E6", outline="#F0D9A8", width=1)
    draw.text((x + w - tw - 19, y + 19), tag, font=F(18, True), fill="#B7791F")

    draw.text((x + 26, y + 340), title, font=F(32, True), fill=NAVY)
    draw.text((x + 26, y + 392), spec1, font=F(24), fill=GRAY)
    draw.text((x + 26, y + 432), spec2, font=F(22), fill=GRAY)

    # role pill
    pw = draw.textlength(role, font=F(20, True)) + 28
    draw.rounded_rectangle((x + 26, y + 486, x + 26 + pw, y + 522), radius=18, fill=LIGHT, outline=PALE, width=1)
    draw.text((x + 40, y + 492), role, font=F(20, True), fill=accent)


def main() -> None:
    canvas = Image.new("RGB", (2400, 1600), "#F7FAFD")
    draw = ImageDraw.Draw(canvas)

    draw.text((55, 38), "硬件参考套件（示意）", font=F(54, True), fill=NAVY)
    draw.text((55, 108), "Beelink EQ12 + 2TB NVMe + 16TB HDD + APC UPS + ESP32-S3 + 120mm PWM",
              font=F(26), fill=GRAY)
    draw.rounded_rectangle((2000, 42, 2340, 94), radius=16, fill="#F0F7F4", outline="#B7E0CD", width=2)
    draw.text((2022, 52), "reference kit", font=F(24, True), fill=TEAL)

    gap, card_w, card_h = 30, 743, 590
    x0, y0 = 55, 170
    cards = [
        (HW / "intel_nuc.jpg", "x86 小主机（同级示意）", "Beelink EQ12 · N100 · 16GB · 双 2.5GbE",
         "M.2 2280 + 2.5\" SATA 位", "计算 / 网络", "同级示意", TEAL),
        (HW / "samsung_980pro.jpg", "2TB NVMe（同级示意）", "Lexar NQ790 · PCIe 4.0 · M.2 2280",
         "热层：最近会话 / 待交付", "热层", "同级示意", ORANGE),
        (HW / "toshiba_hdd.jpg", "16TB HDD（同级示意）", "IronWolf Pro · CMR · 3.5\" · 7200 rpm",
         "冷层：已交付 / 归档；ORICO 7688U3 · 12V/2A", "冷层", "同级示意", ORANGE),
        (HW / "apc_ups.jpg", "APC Back-UPS 650VA", "600VA 级 · 后备式",
         "掉电保护：小主机 + HDD", "供电", "同级示意", "#B7791F"),
        (HW / "esp32_s3.jpg", "ESP32-S3-DevKitC-1", "温度 / 风扇 / 电流",
         "USB telemetry → dashboard", "健康监控", "DevKit 示意", TEAL),
        (None, "系统连接", "SATA→USB 3.0（UASP）", "NVMe 热 / HDD 冷 / UPS / ESP32",
         "整机装配", "reference design", TEAL),
    ]
    for i, (img, title, spec1, spec2, role, tag, accent) in enumerate(cards):
        r, c = divmod(i, 3)
        x = x0 + c * (card_w + gap)
        y = y0 + r * (card_h + gap)
        draw_card(canvas, draw, x, y, card_w, card_h, img, title, spec1, spec2, role, tag, accent)

    draw.line((55, 1450, 2345, 1450), fill=BORDER, width=2)
    draw.text((55, 1470), "产品图：Wikimedia Commons（CC0、CC BY-SA）；同级产品仅作示意。",
              font=F(20), fill=GRAY)
    draw.text((55, 1505), "最终型号、价格与接口以 BOM 和实际采购为准；HDD 为已有 / 可选。",
              font=F(20), fill=GRAY)

    canvas.save(OUT, quality=95)
    print("saved", OUT)


if __name__ == "__main__":
    main()

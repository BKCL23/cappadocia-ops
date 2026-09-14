#!/usr/bin/env python3
"""Generate a KDP ebook cover (1600x2560) for the Cappadocia guide.
Rights-clean original artwork: sunrise gradient + hot-air balloons + fairy chimneys.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import math, random

random.seed(7)
W, H = 1600, 2560

# ---- editable text ----
TITLE = "CAPPADOCIA"
SUBTITLE = "THE COMPLETE TRAVELER’S GUIDE"
TAGLINE = "FAIRY CHIMNEYS  ·  HOT-AIR BALLOONS  ·  CAVE HOTELS  ·  HIDDEN VALLEYS"
BYLINE = "WRITTEN BY A CAPPADOCIA HOTEL OWNER"

SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SANS_R = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"

def font(path, size):
    return ImageFont.truetype(path, size)

# ---------- sky gradient ----------
stops = [
    (0.00, (34, 22, 60)),    # deep plum (title sits here)
    (0.22, (78, 34, 82)),
    (0.40, (150, 58, 92)),
    (0.56, (216, 96, 84)),
    (0.70, (240, 150, 92)),
    (0.82, (255, 206, 150)),  # horizon glow
    (0.90, (240, 178, 120)),
    (1.00, (150, 96, 66)),    # ground haze
]
def lerp(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))
def sky_color(fy):
    for i in range(len(stops)-1):
        y0, c0 = stops[i]; y1, c1 = stops[i+1]
        if y0 <= fy <= y1:
            return lerp(c0, c1, (fy-y0)/(y1-y0))
    return stops[-1][1]

img = Image.new("RGB", (W, H))
px = img.load()
for y in range(H):
    c = sky_color(y/H)
    for x in range(W):
        px[x, y] = c

draw = ImageDraw.Draw(img, "RGBA")

# ---------- sun glow near horizon ----------
glow = Image.new("RGBA", (W, H), (0,0,0,0))
gd = ImageDraw.Draw(glow)
gx, gy = int(W*0.5), int(H*0.80)
for rad, a in [(720, 26), (520, 34), (340, 50), (200, 70), (110, 110)]:
    gd.ellipse([gx-rad, gy-rad, gx+rad, gy+rad], fill=(255, 236, 200, a))
glow = glow.filter(ImageFilter.GaussianBlur(60))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")

# ---------- fairy chimneys (tall tapering rock cones) ----------
def chimney(d, x, base_y, height, width, color, cap=False):
    tip = max(4.0, width*0.14)              # narrow rounded tip
    top_y = base_y - height
    # tapering body
    d.polygon([(x-width/2, base_y), (x+width/2, base_y),
               (x+tip, top_y), (x-tip, top_y)], fill=color)
    d.ellipse([x-tip, top_y-tip, x+tip, top_y+tip], fill=color)   # round the tip
    if cap:                                  # signature caprock
        cw = width*0.30
        d.ellipse([x-cw, top_y-cw*0.75, x+cw, top_y+cw*0.35], fill=color)

# far ridge (hazy, lighter)
far = Image.new("RGBA", (W, H), (0,0,0,0))
fd = ImageDraw.Draw(far)
base_far = int(H*0.865)
xf = -20
while xf < W+40:
    hgt = random.randint(110, 220); wdt = random.randint(40, 74)
    chimney(fd, xf, base_far, hgt, wdt, (120, 82, 74, 190), cap=random.random() < 0.35)
    xf += random.randint(54, 92)
far = far.filter(ImageFilter.GaussianBlur(3))
img = Image.alpha_composite(img.convert("RGBA"), far).convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")

# near ridge (dark, crisp) — clustered, overlapping cones
base_near = int(H*0.935)
xn = -30
near_color = (44, 27, 20, 255)
while xn < W+50:
    hgt = random.randint(200, 380); wdt = random.randint(66, 128)
    chimney(draw, xn, base_near, hgt, wdt, near_color, cap=random.random() < 0.4)
    xn += random.randint(66, 116)
# solid ground base
draw.rectangle([0, base_near-4, W, H], fill=(38, 23, 17, 255))

# ---------- hot-air balloons ----------
combos = [
    [(214,69,65),(242,201,76)], [(64,145,163),(240,240,235)],
    [(120,81,169),(242,201,76)], [(226,114,52),(247,238,214)],
    [(46,110,140),(214,69,65)], [(212,84,120),(250,244,230)],
    [(70,150,110),(242,201,76)], [(230,150,50),(120,81,169)],
]
def draw_balloon(base, cx, cy, r, combo, alpha=255):
    Wb, Hb = int(r*2.2), int(r*3.05)
    layer = Image.new("RGBA", (Wb, Hb), (0,0,0,0))
    mask = Image.new("L", (Wb, Hb), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([int(Wb*0.04), 0, int(Wb*0.96), int(Hb*0.72)], fill=255)
    md.polygon([(int(Wb*0.22), int(Hb*0.52)), (int(Wb*0.78), int(Hb*0.52)),
                (Wb//2, int(Hb*0.80))], fill=255)
    ld = ImageDraw.Draw(layer)
    nst = 10
    for i in range(nst):
        c = combo[i % len(combo)]
        ld.rectangle([int(Wb*i/nst), 0, int(Wb*(i+1)/nst), Hb], fill=(c[0], c[1], c[2], 255))
    # shade lower half for volume
    shade = Image.new("RGBA", (Wb, Hb), (0,0,0,0))
    sd = ImageDraw.Draw(shade)
    sd.rectangle([0, int(Hb*0.4), Wb, Hb], fill=(0,0,0,45))
    layer = Image.alpha_composite(layer, shade)
    # sheen highlight
    sh = Image.new("RGBA", (Wb, Hb), (0,0,0,0))
    shd = ImageDraw.Draw(sh)
    shd.ellipse([int(Wb*0.14), int(Hb*0.06), int(Wb*0.5), int(Hb*0.42)], fill=(255,255,255,60))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    layer = Image.alpha_composite(layer, sh)
    # apply silhouette mask (scaled by alpha)
    m = mask.point(lambda p: p * alpha // 255)
    layer.putalpha(ImageChops.multiply(layer.split()[3], m))
    # basket + lines
    bd = ImageDraw.Draw(layer)
    bx0, bx1 = int(Wb*0.42), int(Wb*0.58); by = int(Hb*0.90)
    bd.line([(int(Wb*0.30), int(Hb*0.70)), (bx0, by)], fill=(60,40,25,alpha), width=max(1,int(r*0.03)))
    bd.line([(int(Wb*0.70), int(Hb*0.70)), (bx1, by)], fill=(60,40,25,alpha), width=max(1,int(r*0.03)))
    bd.rectangle([bx0, by, bx1, int(Hb*0.95)], fill=(96,60,32,alpha))
    base.alpha_composite(layer, (int(cx-Wb/2), int(cy-Hb/2)))

base = img.convert("RGBA")
# (cx_frac, cy_frac, radius, alpha) — kept out of the title zone (top ~32%)
balloons = [
    (0.30, 0.42, 30, 150), (0.68, 0.40, 26, 140), (0.50, 0.46, 34, 160),
    (0.16, 0.50, 40, 180), (0.83, 0.49, 38, 175), (0.40, 0.55, 52, 205),
    (0.62, 0.57, 58, 215), (0.24, 0.62, 66, 230), (0.78, 0.63, 62, 230),
    (0.50, 0.66, 80, 245), (0.36, 0.72, 92, 255), (0.66, 0.73, 88, 255),
    (0.14, 0.70, 60, 235), (0.88, 0.71, 56, 235), (0.50, 0.79, 104, 255),
    (0.22, 0.80, 74, 255), (0.80, 0.81, 70, 255),
]
for i, (fx, fy, r, a) in enumerate(balloons):
    draw_balloon(base, fx*W, fy*H, r, combos[i % len(combos)], a)
img = base.convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")

# ---------- vignette ----------
vig = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(vig)
vd.rectangle([0,0,W,H], fill=0)
vd.ellipse([-int(W*0.25), -int(H*0.15), int(W*1.25), int(H*1.15)], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(220))
dark = Image.new("RGB", (W, H), (18, 10, 26))
img = Image.composite(img, dark, vig)
draw = ImageDraw.Draw(img, "RGBA")

# ---------- text helpers ----------
def tracked_width(text, fnt, tracking):
    w = 0
    for ch in text:
        w += draw.textlength(ch, font=fnt) + tracking
    return w - tracking if text else 0

def draw_tracked(cx, y, text, fnt, tracking, fill, shadow=None):
    total = tracked_width(text, fnt, tracking)
    x = cx - total/2
    for ch in text:
        cw = draw.textlength(ch, font=fnt)
        if shadow:
            sc, off = shadow
            draw.text((x+off, y+off), ch, font=fnt, fill=sc)
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += cw + tracking

CREAM = (255, 247, 233)
GOLD = (233, 195, 108)
SHADOW = ((10, 6, 20, 170), 5)

# soft dark plate behind title for guaranteed legibility
plate = Image.new("RGBA", (W, H), (0,0,0,0))
pd = ImageDraw.Draw(plate)
pd.rectangle([0, int(H*0.045), W, int(H*0.30)], fill=(20, 12, 34, 70))
plate = plate.filter(ImageFilter.GaussianBlur(40))
img = Image.alpha_composite(img.convert("RGBA"), plate).convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")

# Title
title_f = font(SANS_B, 176)
draw_tracked(W/2, int(H*0.085), TITLE, title_f, 6, CREAM, SHADOW)
# gold rule
rule_w = int(W*0.34)
ry = int(H*0.205)
draw.rectangle([W/2 - rule_w/2, ry, W/2 + rule_w/2, ry+5], fill=GOLD)
# small diamond accents
for dx in (-rule_w/2, rule_w/2):
    draw.polygon([(W/2+dx, ry-9), (W/2+dx+11, ry+2), (W/2+dx, ry+13), (W/2+dx-11, ry+2)], fill=GOLD)
# Subtitle
sub_f = font(SANS_R, 52)
draw_tracked(W/2, int(H*0.225), SUBTITLE, sub_f, 8, CREAM, ((10,6,20,150), 3))

# Tagline near lower third
tag_f = font(SANS_R, 33)
draw_tracked(W/2, int(H*0.905), TAGLINE, tag_f, 3, (255, 240, 220), ((10,6,20,150), 2))
# Byline at bottom
by_f = font(SERIF_I, 44)
bw = draw.textlength(BYLINE, font=by_f)
draw.text((W/2 - bw/2 + 3, int(H*0.945)+3), BYLINE, font=by_f, fill=(10,6,20,160))
draw.text((W/2 - bw/2, int(H*0.945)), BYLINE, font=by_f, fill=GOLD)

img.save("cover.png", "PNG")
# also a JPG (KDP accepts either) and a small preview
img.save("Cappadocia-Cover.jpg", "JPEG", quality=92)
img.resize((400, 640), Image.LANCZOS).save("cover-thumb.jpg", "JPEG", quality=90)
print("wrote cover.png / Cappadocia-Cover.jpg (%dx%d) + cover-thumb.jpg" % (W, H))

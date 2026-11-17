"""Animated letter / quiz graphics for the family letters series. Each function writes an MP4 (1280x720, 30 fps, no audio)."""
import math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SC = "/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad"
FB = f"{SC}/fonts/Cairo-ExtraBold.ttf"; FT = f"{SC}/fonts/Lalezar.ttf"; FE = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H, FPS = 1280, 720, 30
GOLD, CREAM, INK, GREEN, RED, BLUE = "#F6B93B", "#FFF6E5", "#3B2A1A", "#2ECC71", "#E74C3C", "#3498DB"

def ease(t): return 1 - (1 - t) ** 3
def bounce(t):
    if t < 1/2.75: return 7.5625*t*t
    if t < 2/2.75: t -= 1.5/2.75; return 7.5625*t*t + .75
    if t < 2.5/2.75: t -= 2.25/2.75; return 7.5625*t*t + .9375
    t -= 2.625/2.75; return 7.5625*t*t + .984375

_bg = None
def background():
    global _bg
    if _bg is None:
        im = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(im)
        for y in range(H):  # soft warm gradient
            c = int(255 - 18*y/H); d.line((0, y, W, y), fill=(255, c - 6, c - 30))
        for x in range(0, W + 60, 60):          # playful dots pattern
            for y in range(0, H + 60, 60):
                o = 30 if (y // 60) % 2 else 0
                d.ellipse((x + o - 4, y - 4, x + o + 4, y + 4), fill=(250, 220, 170))
        _bg = im
    return _bg.copy()

def emoji(ch, size):
    f = ImageFont.truetype(FE, 109); im = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((70, 70), ch, font=f, anchor="mm", embedded_color=True)
    return im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)

def writer(out, n):
    return subprocess.Popen(["ffmpeg","-nostdin","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
                             "-frames:v",str(n),"-c:v","libx264","-crf","18","-pix_fmt","yuv420p",out], stdin=subprocess.PIPE)

def txt(d, xy, s, size, fill, font=FB, stroke=0, sf=INK, anchor="mm"):
    d.text(xy, s, font=ImageFont.truetype(font, size), anchor=anchor, fill=fill, stroke_width=stroke, stroke_fill=sf, direction="rtl")

# ---------------- letter build: dotless shape, then dots drop in ----------------
BASE = {"ب": "ٮ", "ت": "ٮ", "ث": "ٮ", "ن": "ں"}
DOTS = {"ب": [("below", 0)], "ت": [("above", -1), ("above", 1)], "ث": [("above", -1), ("above", 1), ("top", 0)], "ن": [("above", 0)]}
def letter_build(letter, dur, out, caption=None, color=BLUE):
    n = int(dur * FPS); w = writer(out, n)
    f = ImageFont.truetype(FT, 420); base = BASE[letter]
    probe = Image.new("L", (W, H)); ImageDraw.Draw(probe).text((W//2, H//2 + 10), base, font=f, anchor="mm", fill=255, direction="rtl")
    x0, y0, x1, y1 = probe.getbbox(); cx = (x0 + x1) / 2; r = 26; gap = 16
    if letter == "ن": cx = (x0 + x1) / 2 + 6
    dots = DOTS[letter]
    def pos(kind, k):
        if kind == "below": return (cx + k*2.4*r, y1 + gap + r)
        if kind == "above": return (cx + k*1.25*r, y0 - gap - r)
        return (cx, y0 - gap - 3.2*r)
    for i in range(n):
        t = i / FPS; im = background(); d = ImageDraw.Draw(im)
        s = ease(min(1, t / 0.5)); sz = int(420 * (0.6 + 0.4*s))
        txt(d, (W//2, H//2 + 10), base, sz, color, font=FT, stroke=10, sf="white")
        for k, (kind, off) in enumerate(dots):
            st = 0.8 + 0.55*k; p = (t - st) / 0.6
            if p <= 0 or s < 1: continue
            px, py = pos(kind, off); yy = -120 + (py + 120) * bounce(min(1, p))
            d.ellipse((px - r, yy - r, px + r, yy + r), fill=RED, outline="white", width=6)
        if caption and t > 0.8 + 0.55*len(dots) + 0.4:
            txt(d, (W//2, H - 70), caption, 54, INK)
        w.stdin.write(im.tobytes())
    w.stdin.close(); w.wait()

# ---------------- word card: big emoji + word, first letter highlighted ----------------
def word_card(emj, word, dur, out, note=None):
    n = int(dur * FPS); w = writer(out, n); e = emoji(emj, 300)
    for i in range(n):
        t = i / FPS; im = background(); d = ImageDraw.Draw(im); s = ease(min(1, t / 0.4))
        ee = e.resize((max(1, int(300*s)), max(1, int(300*s)))); im.paste(ee, (W//2 - ee.width//2, 230 - ee.height//2), ee)
        if t > 0.3:
            f = ImageFont.truetype(FT, 150); y = 520
            d.text((W//2, y), word, font=f, anchor="mm", fill=INK, direction="rtl")
            right = W//2 + d.textlength(word, font=f, direction="rtl") / 2
            d.text((right, y), word[0] + "‍", font=f, anchor="rm", fill=RED, direction="rtl")   # first letter in red
        if note and t > 0.9: txt(d, (W//2, 665), note, 40, "#7A5C3A")
        w.stdin.write(im.tobytes())
    w.stdin.close(); w.wait()

# ---------------- choice question with countdown ----------------
def choice_quiz(question, options, correct, dur, out, count_at=None):
    """options: list of (emoji or None, label). Countdown 3-2-1 starts at count_at (s), reveal at count_at+3."""
    n = int(dur * FPS); w = writer(out, n); count_at = count_at if count_at is not None else max(0.8, dur - 4.2)
    es = [emoji(e, 170) if e else None for e, _ in options]
    for i in range(n):
        t = i / FPS; im = background(); d = ImageDraw.Draw(im, "RGBA")
        txt(d, (W//2, 85), question, 50, INK)
        k = len(options); cw = 300; gap = 60; x0 = W//2 - (k*cw + (k-1)*gap)//2
        reveal = t >= count_at + 3
        for j, ((e, lab), em) in enumerate(zip(options, es)):
            a = ease(min(1, max(0, (t - 0.15*j) / 0.35)))
            x = x0 + (k - 1 - j)*(cw + gap); y = 190 + int(40*(1 - a))   # RTL: first option on the right
            ok = reveal and j == correct; dim = reveal and j != correct
            d.rounded_rectangle((x, y, x+cw, y+330), 36, fill=(255, 255, 255, 235 if not dim else 120),
                                outline=GREEN if ok else (230, 200, 160), width=14 if ok else 6)
            if em: im.paste(em, (x + cw//2 - 85, y + 30), em)
            txt(d, (x + cw//2, y + (270 if em else 165)), lab, 64 if em else 120, INK if not dim else (150, 140, 130), font=FT)
            if ok:
                d.ellipse((x+cw-70, y-30, x+cw+20, y+60), fill=GREEN)
                d.line([(x+cw-48, y+15), (x+cw-30, y+35), (x+cw-2, y-8)], fill="white", width=10, joint="curve")
        if count_at <= t < count_at + 3:
            num = 3 - int(t - count_at); p = (t - count_at) % 1
            rr = 70 + 18*(1 - p); d.ellipse((W//2 - rr, 620 - rr, W//2 + rr, 620 + rr), fill=GOLD, outline="white", width=8)
            txt(d, (W//2, 615), str(num), 90, "white", font=FT)
        w.stdin.write(im.tobytes())
    w.stdin.close(); w.wait()

# ---------------- riddle answer reveal: question mark, countdown, then emoji + word ----------------
def riddle(emj, word, dur, out, count_at=None):
    n = int(dur * FPS); w = writer(out, n); count_at = count_at if count_at is not None else max(0.6, dur - 4.4); e = emoji(emj, 330)
    for i in range(n):
        t = i / FPS; im = background(); d = ImageDraw.Draw(im)
        if t < count_at + 3:
            s = 1 + 0.05*math.sin(t*6)
            txt(d, (W//2, 300), "؟", int(330*s), GOLD, font=FT, stroke=12, sf="white")
            txt(d, (W//2, 80), "حزّورة!", 60, INK, font=FT)
            if t >= count_at:
                num = 3 - int(t - count_at); txt(d, (W//2, 610), str(num), 120, RED, font=FT, stroke=8, sf="white")
        else:
            p = ease(min(1, (t - count_at - 3) / 0.4)); ee = e.resize((max(1, int(330*p)), max(1, int(330*p))))
            im.paste(ee, (W//2 - ee.width//2, 260 - ee.height//2), ee)
            f = ImageFont.truetype(FT, 140); y = 560
            d.text((W//2, y), word, font=f, anchor="mm", fill=INK, direction="rtl")
            right = W//2 + d.textlength(word, font=f, direction="rtl") / 2
            d.text((right, y), word[0] + "‍", font=f, anchor="rm", fill=RED, direction="rtl")
        w.stdin.write(im.tobytes())
    w.stdin.close(); w.wait()

# ---------------- locks: 4 padlocks, unlock index u animates ----------------
LOCKS = ["ب", "ت", "ث", "ن"]
def padlock(d, cx, cy, letter_shown, open_p, glow=0):
    sh = int(55 * open_p)
    d.arc((cx - 55, cy - 125 - sh, cx + 55, cy - 15 - sh), 180, 360, fill="#8E8E8E", width=22)
    d.line((cx - 55, cy - 70 - sh, cx - 55, cy - 40), fill="#8E8E8E", width=22)
    if open_p < 0.2: d.line((cx + 55, cy - 70 - sh, cx + 55, cy - 40), fill="#8E8E8E", width=22)
    d.rounded_rectangle((cx - 85, cy - 45, cx + 85, cy + 115), 26, fill=GOLD, outline="#B9770E", width=8)
    txt(d, (cx, cy + 32), letter_shown, 120, INK, font=FT)
    if glow:
        for k in range(8):
            a = k*math.pi/4; r1, r2 = 110 + 30*glow, 140 + 60*glow
            d.line((cx + r1*math.cos(a), cy + 30 + r1*math.sin(a), cx + r2*math.cos(a), cy + 30 + r2*math.sin(a)), fill=GOLD, width=8)
def locks(opened_before, unlock, dur, out):
    n = int(dur * FPS); w = writer(out, n)
    for i in range(n):
        t = i / FPS; im = background(); d = ImageDraw.Draw(im)
        txt(d, (W//2, 80), "صندوق النقاط", 64, INK, font=FT)
        for j, L in enumerate(LOCKS):
            cx = 230 + j*273; cy = 380
            if j < opened_before: padlock(d, cx, cy, L, 1)
            elif j == unlock:
                p = ease(min(1, max(0, (t - 0.5) / 0.6)))
                padlock(d, cx, cy, L if p > 0.3 else BASE[L], p, glow=(p if p < 1 else max(0, 1 - (t - 1.1)*1.5)))
            else: padlock(d, cx, cy, BASE[L], 0)
        w.stdin.write(im.tobytes())
    w.stdin.close(); w.wait()

def title_card(title, sub, dur, out, bg_img=None):
    n = int(dur * FPS); w = writer(out, n)
    base = Image.open(bg_img).convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(6)) if bg_img else background()
    if bg_img: base = Image.eval(base, lambda p: int(p*0.6))
    for i in range(n):
        t = i / FPS; im = base.copy(); d = ImageDraw.Draw(im); s = ease(min(1, t / 0.5))
        txt(d, (W//2, H//2 - 60), title, int(120*(0.7 + 0.3*s)), "#FFD54A", font=FT, stroke=10, sf="#3a1d05")
        if t > 0.4: txt(d, (W//2, H//2 + 85), sub, 70, "white", font=FT, stroke=8, sf="#3a1d05")
        w.stdin.write(im.tobytes())
    w.stdin.close(); w.wait()

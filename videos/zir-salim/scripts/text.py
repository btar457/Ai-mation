"""طبقات النص الشفافة 1080x1920 للفيديو (RAQM + RTL)."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
AMIRI = "fonts/Amiri-Bold.ttf"
CAIRO = "fonts/Cairo.ttf"
WHITE = (255, 255, 255)
GOLD = (240, 190, 110)
CX, MAXW = 490, 800  # منتصف منطقة النص الآمنة وعرضها


def font(path, size, weight=None):
    f = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    if weight and path == CAIRO:
        try:
            f.set_variation_by_axes([0, weight])
        except Exception:
            pass
    return f


def wrap(draw, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f, direction="rtl") <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_block(img, lines, f, y, colors, gap=1.25, shadow=10):
    """lines: list[str]; colors: list per line. Returns bottom y."""
    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_layer)
    d = ImageDraw.Draw(img)
    lh = int(f.size * gap)
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=f, direction="rtl")
        x = CX - tw / 2
        sd.text((x, y + i * lh + 4), line, font=f, fill=(0, 0, 0, 230), direction="rtl")
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow))
    img.alpha_composite(shadow_layer)
    img.alpha_composite(shadow_layer)
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=f, direction="rtl")
        x = CX - tw / 2
        d.text((x, y + i * lh), line, font=f, fill=colors[i] + (255,), direction="rtl")
    return y + len(lines) * lh


def label(path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f = font(CAIRO, 34, 700)
    d = ImageDraw.Draw(img)
    t = "حكايات من التاريخ"
    tw = d.textlength(t, font=f, direction="rtl")
    x = CX - tw / 2
    d.rounded_rectangle((x - 26, 238, x + tw + 26, 296), 29, fill=(0, 0, 0, 120), outline=GOLD + (200,), width=2)
    d.text((x, 240), t, font=f, fill=GOLD + (255,), direction="rtl")
    img.save(path)


def title(path, lines, colors=None, size=78, y=345):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(AMIRI, size)
    out = []
    for ln in lines:
        out += wrap(d, ln, f, MAXW)
    colors = colors or [WHITE] * len(out)
    if len(colors) < len(out):
        colors = colors + [colors[-1]] * (len(out) - len(colors))
    draw_block(img, out, f, y, colors)
    img.save(path)


def verse(path, hemistichs, colors, size=70, y=360, faded=None):
    """البيت: كل شطر في سطر. faded: فهارس الأشطر التي تُرسم شبه شفافة."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(AMIRI, size)
    lh = int(size * 1.55)
    for i, h in enumerate(hemistichs):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_block(layer, [h], f, y + i * lh, [colors[i]])
        if faded and i in faded:
            a = layer.getchannel("A").point(lambda v: int(v * 0.0))
            layer.putalpha(a)
        img.alpha_composite(layer)
    img.save(path)


def caption(path, text, size=50, y=1240):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(AMIRI, size)
    lines = wrap(d, text, f, MAXW)
    draw_block(img, lines, f, y, [WHITE] * len(lines), gap=1.35, shadow=8)
    img.save(path)

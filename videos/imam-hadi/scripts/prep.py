"""يجهّز الصور (تكبير 1080x1920 + قص) وخرائط العمق (Depth Anything V2) وملف film/data.js من جدول اللقطات."""
import json, os, sys
from PIL import Image, ImageEnhance, ImageFilter
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "scripts")
from lines import POEM
OUT = "film/assets/img"; os.makedirs(OUT, exist_ok=True)

# اقتصاصات مشتقة (للقطات الشخصيات الناقصة مؤقتاً): (المصدر، x0، y0، العرض كنسبة)
CROPS = {"H1c": ("H1", .36, .30, .64), "H1i": ("H1", .0, .12, .58), "S5c": ("S5", .22, .30, .62), "S3c": ("S3", .30, .25, .62)}
# جدول اللقطات: (الصورة، البداية، الحركة، خيارات)
T = [
 ("H1", 0.0, "push", dict(flick=.6, glow=[.37, .42, .07])),
 ("H2", 4.1, "in", {}), ("H3", 7.6, "left", dict(flick=.8)), ("H2", 12.0, "out", {}),
 ("S1", 13.4, "in", dict(flick=.8)), ("S2", 17.1, "push", dict(flick=.7)), ("S3", 23.4, "in", dict(dust=.9)),
 ("S4", 28.6, "push", dict(flick=.5)), ("S5", 30.3, "in", dict(glow=[.52, .47, .075], dust=.7)),
 ("S5c", 36.2, "orbit", dict(glow=[.535, .29, .12], dust=.7)), ("S7", 42.8, "right", dict(flick=.5)),
 ("S3c", 46.6, "left", dict(dust=.8)), ("S9", 50.8, "push", dict(flick=.6)), ("H1c", 52.1, "in", dict(flick=.7)),
 ("H1", 55.7, "orbit", dict(flick=.6, glow=[.37, .42, .07])), ("H1i", 59.91, "push", dict(glow=[.62, .55, .11])),
 ("H1i", 62.6, "out", dict(glow=[.62, .55, .11])), ("S2", 65.14, "in", dict(flick=.7)),
 ("S5c", 72.18, "in", dict(glow=[.535, .29, .12])), ("S2", 75.83, "push", dict(flick=.9)), ("H3", 79.50, "in", dict(flick=.6)),
 ("P1", 81.07, "up", dict(dust=.4)), ("P2", 90.12, "in", dict(dust=.9)), ("P3", 98.88, "push", dict(dust=.8)),
 ("P4", 107.50, "left", dict(dust=.5)), ("P5", 115.92, "push", dict(dust=.8)), ("P6", 124.29, "out", dict(dust=.7)),
 ("S1", 132.79, "out", dict(flick=.8)), ("H1c", 138.79, "push", dict(flick=.5, bright=.9)), ("E3", 147.98, "right", dict(flick=.6)),
 ("H2", 149.78, "in", {}), ("E5", 152.58, "in", dict(dust=.6, warm=1)),
]

def src_path(i):
    for ext in ("png", "jpg"):
        if os.path.exists(f"images/{i}.{ext}"): return f"images/{i}.{ext}"

def load(i):
    if i in CROPS:
        s, x0, y0, w = CROPS[i]; im = load(s); W, H = im.size
        cw = int(W * w); ch = int(cw * 16 / 9); x = int(W * x0); y = min(int(H * y0), H - ch)
        return im.crop((x, y, x + cw, y + ch))
    p = src_path(i)
    if not p: return None
    im = Image.open(p).convert("RGB")
    if p.endswith(".jpg"): im = im.crop((0, 0, im.width, int(im.height * .92)))   # علامة Pollinations
    return im

def fit(im):
    s = max(1080 / im.width, 1920 / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - 1080) // 2, (im.height - 1920) // 2
    return ImageEnhance.Sharpness(im.crop((l, t, l + 1080, t + 1920))).enhance(1.25)

from transformers import pipeline
import sys as _s
if "--data-only" in _s.argv:
    pass
dp = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device="cpu")
ids = sorted(set(x[0] for x in T)); missing = []
for i in ids:
    im = load(i)
    if im is None: missing.append(i); continue
    big = fit(im); big.save(f"{OUT}/{i}.jpg", quality=92)
    d = dp(big.resize((540, 960)))["depth"].convert("L").filter(ImageFilter.GaussianBlur(2.5))
    d.save(f"{OUT}/{i}_d.png"); print("prep", i, flush=True)
if missing: sys.exit(f"missing images: {missing}")

tl = json.load(open("timeline.json"))
shots = []
for k, (img, a, m, o) in enumerate(T):
    b = T[k + 1][1] if k + 1 < len(T) else tl["duration"]
    shots.append({"img": img, "a": a, "b": b, "m": m, **o})
open("film/data.js", "w").write("const DATA = " + json.dumps({"duration": tl["duration"], "shots": shots, "words": tl["words"],
                                 "poem": POEM}, ensure_ascii=False) + ";\n")
print("data.js ok", len(shots), "shots")

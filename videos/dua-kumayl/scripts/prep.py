"""يجهّز الصور (تكبير 1080x1920 + قص) وخرائط العمق (Depth Anything V2) وملف film/data.js من جدول اللقطات."""
import json, os, sys
from PIL import Image, ImageEnhance, ImageFilter
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "scripts")
OUT = "film/assets/img"; os.makedirs(OUT, exist_ok=True)

# اقتصاصات مشتقة (للقطات الشخصيات الناقصة مؤقتاً): (المصدر، x0، y0، العرض كنسبة)
CROPS = {"B2c": ("B2", .30, .32, .70), "B3c": ("B3", .22, .22, .56), "B4c": ("B4", .18, .28, .62), "B8": ("B1_old", .22, .45, .56), "B6c": ("B6", .0, .30, .70), "B6d": ("B6", .0, .40, .58)}
# جدول اللقطات: (الصورة، البداية، الحركة، خيارات)
T = [
 ("B1", ("hook", 0.0), "push", dict(bright=1.08, dust=.6, shake=.3)),
 ("B15", ("hook", 4.6), "in", dict(dust=.8)),
 ("B2", ("intro", 0.0), "left", dict(flick=.8)), ("B2c", ("intro", 4.6), "in", dict(flick=.8)),
 ("B3", ("pass", 0.0), "in", dict(glow=[.50, .43, .05], rays=.3)), ("B4", ("pass", 3.6), "push", dict(flick=.5)),
 ("B12", ("ask", 0.0), "orbit", dict(rays=.3, dust=.4)),
 ("B13", ("girl", 0.0), "push", dict(shake=.4)),
 ("B3c", ("answer", 0.0), "push", dict(glow=[.50, .40, .09], rays=.5)),
 ("B11", ("inside", 0.0), "in", dict(flick=.7)),
 ("B5", ("run", 0.0), "push", dict(flick=.4, desat=.2)), ("B9", ("run", 3.6), "push", dict(shake=.5, flick=.4)),
 ("B10", ("run", 5.6), "in", dict(dust=.6)),
 ("B6c", ("bishr", 0.0), "push", dict(rays=.6, warm=1)),
 ("B6d", ("repent", 0.0), "in", dict(rays=.5, warm=1)), ("B7", ("repent", 4.2), "in", dict(dust=.5, warm=1)),
 ("B14", ("end", 0.0), "in", dict(rays=.4, dust=.4, warm=1)),
]

FALLBACK = {}
def src_path(i):
    for ext in ("png", "jpg"):
        if os.path.exists(f"images/{i}.{ext}"): return f"images/{i}.{ext}"

def load(i):
    if i in CROPS:
        s, x0, y0, w = CROPS[i]; im = load(s); W, H = im.size
        cw = int(W * w); ch = int(cw * 16 / 9); x = int(W * x0); y = min(int(H * y0), H - ch)
        return im.crop((x, y, x + cw, y + ch))
    p = src_path(i)
    if not p and i in FALLBACK:
        print("FALLBACK", i, "->", FALLBACK[i], flush=True); return load(FALLBACK[i])
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
SEG = {x["tag"]: x for x in tl["segments"]}
def at(anc):
    tag, off = anc
    seg = SEG[tag]
    return round(min(seg["start"] + off, seg["end"] - 0.3) if off > 0 else seg["start"] + off, 3)
T = [(img, at(anc), m, o) for img, anc, m, o in T]
for k, (img, a, m, o) in enumerate(T):
    b = T[k + 1][1] if k + 1 < len(T) else tl["duration"]
    shots.append({"img": img, "a": a, "b": b, "m": m, **{k: v for k, v in o.items() if v is not None}})
open("film/data.js", "w").write("const DATA = " + json.dumps({"duration": tl["duration"], "shots": shots, "words": tl["words"], "segments": tl["segments"],
                                 }, ensure_ascii=False) + ";\n")
print("data.js ok", len(shots), "shots")

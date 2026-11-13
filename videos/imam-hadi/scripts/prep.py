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
 ("H1", ("hook", 0.0), "push", dict(flick=.6, glow=[.37, .42, .07])),
 ("H2", ("intro", -0.06), "in", {}), ("H3", ("intro", 3.44), "left", dict(flick=.8)), ("H2", ("intro", 7.84), "out", {}),
 ("S1", ("story", 1.37), "in", dict(flick=.8)), ("S2", ("story", 5.07), "push", dict(flick=.7)), ("S3", ("story", 11.37), "in", dict(dust=.9)),
 ("S4", ("story", 16.57), "push", dict(flick=.5, shake=.5)), ("S5", ("story", 18.27), "in", dict(glow=[.52, .47, .075], dust=.7, rays=.4)),
 ("S5c", ("story", 24.17), "orbit", dict(glow=[.535, .29, .12], dust=.7, rays=.5)), ("S7", ("story", 30.77), "right", dict(flick=.5)),
 ("S3c", ("story", 34.57), "left", dict(dust=.8)), ("S9", ("story", 38.77), "push", dict(flick=.6)),
 ("S10", ("story", 40.07), "in", dict(flick=.8)),
 ("S11", ("story", 43.67), "orbit", dict(flick=.6)),
 ("S12", ("refuse", 0.0), "push", dict(rays=.4)),
 ("H1i", ("refuse", 3.4), "out", dict(glow=[.62, .55, .11], rays=.3)),
 ("H1c", ("ask_r", 0.0), "in", dict(flick=.7)), ("S2", ("ask", 0.0), "push", dict(flick=.7)),
 ("S5c", ("little", 0.0), "in", dict(glow=[.535, .29, .12], rays=.5)),
 ("S2", ("insist", 0.0), "push", dict(flick=.9, shake=1.0)), ("R2", ("insist_r", 0.0), "in", dict(flick=.6)),
 ("P1", ("v1", 0.0), "up", dict(dust=.4, desat=.3, rays=.4, fade=1)), ("R2", ("v1", 5.4), "in", dict(desat=.25, flick=.4)),
 ("P2", ("v2", 0.0), "in", dict(dust=.9, desat=.35)),
 ("P3", ("v3", 0.0), "push", dict(dust=.8, desat=.35, rays=.3)), ("R1", ("v3", 5.6), "push", dict(desat=.3, flick=.4)),
 ("P4", ("v4", 0.0), "left", dict(dust=.5, desat=.4)), ("P5", ("v5", 0.0), "push", dict(dust=.8, desat=.45, rays=.3)),
 ("P6", ("v6", 0.0), "out", dict(dust=.7, desat=.45)), ("R1", ("v6", 4.6), "push", dict(desat=.35, flick=.3)),
 ("R2", ("end", 0.0), "out", dict(flick=.6, desat=.2)),
 ("E2", ("end", 5.65), "push", dict(flick=.4, desat=.25, bright=.95)),
 ("E1", ("end", 12.25), "in", dict(flick=.4, desat=.2)),
 ("E3", ("end", 15.2), "right", dict(flick=.6, dim=1)),
 ("E4", ("end", 17.0), "in", dict(rays=.6, glow=None)),
 ("E5", ("end", 19.8), "in", dict(dust=.6, warm=1)),
]

FALLBACK = {"E2": "H1c", "E1": "S1", "R1": "S2", "R2": "S1", "S10": "H1c", "S11": "H1", "S12": "H1i", "E4": "H2"}
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
                                 "poem": POEM}, ensure_ascii=False) + ";\n")
print("data.js ok", len(shots), "shots")

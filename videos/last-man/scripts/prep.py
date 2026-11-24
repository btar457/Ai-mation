"""يجهّز الصور (تكبير 1080x1920 + قص) وخرائط العمق (Depth Anything V2) وملف film/data.js من جدول اللقطات."""
import json, os, sys
from PIL import Image, ImageEnhance, ImageFilter
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "scripts")
OUT = "film/assets/img"; os.makedirs(OUT, exist_ok=True)

# اقتصاصات مشتقة: (المصدر، x0، y0، العرض كنسبة)
CROPS = {"L7c": ("L7", .30, .48, .50), "L1c": ("L1", .20, .22, .62), "L12c": ("L12", .25, .20, .55)}
# جدول اللقطات: (الصورة، (الجملة، الإزاحة)، الحركة، خيارات)
T = [
 ("L1", ("l1", 0.0), "push", dict(shake=.35, dust=.5)), ("L1c", ("l1", 1.5), "orbit", dict(dust=.5)),
 ("L2", ("l2", 0.0), "in", dict(dust=.3)),
 ("L3", ("l3", 0.0), "push", dict(dust=.2)),
 ("L4", ("l4", 0.0), "left", dict(dust=.4)),
 ("L5", ("l5", 0.0), "in", dict(dust=.4)), ("L6", ("l5", 1.9), "right", dict(dust=.3)),
 ("L7c", ("l6", 0.0), "orbit", dict(dust=.9)),
 ("L8", ("l7", 0.0), "push", dict(dust=.2)),
 ("L9", ("l8", 0.0), "push", dict(shake=.7, dust=.6)),
 ("L10", ("l9", 0.0), "in", dict(dust=.3, desat=.2)),
 ("L11", ("l10", 0.0), "push", dict(shake=.6, warm=.5)),
 ("L12", ("l11", 0.0), "orbit", dict(warm=.6)),
 ("L12c", ("l12", 0.0), "push", dict(warm=.3, desat=.35)),
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

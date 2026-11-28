"""توحيد لون الصور (دوتون طيني نحاسي) وقص اللوح من خلفيته السوداء."""
import numpy as np
from PIL import Image, ImageFilter

STOPS = [(0.0, (16, 10, 7)), (0.45, (122, 64, 34)), (0.75, (205, 138, 82)), (1.0, (246, 230, 202))]

def duotone(lum):
    out = np.zeros(lum.shape + (3,))
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        m = (lum >= a) & (lum <= b)
        t = ((lum - a) / (b - a))[..., None]
        out[m] = (np.array(ca) * (1 - t) + np.array(cb) * t)[m]
    return out

def grade(src, dst, mix=0.62, keep_green=False):
    im = np.asarray(Image.open(src).convert("RGB")).astype(float)
    lum = (0.299 * im[..., 0] + 0.587 * im[..., 1] + 0.114 * im[..., 2]) / 255
    out = im * (1 - mix) + duotone(lum) * mix
    if keep_green:  # لون الصدأ الأخضر يبقى خارج التدرج عمداً: علامة النحاس الرديء
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        green = np.clip((g - r) / 40 + (b - r) / 60, 0, 1)[..., None]
        out = out * (1 - green) + im * green
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst, quality=92)

for k in "NEBMU":
    grade(f"img/{k}.png", f"deck/assets/img/{k}.jpg")
grade("img/I.png", "deck/assets/img/I.jpg", keep_green=True)

# اللوح: قناع من الإضاءة على الخلفية السوداء
t = Image.open("img/T.png").convert("RGB")
a = np.asarray(t).astype(float)
lum = a.max(axis=2)
mask = Image.fromarray((np.clip((lum - 18) / 22, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
grade("img/T.png", "/tmp/claude-0/-home-user-Ai-mation/03064949-7577-5614-8fb0-795e8fa54ba0/scratchpad/Tg.jpg", mix=0.35)
tg = Image.open("/tmp/claude-0/-home-user-Ai-mation/03064949-7577-5614-8fb0-795e8fa54ba0/scratchpad/Tg.jpg").convert("RGBA")
tg.putalpha(mask)
tg = tg.crop(tg.getbbox())
tg.save("deck/assets/img/T.png")
print(tg.size)

"""تدرّج لوني واحد لكل الصور: ظلال زرقاء مخضرّة وإضاءة كهرمانية (ليل ألف ليلة)."""
import sys, os
import numpy as np
from PIL import Image

def grade(src, dst, mix=0.45):
    im = np.asarray(Image.open(src).convert("RGB")).astype(float) / 255
    lum = 0.299 * im[..., 0] + 0.587 * im[..., 1] + 0.114 * im[..., 2]
    shadow = np.array([0.05, 0.16, 0.20])   # أزرق مخضر
    light = np.array([1.00, 0.72, 0.38])    # كهرماني
    w = np.clip((lum - 0.15) / 0.6, 0, 1)[..., None]
    tone = (shadow * (1 - w) + light * w) * (0.35 + lum[..., None] * 1.1)
    out = im * (1 - mix) + np.clip(tone, 0, 1) * mix
    out = np.clip((out - 0.5) * 1.08 + 0.5, 0, 1)  # تباين خفيف
    Image.fromarray((out * 255).astype(np.uint8)).save(dst, quality=93)

keys = sys.argv[1].split(",") if len(sys.argv) > 1 else [f[:-4] for f in os.listdir("img") if f.endswith(".png")]
for k in keys:
    grade(f"img/{k}.png", f"film/assets/img/{k}.jpg")
    print("graded", k)

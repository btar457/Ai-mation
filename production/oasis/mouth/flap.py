"""Free audio-driven jaw flap for a still cartoon crop.
python3 flap.py base.jpg line.wav out.mp4
"""
import sys, subprocess, numpy as np, math
from PIL import Image, ImageDraw, ImageFilter

base_p, wav, out = sys.argv[1:4]
FPS = 30
# --- character rig (Rahhal, crop 11) ---
CURVE = [(818, 476), (850, 497), (885, 513), (920, 524), (955, 531), (985, 534)]   # closed-mouth smile line
JAW = CURVE + [(1000, 545), (990, 562), (955, 572), (905, 566), (860, 545), (825, 505)]  # lower jaw region under the line
MAXD = 30                       # max jaw drop in px
EYE = (710, 422, 58, 50)        # cx, cy, rx, ry for blink
SKIN = (226, 170, 105)

# --- audio envelope ---
raw = subprocess.run(["ffmpeg","-nostdin","-v","error","-i",wav,"-ac","1","-ar","48000","-f","s16le","-"], capture_output=True).stdout
a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
hop = 48000 // FPS
n = math.ceil(len(a) / hop) + 6
rms = np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop]**2)) if i*hop < len(a) else 0 for i in range(n)])
rms = np.convolve(rms, [0.25, 0.5, 0.25], mode="same")
lvl = np.clip(rms / (np.percentile(rms[rms > 0], 90) + 1e-6), 0, 1)
lvl = np.where(lvl < 0.12, 0, lvl)
q = np.round(lvl * 3) / 3          # 4 classic mouth positions

base = Image.open(base_p).convert("RGB")
W, H = base.size
jaw_mask = Image.new("L", (W, H), 0); ImageDraw.Draw(jaw_mask).polygon(JAW, fill=255)
jaw_mask = jaw_mask.filter(ImageFilter.GaussianBlur(1.2))
jaw = base.copy()

p = subprocess.Popen(["ffmpeg","-nostdin","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
                      "-i",wav,"-vf","scale=1280:720:flags=lanczos,format=yuv420p","-c:v","libx264","-crf","18","-c:a","aac","-shortest",out],
                     stdin=subprocess.PIPE)
for i in range(n):
    d = int(q[i] * MAXD)
    fr = base.copy(); dr = ImageDraw.Draw(fr)
    if d > 0:
        lower = [(x + d*0.15*(k/len(CURVE)), y + d) for k, (x, y) in enumerate(CURVE)]
        mouth = CURVE + lower[::-1]
        dr.polygon(mouth, fill=(70, 22, 26))                                   # mouth interior
        tx = sum(x for x, _ in lower)/len(lower); ty = max(y for _, y in lower) - d*0.35
        dr.ellipse((tx-28, ty-d*0.25, tx+34, ty+d*0.3), fill=(214, 92, 104))   # tongue
        fr.paste(jaw.crop((0, 0, W, H)), (int(d*0.15), d), jaw_mask)           # dropped lower jaw over it
    # blink every ~3.2 s for 3 frames
    if i % 96 in (0, 1, 2) and i > 10:
        cx, cy, rx, ry = EYE; k = [0.6, 1.0, 0.6][i % 96]
        dr.ellipse((cx-rx, cy-ry, cx+rx, cy-ry + 2*ry*k), fill=SKIN)
    # tiny head bob with speech
    s = 1 + 0.012*q[i] + 0.004*math.sin(i/9)
    if s != 1:
        z = fr.resize((int(W*s), int(H*s)), Image.BILINEAR); ox, oy = (z.width-W)//2, int((z.height-H)*0.7)
        fr = z.crop((ox, oy, ox+W, oy+H))
    p.stdin.write(fr.tobytes())
p.stdin.close(); p.wait(); print("ok", out, n, "frames")

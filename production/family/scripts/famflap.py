import sys, os, subprocess, math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
FPS = 30
C = "/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad/fam/crops"
RIGS = {
 "boy": dict(img=f"{C}/boy.jpg", curve=[(664,486),(700,496),(740,497),(774,486)], jaw=34, maxd=24, eye=None, eyes=[(654,376,40,38),(824,376,40,38)], search=12),
 "gm":  dict(img=f"{C}/gm.jpg",  curve=[(680,365),(720,378),(760,380),(800,368)], jaw=34, maxd=22, eye=None, search=12),
 "gp":  dict(img=f"{C}/gp.jpg",  curve=[(685,396),(725,404),(770,405),(815,395)], jaw=40, maxd=22, eye=None, search=12),
}
def envelope(wav, start):
    raw = subprocess.run(["ffmpeg","-nostdin","-v","error","-ss",str(start),"-i",wav,"-ac","1","-ar","48000","-f","s16le","-"], capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    hop = 48000 // FPS; n = max(1, math.ceil(len(a) / hop))
    rms = np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop]**2)) if i*hop < len(a) else 0 for i in range(n)])
    rms = np.convolve(rms, [0.25, 0.5, 0.25], mode="same")
    nz = rms[rms > 0]; ref = np.percentile(nz, 90) if len(nz) else 1
    lvl = np.clip(rms / (ref + 1e-6), 0, 1); lvl = np.where(lvl < 0.12, 0, lvl)
    return np.round(lvl * 3) / 3

def snap(rig, base):
    """Find the drawn mouth line (darkest pixel per column near the rig curve); return xs, line ys, line thickness."""
    C = rig["curve"]; W, H = base.size
    g = np.asarray(base.convert("L")).astype(np.float32)
    g = (g + np.roll(g, 1, 1) + np.roll(g, -1, 1)) / 3
    xs = np.arange(int(C[0][0]), min(W - 1, int(C[-1][0])) + 1)
    yc = np.interp(xs, [p[0] for p in C], [p[1] for p in C]).astype(int)
    R = rig.get("search", 22); ys = []; th = []
    for x, y in zip(xs, yc):
        lo, hi = max(0, y - R), min(H - 1, y + R)
        col = g[lo:hi, x]; k = int(np.argmin(col)); ys.append(lo + k)
        thr = col[k] + 35; t = 1
        while k + t < len(col) and col[k + t] < thr and t < 10: t += 1
        th.append(t)
    ys = np.array(ys, dtype=float)
    ys = np.array([np.median(ys[max(0, i-6):i+7]) for i in range(len(ys))])      # smooth
    ys = np.convolve(np.pad(ys, 4, mode="edge"), np.ones(9)/9, mode="valid")
    return xs, ys.astype(int), int(np.median(th)) + 1

def frame(rig, base, jaw_img, jaw_mask, q, i, punch):
    W, H = base.size; C = rig["curve"]; d = q * rig["maxd"]
    arr = np.asarray(base).copy()
    if d > 0.5:
        xs, ys, th = rig["_snap"]
        t = (xs - xs[0]) / max(1, xs[-1] - xs[0])
        off = (d * np.sin(np.pi * t) ** 0.8).astype(int)
        J = rig["jaw"]; src = np.asarray(jaw_img)
        for x, y, o, tt in zip(xs, ys, off, t):
            if o <= 0: continue
            top = y - th // 2                                   # opening starts on the drawn line itself
            seg = src[top + th:top + th + J, x].copy()          # lower jaw below the line (line not duplicated)
            dst = top + th + o
            n = min(len(seg), H - dst)
            if n > 0: arr[dst:dst + n, x] = seg[:n]
            arr[top:top + th + o, x] = (60, 18, 22)             # mouth interior replaces the old line
            if 0.28 < tt < 0.72 and o > 4:
                tl = max(1, int(o * 0.45)); arr[top + th + o - tl:top + th + o, x] = (214, 92, 104)
            arr[top + th + o:top + th + o + 2, x] = (40, 12, 14)  # lower lip edge
        fr = Image.fromarray(arr)
    else:
        fr = base.copy()
    dr = ImageDraw.Draw(fr)
    eyes = rig.get("eyes") or ([rig["eye"]] if rig.get("eye") else [])
    if eyes and i % 96 in (0, 1, 2) and i > 10:
        k = [0.6, 1.0, 0.6][i % 96]
        for cx, cy, rx, ry in eyes:
            skin = base.getpixel((cx, max(0, cy - ry - 10)))
            dr.ellipse((cx-rx, cy-ry, cx+rx, cy-ry + 2*ry*k), fill=skin)
    s = punch * (1 + 0.012*q + 0.004*math.sin(i/9))
    z = fr.resize((int(W*s), int(H*s)), Image.BILINEAR)
    cx = (C[0][0] + C[-1][0]) / 2 * s; ox = int(min(max(0, cx - W/2), z.width - W)) if punch > 1 else (z.width-W)//2
    oy = int((z.height-H)*0.6)
    return z.crop((ox, oy, ox+W, oy+H))

def prep(rig):
    base = Image.open(rig["img"]).convert("RGB"); W, H = base.size; C = rig["curve"]
    poly = C + [(x, y + rig["jaw"]) for x, y in C[::-1]]
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    rig["_snap"] = snap(rig, base)
    return base, base.copy(), m.filter(ImageFilter.GaussianBlur(1.2))


def render(rig_name, wav, out, punch=1.0, start=0.0):
    rig = RIGS[rig_name]; base, ji, jm = prep(rig); q = envelope(wav, start); W, H = base.size
    p = subprocess.Popen(["ffmpeg","-nostdin","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
                          "-vf","scale=1280:720:flags=lanczos,setsar=1,format=yuv420p","-c:v","libx264","-crf","18","-an",out], stdin=subprocess.PIPE)
    for i in range(len(q)): p.stdin.write(frame(rig, base, ji, jm, q[i], i, punch).tobytes())
    p.stdin.close(); p.wait()

def check(out):
    tiles = []
    for n, rig in RIGS.items():
        base, ji, jm = prep(rig); fr = frame(rig, base, ji, jm, 0.67, 5, 1.0)
        x0 = max(0, rig["curve"][0][0]-200); y0 = max(0, rig["curve"][0][1]-200)
        tiles.append(fr.crop((x0, y0, x0+500, y0+340)).resize((400, 272)))
    s = Image.new("RGB", (1200, 272)); [s.paste(t, (i*400, 0)) for i, t in enumerate(tiles)]; s.save(out)

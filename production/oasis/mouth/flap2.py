"""Free audio-driven jaw flap for still cartoon crops, driven by a rig per crop.
python3 flap2.py check            -> one wide-open frame per rig (contact sheet)
python3 flap2.py render           -> render every job in JOBS to ../lip/flap/
"""
import sys, os, subprocess, math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
SC = "/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad"
L = f"{SC}/lip"; OUT = f"{L}/flap"; os.makedirs(OUT, exist_ok=True)
FPS = 30
# curve = closed mouth line (left->right), jaw = thickness of the lower jaw below the line, maxd = max drop, eye=(cx,cy,rx,ry) or None
RIGS = {
 "r01": dict(img=f"{L}/crops/01.jpg", curve=[(852,322),(900,348),(948,363),(990,366)], jaw=42, maxd=26, eye=(760,264,36,34)),
 "r09": dict(img=f"{L}/crops/09.jpg", curve=[(838,486),(885,512),(935,530),(980,536)], jaw=44, maxd=28, eye=(734,420,38,36)),
 "r14": dict(img=f"{L}/crops/14.jpg", curve=[(1175,432),(1220,458),(1265,478),(1310,486)], jaw=44, maxd=28, eye=(1080,362,36,34)),
 "r19": dict(img=f"{L}/crops/19.jpg", curve=[(858,294),(900,318),(942,332),(982,336)], jaw=40, maxd=26, eye=(764,234,36,34)),
 "r20": dict(img=f"{L}/crops/20.jpg", curve=[(787,263),(840,300),(895,322),(950,326)], jaw=40, maxd=26, eye=(720,204,32,34)),
 "r24": dict(search=7, img=f"{L}/crops/24.jpg", curve=[(870,353),(935,378),(975,388),(1035,378)], jaw=36, maxd=22, eye=(824,320,26,26)),
 "r26": dict(img=f"{L}/crops/26.jpg", curve=[(715,343),(780,395),(835,423),(900,418)], jaw=42, maxd=26, eye=(640,308,34,34)),
 "r31": dict(img=f"{L}/crops/31.jpg", curve=[(875,393),(915,420),(960,437),(1008,444)], jaw=40, maxd=26, eye=(770,328,30,30)),
 "r33": dict(img=f"{L}/crops/33.jpg", curve=[(895,238),(965,275),(1010,295),(1100,291)], jaw=50, maxd=32, eye=(790,164,40,40)),
 "h05": dict(img=f"{L}/crops/05.jpg", curve=[(770,388),(805,400),(845,402),(875,390)], jaw=26, maxd=20, eye=None),
 "h06": dict(img=f"{L}/crops/06.jpg", curve=[(722,530),(755,545),(790,548),(825,536)], jaw=30, maxd=22, eye=None),
 "h15": dict(img=f"{L}/crops/15.jpg", curve=[(606,292),(636,305),(670,308),(712,296)], jaw=28, maxd=20, eye=None),
 "h27": dict(img=f"{L}/crops/27.jpg", curve=[(830,238),(865,255),(905,258),(945,245)], jaw=30, maxd=22, eye=None),
 "h30": dict(img=f"{L}/crops/30.jpg", curve=[(633,431),(665,446),(705,449),(745,436)], jaw=28, maxd=20, eye=None),
 "h34": dict(img=f"{L}/crops/34.jpg", curve=[(430,288),(490,320),(570,325),(640,295)], jaw=40, maxd=28, eye=None),
 "s23": dict(search=5, img=f"{L}/sh/crop_23.jpg", curve=[(730,383),(775,393),(820,393),(850,383)], jaw=30, maxd=16, eye=None),
 "s32": dict(search=5, img=f"{L}/sh/crop_32.jpg", curve=[(668,280),(705,290),(745,292),(790,284)], jaw=60, maxd=22, eye=None),
}
# line -> (rig, start second in the line audio, punch-in zoom)
JOBS = {
 "11": ("r09", 0, 1.0), "14": ("r14", 0, 1.0), "16": ("r14", 0, 1.08), "19": ("r19", 0, 1.0), "20": ("r20", 0, 1.0),
 "24": ("r24", 0, 1.0), "26": ("r26", 0, 1.0), "28": ("r26", 0, 1.08), "31": ("r31", 0, 1.0), "33": ("r33", 0, 1.0),
 "12": ("h06", 0, 1.08), "15": ("h15", 0, 1.0), "27": ("h27", 0, 1.0), "29": ("h27", 0, 1.08), "30": ("h30", 0, 1.0), "34": ("h34", 0, 1.0),
 "23": ("s23", 0, 1.0), "25": ("s23", 0, 1.08),
 # remainders after a LongCat clip that stopped at 5 s
 "01_r": ("r01", 5.0, 1.12), "09_r": ("r09", 5.0, 1.12), "05_r": ("h05", 5.0, 1.12), "08_r": ("h06", 5.0, 1.12),
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
    if rig["eye"] and i % 96 in (0, 1, 2) and i > 10:
        cx, cy, rx, ry = rig["eye"]; k = [0.6, 1.0, 0.6][i % 96]
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

if sys.argv[1] == "check":
    tiles = []
    for name, rig in RIGS.items():
        base, ji, jm = prep(rig); fr = frame(rig, base, ji, jm, 0.67, 5, 1.0)
        x0 = max(0, rig["curve"][0][0]-220); y0 = max(0, rig["curve"][0][1]-170)
        t = fr.crop((x0, y0, x0+440, y0+300)).resize((330, 225)); ImageDraw.Draw(t).text((4,4), name, fill="yellow"); tiles.append(t)
    s = Image.new("RGB", (330*6, 225*3))
    for i, t in enumerate(tiles): s.paste(t, ((i % 6)*330, (i//6)*225))
    s.save(f"{SC}/mouth/check.jpg", quality=85); print("ok")
else:
    only = sys.argv[2:]
    for job, (rn, start, punch) in JOBS.items():
        if only and job not in only: continue
        l = job.split("_")[0]; wav = f"{SC}/tts/full/line_{l}.wav"; out = f"{OUT}/{job}.mp4"
        rig = RIGS[rn]; base, ji, jm = prep(rig); q = envelope(wav, start); W, H = base.size
        p = subprocess.Popen(["ffmpeg","-nostdin","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
                              "-vf","scale=1280:720:flags=lanczos,setsar=1,format=yuv420p","-c:v","libx264","-crf","18","-an",out], stdin=subprocess.PIPE)
        for i in range(len(q)): p.stdin.write(frame(rig, base, ji, jm, q[i], i, punch).tobytes())
        p.stdin.close(); p.wait(); print("ok", job, round(len(q)/FPS, 2), "s", flush=True)

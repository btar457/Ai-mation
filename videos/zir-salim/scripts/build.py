"""تركيب الفيديو النهائي: معالجة كل لقطة، ثم الدمج مع النصوص والصوت."""
import os
import subprocess
import sys
from PIL import Image
from plan import SHOTS, CAPTIONS, END, S

W, H, FPS = 1080, 1920, 30
os.makedirs("shots", exist_ok=True)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])


def gradient(path):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = g.load()
    for y in range(820):
        a = int(235 * (1 - y / 820) ** 1.6)
        for x in range(W):
            px[x, y] = (0, 0, 0, a)
    # تعتيم خفيف أسفل الصورة ليقرأ النص المكتوب فوق منطقة الوصف
    for y in range(1150, 1500):
        a = int(110 * min(1, (y - 1150) / 120) * min(1, (1500 - y) / 120))
        for x in range(W):
            px[x, y] = (0, 0, 0, a)
    g.save(path)


if not os.path.exists("txt/grad.png"):
    gradient("txt/grad.png")

FLASH_WHITE = {"reveal1", "reveal2"}
TEXT_AT = {"hook": 0.25, "name": 0.6, "verse_half": 0.2, "verse_q": 0.0, "verse_gaps": 0.2,
           "reveal1": 0.35, "reveal2": 0.35, "end": 3.3}

for n, (clip, a, b, off, txt, cs) in enumerate(SHOTS):
    out = f"shots/{n:02d}.mp4"
    if os.path.exists(out) and "--force" not in sys.argv:
        continue
    D = b - a
    avail = 5.06 - cs
    stretch = max(1.0, D / avail)  # إبطاء المقطع بدل تجميد الإطارات
    zoom_frames = int(D * FPS)
    zdir = n % 2 == 0
    z = f"1+0.05*on/{zoom_frames}" if zdir else f"1.05-0.05*on/{zoom_frames}"
    flash = "white" if txt in FLASH_WHITE else "black"
    fd = 0.3 if flash == "white" else 0.13
    vf = (f"[0:v]trim=start={cs},setpts=(PTS-STARTPTS)*{stretch:.4f},"
          f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:vsbmc=1,"
          f"scale=-2:{H}:flags=lanczos,crop={W}:{H},"
          f"pad={W}:{H + off}:0:{off}:black,crop={W}:{H}:0:0,unsharp=5:5:0.6,"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
          f"trim=duration={D:.3f}[bg];"
          f"[1:v]format=rgba[g];[bg][g]overlay=0:0[v0]")
    inputs = ["-i", f"clips/{clip}.mp4", "-loop", "1", "-t", f"{D:.3f}", "-i", "txt/grad.png"]
    last = "v0"
    extra = []
    if txt:
        extra.append((f"txt/{txt}.png", TEXT_AT[txt]))
    if txt == "verse_q":
        extra.append(("txt/q.png", 1.0))
    for i, (png, st) in enumerate(extra, start=2):
        inputs += ["-loop", "1", "-t", f"{D:.3f}", "-i", png]
        vf += f";[{i}:v]format=rgba,fade=t=in:st={st}:d=0.5:alpha=1[t{i}];[{last}][t{i}]overlay=0:0[v{i}]"
        last = f"v{i}"
    vf += f";[{last}]fade=t=in:st=0:d={fd}:color={flash},format=yuv420p[out]"
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", vf, "-map", "[out]",
         "-r", str(FPS), "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-t", f"{D:.3f}", out])
    print("shot", n, clip, f"{D:.2f}s", f"x{stretch:.2f}", flush=True)

if "--shots-only" in sys.argv:
    sys.exit()

# الدمج النهائي
with open("shots/list.txt", "w") as f:
    for n in range(len(SHOTS)):
        f.write(f"file '{n:02d}.mp4'\n")
run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "shots/list.txt", "-c", "copy", "concat.mp4"])

inputs = ["-i", "concat.mp4", "-i", "audio_final.wav", "-loop", "1", "-t", f"{END}", "-i", "txt/label.png"]
fc = "[2:v]format=rgba,fade=t=in:st=0.2:d=0.6:alpha=1[lb];[0:v][lb]overlay=0:0[c0]"
last = "c0"
for k, (i0, i1, _) in enumerate(CAPTIONS):
    st, en = max(0.0, S[i0][0] - 0.1), S[i1][1] + 0.25
    idx = 3 + k
    inputs += ["-loop", "1", "-t", f"{END}", "-i", f"txt/cap{k:02d}.png"]
    fc += (f";[{idx}:v]format=rgba,fade=t=in:st={st:.2f}:d=0.25:alpha=1,"
           f"fade=t=out:st={en - 0.25:.2f}:d=0.25:alpha=1[k{k}];[{last}][k{k}]overlay=0:0:"
           f"enable='between(t,{st:.2f},{en:.2f})'[c{k + 1}]")
    last = f"c{k + 1}"
fc += f";[{last}]fade=t=out:st={END - 0.8}:d=0.8,format=yuv420p[vout]"
run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fc, "-map", "[vout]", "-map", "1:a",
     "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
     "-movflags", "+faststart", "-t", f"{END}", "final.mp4"])
print("final.mp4 done")

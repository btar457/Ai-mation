"""Wan clips for Shaheen's lines (and the closing night shot), tight crops, chained for lines > 5 s.
python3 shaheen.py crops | gen
"""
import os, sys, shutil, subprocess, time
from PIL import Image, ImageDraw
SC = "/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad"
EP = "/home/user/Ai-mation/docs/oasis-team/ep01"
L = f"{SC}/lip"; os.makedirs(f"{L}/sh", exist_ok=True)
sys.path.insert(0, f"{SC}/tts/full")
from lines import LINES
TAG = {lid: tag.split(",")[0] for _, (_, ls) in LINES.items() for lid, tag, _ in ls}
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
SPEC = {  # line: image, cx, cy, zoom
 "04": ("s03", 0.46, 0.40, 3.0), "21": ("s10", 0.69, 0.47, 2.3), "22": ("s10", 0.69, 0.47, 2.3),
 "23": ("s10", 0.69, 0.47, 2.3), "25": ("s10", 0.69, 0.47, 2.3), "32": ("s13", 0.50, 0.42, 3.1),
 "35": ("s14", 0.55, 0.55, 1.5),
}
TALK = ("close-up of the cartoon falcon with the teal satchel talking {e}, his beak opening and closing as he speaks, "
        "gentle head movement, wings resting at his sides, no other characters speak, smooth Pixar-style 3D animation, stable character")
EXTRA = {"36": ("s14", "the night sky over the desert oasis, a glowing golden shape twinkles among the stars, stars twinkling, the falcon on the palm branch gazes up in wonder, smooth Pixar-style 3D animation")}

def crop(img, fx, fy, z, out):
    im = Image.open(f"{EP}/{img}.jpg"); w, h = im.size; cw, ch = int(w/z), int(h/z)
    x = min(max(0, int(fx*w - cw/2)), w-cw); y = min(max(0, int(fy*h - ch/2)), h-ch)
    im.crop((x, y, x+cw, y+ch)).resize((w, h), Image.LANCZOS).save(out, quality=95)

def last_frame(video, out):
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-sseof","-0.1","-i",video,"-frames:v","1","-q:v","2",out], check=True)

if sys.argv[1] == "crops":
    ims = []
    for l, sp in SPEC.items():
        crop(*sp, f"{L}/sh/crop_{l}.jpg"); ims.append(Image.open(f"{L}/sh/crop_{l}.jpg").resize((400, 221)))
    s = Image.new("RGB", (400*4, 221*2))
    for i, im in enumerate(ims): s.paste(im, ((i % 4)*400, (i//4)*221))
    s.save(f"{L}/sh_crops.jpg", quality=85); print("ok")
else:
    from gradio_client import Client, handle_file
    c = Client('zerogpu-aoti/wan2-2-fp8da-aoti-faster', verbose=False)
    todo = [(l, f"{L}/sh/crop_{l}.jpg", TALK.format(e=TAG[l])) for l in SPEC] + [(l, f"{EP}/{v[0]}.jpg", v[1]) for l, v in EXTRA.items()]
    only = sys.argv[2:]
    for l, src, prompt in todo:
        if only and l not in only: continue
        need = dur(f"{SC}/tts/full/line_{l}.wav") + 0.4
        k = 0
        while need > 0.3:
            out = f"{L}/sh/{l}_{k}.mp4"
            if not os.path.exists(out):
                d = round(min(5.0, max(1.5, need)), 2)
                try:
                    r = c.submit(input_image=handle_file(src), prompt=prompt, steps=6, duration_seconds=d, seed=42,
                                 randomize_seed=False, api_name='/generate_video').result(timeout=300)
                    shutil.copy(r[0], out); print("ok", l, k, d, flush=True)
                except Exception as e:
                    print("FAIL", l, k, str(e)[:200], flush=True)
                    if "quota" in str(e).lower(): print("STOP", flush=True); sys.exit(0)
                    break
            need -= dur(out)
            if need > 0.3:
                src = f"{L}/sh/{l}_{k}_last.jpg"; last_frame(out, src)   # continue from the last frame, same speaker
            k += 1
    print("DONE", flush=True)

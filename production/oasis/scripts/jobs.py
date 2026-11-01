"""LongCat lip-sync jobs for Rahhal and Hasat lines, plus Wan jobs for Shaheen.
python3 jobs.py crops   -> make crops + contact sheet
python3 jobs.py lc      -> generate LongCat clips (skip existing, stop on quota)
"""
import os, sys, json, shutil, time
from PIL import Image, ImageDraw
SC = "/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad"
EP = "/home/user/Ai-mation/docs/oasis-team/ep01"
L = f"{SC}/lip"; os.makedirs(f"{L}/crops", exist_ok=True); os.makedirs(f"{L}/clips", exist_ok=True)

# line: (image, center x, center y, zoom)
RAHHAL = {
 "01": ("s01", 0.48, 0.36, 1.9), "03": ("s03", 0.21, 0.40, 2.0), "09": ("s04", 0.16, 0.33, 2.4), "11": ("s04", 0.16, 0.33, 2.4),
 "14": ("s06", 0.19, 0.33, 2.4), "16": ("s06", 0.19, 0.33, 2.4), "19": ("s08", 0.48, 0.38, 1.9),
 "20": ("s09", 0.50, 0.40, 1.8), "24": ("s10", 0.27, 0.36, 2.2), "26": ("s11b", 0.33, 0.36, 2.4),
 "28": ("s11b", 0.33, 0.36, 2.4), "31": ("s12", 0.18, 0.36, 2.4), "33": ("s13", 0.24, 0.36, 2.5),
}
HASAT = {
 "05": ("s03", 0.80, 0.52, 2.0), "06": ("s04", 0.87, 0.40, 2.4), "07": ("s04", 0.87, 0.40, 2.4), "08": ("s04", 0.87, 0.40, 2.4),
 "10": ("s04", 0.87, 0.40, 2.4), "12": ("s04", 0.87, 0.40, 2.4), "15": ("s06", 0.84, 0.58, 2.4),
 "27": ("s11", 0.50, 0.50, 1.6), "29": ("s11", 0.50, 0.50, 1.6), "30": ("s12", 0.84, 0.45, 2.4),
 "34": ("s13", 0.77, 0.45, 2.5),
}
P_R = "A cute cartoon baby camel with a red headband speaks {e}, his mouth moving with the words, lively head movement, 3D animation style."
P_H = "A gentle old cartoon tortoise with round glasses speaks {e}, her mouth moving with the words, calm head movement, 3D animation style."
sys.path.insert(0, f"{SC}/tts/full")
from lines import LINES
TAG = {lid: tag.split(",")[0] for _, (_, ls) in LINES.items() for lid, tag, _ in ls}

def crop(img, fx, fy, z, out):
    im = Image.open(f"{EP}/{img}.jpg"); w, h = im.size; cw, ch = int(w/z), int(h/z)
    x = min(max(0, int(fx*w - cw/2)), w-cw); y = min(max(0, int(fy*h - ch/2)), h-ch)
    im.crop((x, y, x+cw, y+ch)).resize((w, h), Image.LANCZOS).save(out, quality=95)

def jobs():
    js = []
    for d, p in ((RAHHAL, P_R), (HASAT, P_H)):
        for l, (img, fx, fy, z) in d.items():
            js.append(dict(id=l, crop=f"{L}/crops/{l}.jpg", spec=(img, fx, fy, z), prompt=p.format(e=TAG[l])))
    return sorted(js, key=lambda j: j["id"])

if sys.argv[1] == "crops":
    js = jobs(); ims = []
    for j in js:
        crop(*j["spec"], j["crop"]); ims.append((j["id"], Image.open(j["crop"]).resize((340, 188))))
    s = Image.new("RGB", (340*6, 188*((len(ims)+5)//6))); d = ImageDraw.Draw(s)
    for i, (k, im) in enumerate(ims):
        x, y = (i % 6)*340, (i//6)*188; s.paste(im, (x, y)); d.rectangle((x, y, x+30, y+16), fill="black"); d.text((x+4, y+2), k, fill="yellow")
    s.save(f"{L}/crops_sheet.jpg", quality=85); print(len(js), "crops")
elif sys.argv[1] == "lc2":
    # chunked generation: every line split into <=4.9 s audio pieces at word gaps; piece k>0 starts from the last frame of piece k-1
    import subprocess, json as _j
    from gradio_client import Client, handle_file
    WT = _j.load(open(f"{SC}/tts/full/word_times.json"))
    def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
    def bounds(l):
        D = dur(f"{SC}/tts/full/line_{l}.wav"); cuts = [0.0]
        if os.path.exists(f"{L}/clips/lc_{l}.mp4"): cuts.append(min(D, dur(f"{L}/clips/lc_{l}.mp4")))  # existing first piece
        while D - cuts[-1] > 5.0:
            gaps = [ (a+b)/2 for (_, a), (b, _) in zip(WT[l], WT[l][1:]) if cuts[-1]+1.5 < (a+b)/2 <= cuts[-1]+4.9 ]
            cuts.append(max(gaps) if gaps else cuts[-1]+4.9)
        cuts.append(D); return cuts
    os.makedirs(f"{L}/achunks", exist_ok=True)
    c = Client('victor/LongCat-Video-Avatar-1.5', verbose=False)
    for j in jobs():
        l = j["id"]; b = bounds(l)
        for k in range(len(b)-1):
            out = f"{L}/clips/lc_{l}.mp4" if k == 0 else f"{L}/clips/lc_{l}_{k}.mp4"
            if os.path.exists(out): continue
            wav = f"{L}/achunks/{l}_{k}.wav"
            subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-ss",f"{b[k]:.3f}","-to",f"{b[k+1]:.3f}","-i",f"{SC}/tts/full/line_{l}.wav",wav], check=True)
            img = j["crop"]
            if k > 0:
                prev = f"{L}/clips/lc_{l}.mp4" if k == 1 else f"{L}/clips/lc_{l}_{k-1}.mp4"
                img = f"{L}/achunks/{l}_{k}_start.jpg"
                subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-sseof","-0.08","-i",prev,"-frames:v","1","-q:v","2",img], check=True)
            try:
                t = time.time()
                r = c.submit(image_path=handle_file(img), audio_path=handle_file(wav), prompt=j["prompt"], resolution='480p', seed=42,
                             vocal_mode='Clean speech (fast)', acceleration='DBCache faster', api_name='/generate').result(timeout=600)
                pth = r if isinstance(r, str) else (r.get('video') if isinstance(r, dict) else r[0])
                if isinstance(pth, dict): pth = pth.get('video') or pth.get('path')
                shutil.copy(pth, out); print("ok", l, k, f"{b[k]:.2f}-{b[k+1]:.2f}", round(time.time()-t), "s", flush=True)
            except Exception as e:
                print("FAIL", l, k, str(e)[:200], flush=True)
                if "quota" in str(e).lower(): print("STOP", flush=True); sys.exit(0)
                break
    print("DONE", flush=True)
elif sys.argv[1] == "lc":
    from gradio_client import Client, handle_file
    c = Client('victor/LongCat-Video-Avatar-1.5', verbose=False); fails = 0
    for j in jobs():
        out = f"{L}/clips/lc_{j['id']}.mp4"
        if os.path.exists(out): continue
        try:
            t = time.time()
            r = c.submit(image_path=handle_file(j["crop"]), audio_path=handle_file(f"{SC}/tts/full/line_{j['id']}.wav"),
                         prompt=j["prompt"], resolution='480p', seed=42, vocal_mode='Clean speech (fast)',
                         acceleration='DBCache faster', api_name='/generate').result(timeout=600)
            p = r if isinstance(r, str) else (r.get('video') if isinstance(r, dict) else r[0])
            if isinstance(p, dict): p = p.get('video') or p.get('path')
            shutil.copy(p, out); fails = 0; print("ok", j["id"], round(time.time()-t), "s", flush=True)
        except Exception as e:
            fails += 1; print("FAIL", j["id"], str(e)[:200], flush=True)
            if fails >= 3 or "quota" in str(e).lower(): print("STOP", flush=True); break
            time.sleep(15)
            try: c = Client('victor/LongCat-Video-Avatar-1.5', verbose=False)
            except Exception: pass
    print("DONE", len(os.listdir(f"{L}/clips")), "/", len(jobs()), flush=True)

import os, re, subprocess, wave, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SC = "/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad"
EP = "/home/user/Ai-mation/docs/oasis-team/ep01"
LN = f"{SC}/tts/full"
AN = f"{SC}/anim"
OUT = f"{SC}/edit"
FONT_B = f"{SC}/fonts/Cairo-ExtraBold.ttf"
FONT_T = f"{SC}/fonts/Lalezar.ttf"
W, H, FPS = 1280, 720, 30
os.makedirs(f"{OUT}/png", exist_ok=True); os.makedirs(f"{OUT}/seg", exist_ok=True)

import sys; sys.path.insert(0, LN)
from lines import LINES
TEXT, SPK = {}, {}
for ch, (_, ls) in LINES.items():
    for lid, _, t in ls: TEXT[lid] = t; SPK[lid] = ch
COLOR = {"rahhal": "#FFB13D", "shaheen": "#5EE6F0", "hasat": "#B6F25A", "narrator": "#FFFFFF"}

def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
LD = {lid: dur(f"{LN}/line_{lid}.wav") for lid in TEXT}

def run(cmd): subprocess.run(cmd, check=True)

# ---------- text images ----------
TASH = re.compile(r"[ً-ْ]")
def text_png(path, text, size, color, font=FONT_B, stroke=7):
    f = ImageFont.truetype(font, size)
    im = Image.new("RGBA", (W, H), (0,0,0,0)); d = ImageDraw.Draw(im)
    return im, d, f

def subtitle_png(path, text, color, big=False):
    size = 74 if big else 58
    f = ImageFont.truetype(FONT_B, size)
    im = Image.new("RGBA", (W, H), (0,0,0,0)); d = ImageDraw.Draw(im)
    d.text((W//2, H-95), text, font=f, anchor="mm", fill=color, stroke_width=7, stroke_fill="#1a1208", direction="rtl")
    im.save(path)

def chunks(text):
    t = TASH.sub("", text).replace("…", " ").replace("?!", "؟!")
    words = t.split()
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == 3 or re.search(r"[!؟?.،:]$", w):
            out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    # merge single trailing tiny chunk
    return out

# ---------- shots ----------
# visual: list of ("clip", name, start, length) and/or ("img", name, motion)
SHOTS = [
 dict(v=[("clip","s01",0,3.4),("img","s01","in")], lines=["01","02"], lead=0.2, tail=0.5, wind=True),
 dict(title=True, d=3.0),
 dict(v=[("img","s03","in")], lines=["03","04","05"], focus={"rahhal":(0.21,0.45),"shaheen":(0.42,0.5),"hasat":(0.79,0.55)}),
 dict(v=[("img","s04","out")], lines=["06","07","08","09","10","11","12"], badge="وقت الإحماء!", big=["07","08","09","10"], focus={"rahhal":(0.2,0.45),"shaheen":(0.47,0.45),"hasat":(0.82,0.45)}),
 dict(v=[("clip","s05",0,3.4),("img","s05","in")], lines=["13"]),
 dict(v=[("img","s06","in")], lines=["14","15","16"], tail=0.1, focus={"rahhal":(0.22,0.42),"shaheen":(0.45,0.42),"hasat":(0.8,0.6)}),
 dict(v=[("clip","s06",0,3.0)], lines=[], d=3.0),
 dict(v=[("clip","s07",0,2.8),("img","s07","right")], lines=["17","18"]),
 dict(v=[("clip","s08",0,3.5),("img","s08","in")], lines=["19"], wind=True),
 dict(v=[("clip","s01",1.0,2.4)], lines=[], d=2.4, wind=True, caption=("أين الواحة؟!", COLOR["rahhal"])),
 dict(v=[("img","s09","in")], lines=["20"], tail=2.2, qmark=True),
 dict(v=[("img","s10","out")], lines=["21","22","23","24","25"], focus={"rahhal":(0.3,0.5),"shaheen":(0.65,0.55)}),
 dict(v=[("img","s11b","in")], lines=["26"], tail=0.3),
 dict(v=[("img","s11","in")], lines=["27"], tail=0.3),
 dict(v=[("img","s11b","out")], lines=["28"], tail=0.3),
 dict(v=[("img","s11","out")], lines=["29"]),
 dict(v=[("img","s12","in")], lines=["30","31"], focus={"rahhal":(0.22,0.45),"shaheen":(0.45,0.5),"hasat":(0.8,0.5)}),
 dict(v=[("img","s13","out")], lines=["32","33","34"], tail=0.8, focus={"rahhal":(0.3,0.45),"shaheen":(0.5,0.5),"hasat":(0.72,0.5)}),
 dict(v=[("img","s14","in")], lines=["35","36"], tail=2.0, endcard=True),
]
GAP = 0.35

def kb(img, motion, d, out):
    n = max(1, round(d*FPS))
    if motion == "in":  z, x, y = f"1+0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "out": z, x, y = f"1.10-0.10*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    else: z, x, y = "1.08", f"(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"
    run(["ffmpeg","-nostdin","-v","error","-y","-framerate",str(FPS),"-loop","1","-t",f"{d:.3f}","-i",f"{EP}/{img}.jpg",
         "-vf",f"scale=2560:1440,zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p",
         "-frames:v",str(n),"-c:v","libx264","-crf","18","-preset","fast",out])

def kbf(img, fx, fy, d, out, z0=1.45, z1=1.55):
    n = max(1, round(d*FPS))
    z = f"{z0}+{z1-z0}*on/{n}"
    x = f"max(0,min(iw-iw/zoom,{fx}*iw-iw/zoom/2))"; y = f"max(0,min(ih-ih/zoom,{fy}*ih-ih/zoom/2))"
    run(["ffmpeg","-nostdin","-v","error","-y","-framerate",str(FPS),"-loop","1","-t",f"{d:.3f}","-i",f"{EP}/{img}.jpg",
         "-vf",f"scale=2560:1440,zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p",
         "-frames:v",str(n),"-c:v","libx264","-crf","18","-preset","fast",out])

CL = f"{SC}/anim2/clips"
USE_CLIPS = True
def clipf(path, length, out, pad=0.0):
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},setsar=1"
    if pad > 0: vf += f",tpad=stop_mode=clone:stop_duration={pad:.3f}"
    run(["ffmpeg","-nostdin","-v","error","-y","-i",path,"-t",f"{length+pad:.3f}","-vf",vf+",format=yuv420p","-an","-c:v","libx264","-crf","18","-preset","fast",out])

def clip(name, start, length, out):
    run(["ffmpeg","-nostdin","-v","error","-y","-ss",str(start),"-t",f"{length:.3f}","-i",f"{AN}/{name}.mp4",
         "-vf",f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,format=yuv420p",
         "-an","-c:v","libx264","-crf","18","-preset","fast",out])

def title_card(d, out):
    bg = Image.open(f"{EP}/s13.jpg").convert("RGB").resize((W,H)).filter(ImageFilter.GaussianBlur(6))
    bg = Image.eval(bg, lambda p: int(p*0.55))
    d_ = ImageDraw.Draw(bg)
    d_.text((W//2, H//2-60), "فريق الواحة", font=ImageFont.truetype(FONT_T,150), anchor="mm", fill="#FFD54A", stroke_width=8, stroke_fill="#3a1d05", direction="rtl")
    d_.text((W//2, H//2+95), "سباق الكثبان", font=ImageFont.truetype(FONT_B,70), anchor="mm", fill="white", stroke_width=6, stroke_fill="#3a1d05", direction="rtl")
    bg.save(f"{OUT}/png/title.png")
    kbtmp = f"{OUT}/png/title.png"
    n = round(d*FPS)
    run(["ffmpeg","-nostdin","-v","error","-y","-framerate",str(FPS),"-loop","1","-t",f"{d:.3f}","-i",kbtmp,
         "-vf",f"scale=2560:1440,zoompan=z='1+0.05*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},fade=t=in:st=0:d=0.3,setsar=1,format=yuv420p",
         "-frames:v",str(n),"-c:v","libx264","-crf","18","-preset","fast",out])

timeline = []   # (abs_time, lid)
winds = []      # (start, end)
segs = []
t0 = 0.0
pi = 0
for si, s in enumerate(SHOTS):
    seg = f"{OUT}/seg/{si:02d}.mp4"
    if s.get("title"):
        title_card(s["d"], seg); segs.append(seg); t0 += s["d"]; continue
    lead, tail = s.get("lead", 0.3), s.get("tail", 0.6)
    lines = s["lines"]
    if lines:
        d = lead + sum(LD[l] for l in lines) + GAP*(len(lines)-1) + tail
    else:
        d = s["d"]
    # visual parts
    parts, rem = [], d
    if lines and USE_CLIPS:
        for i, l in enumerate(lines):
            need = LD[l] + (GAP if i < len(lines)-1 else tail) + (lead if i == 0 else 0)
            k = 0; got = 0.0
            while got < need - 0.04:
                cp = f"{CL}/{l}_{k}.mp4"
                if not os.path.exists(cp): break
                cd = dur(cp); L = min(cd, need - got)
                p = f"{OUT}/seg/{si:02d}_c{i}_{k}.mp4"; clipf(cp, L, p); parts.append(p); got += L; k += 1
            if got < need - 0.04:
                rest = need - got
                if got > 0 and rest <= 0.8:
                    p = f"{OUT}/seg/{si:02d}_c{i}_pad.mp4"; clipf(f"{CL}/{l}_{k-1}.mp4", dur(f"{CL}/{l}_{k-1}.mp4"), p, pad=rest); parts.append(p)
                else:
                    img = s["v"][-1][1]; p = f"{OUT}/seg/{si:02d}_c{i}_kb.mp4"
                    fx = s.get("focus", {}).get(SPK[l])
                    if fx: kbf(img, *fx, rest, p)
                    else: kb(img, "in", rest, p)
                    parts.append(p); print("  fallback still", l, round(rest,2), flush=True)
        rem = 0
    if rem > 0 and s.get("focus"):
        img = s["v"][0][1]; prev = None
        for i, l in enumerate(lines):
            ln = LD[l] + (GAP if i < len(lines)-1 else tail) + (lead if i == 0 else 0)
            spk = SPK[l]; p = f"{OUT}/seg/{si:02d}_f{i}.mp4"
            wide = (i == 0) or (spk == prev and i % 2 == 0) or spk not in s["focus"]
            if wide: kb(img, ["in","out"][i % 2], ln, p)
            else: kbf(img, *s["focus"][spk], ln, p)
            parts.append(p); prev = spk
        rem = 0
    for k, item in enumerate(s["v"] if rem > 0 else []):
        if rem <= 0.05: break
        p = f"{OUT}/seg/{si:02d}_{k}.mp4"
        if item[0] == "clip":
            L = min(item[3], rem); clip(item[1], item[2], L, p); rem -= L
        else:
            kb(item[1], item[2], rem, p); rem = 0
        parts.append(p)
    # overlays
    ov = []  # (png, start, end)
    t = lead
    for l in lines:
        ld = LD[l] - 0.1
        cs = chunks(TEXT[l]); total = sum(len(c) for c in cs); ct = t
        for ci, c in enumerate(cs):
            cd = ld * len(c) / total
            png = f"{OUT}/png/sub_{l}_{ci}.png"
            subtitle_png(png, c, COLOR[SPK[l]], big=l in s.get("big", []))
            ov.append((png, ct, ct + cd)); ct += cd
        timeline.append((t0 + t, l))
        t += LD[l] + GAP
    if s.get("badge"):
        im = Image.new("RGBA",(W,H),(0,0,0,0)); dd = ImageDraw.Draw(im)
        dd.rounded_rectangle((W-360,30,W-30,120), 24, fill="#FF7A2F")
        dd.text((W-195,73), s["badge"], font=ImageFont.truetype(FONT_B,48), anchor="mm", fill="white", direction="rtl")
        im.save(f"{OUT}/png/badge.png"); ov.append((f"{OUT}/png/badge.png", 0, d))
    if s.get("qmark"):
        im = Image.new("RGBA",(W,H),(0,0,0,0)); dd = ImageDraw.Draw(im)
        dd.text((W-210, H//2-40), "؟", font=ImageFont.truetype(FONT_T,300), anchor="mm", fill="#FFD54A", stroke_width=10, stroke_fill="#3a1d05")
        im.save(f"{OUT}/png/q.png"); ov.append((f"{OUT}/png/q.png", d - s["tail"], d))
    if s.get("caption"):
        txt, col = s["caption"]; png = f"{OUT}/png/cap_{si}.png"; subtitle_png(png, txt, col, big=True); ov.append((png, 0.2, d))
    if s.get("endcard"):
        im = Image.new("RGBA",(W,H),(0,0,0,0)); dd = ImageDraw.Draw(im)
        dd.rounded_rectangle((W//2-420,60,W//2+420,200), 30, fill=(10,20,60,200))
        dd.text((W//2,130), "الحلقة القادمة: سرّ النجوم", font=ImageFont.truetype(FONT_B,64), anchor="mm", fill="#FFD54A", direction="rtl")
        im.save(f"{OUT}/png/end.png"); st = timeline[-1][0] - t0
        ov.append((f"{OUT}/png/end.png", st, d))
    if s.get("wind"): winds.append((t0, t0 + d))
    # assemble shot: concat parts, then overlays
    cmd = ["ffmpeg","-nostdin","-v","error","-y"]
    for p in parts: cmd += ["-i", p]
    for png, a, b in ov: cmd += ["-i", png]
    fc = "".join(f"[{i}:v]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[b0];"
    last = "b0"
    for j, (png, a, b) in enumerate(ov):
        fc += f"[{last}][{len(parts)+j}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[b{j+1}];"; last = f"b{j+1}"
    fc += f"[{last}]fade=t=in:st=0:d=0.15,format=yuv420p[vout]"
    cmd += ["-filter_complex", fc, "-map", "[vout]", "-t", f"{d:.3f}", "-r", str(FPS), "-c:v","libx264","-crf","19","-preset","medium", seg]
    run(cmd)
    segs.append(seg); t0 += d
    print(f"shot {si:02d} {d:5.2f}s  ends {t0:6.2f}", flush=True)

TOTAL = t0
with open(f"{OUT}/seg/list.txt","w") as f:
    for s in segs: f.write(f"file '{s}'\n")
run(["ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i",f"{OUT}/seg/list.txt","-c","copy",f"{OUT}/video_only.mp4"])

# ---------- audio ----------
cmd = ["ffmpeg","-nostdin","-v","error","-y"]
fc = ""; labels = []
for i, (at, l) in enumerate(timeline):
    cmd += ["-i", f"{LN}/line_{l}.wav"]
    ms = int(at*1000); fc += f"[{i}:a]aresample=44100,aformat=channel_layouts=mono,loudnorm=I=-16:TP=-2,adelay={ms}|{ms}[a{i}];"; labels.append(f"[a{i}]")
n = len(timeline)
# wind ambience: brown noise, band-limited, faded in each wind window
cmd += ["-f","lavfi","-t",f"{TOTAL:.3f}","-i","anoisesrc=color=brown:amplitude=0.6:sample_rate=44100"]
expr = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in winds) or "0"
fc += f"[{n}:a]lowpass=f=700,highpass=f=120,volume='0.10*({expr})':eval=frame[w];"
labels.append("[w]")
fc += "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{TOTAL:.3f}[mix]"
cmd += ["-filter_complex", fc, "-map", "[mix]", "-ar","44100","-ac","2", f"{OUT}/voice_mix.wav"]
run(cmd)
run(["ffmpeg","-nostdin","-v","error","-y","-i",f"{OUT}/video_only.mp4","-i",f"{OUT}/voice_mix.wav",
     "-c:v","copy","-af","loudnorm=I=-16:TP=-1.5:LRA=9","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",f"{OUT}/ep01_v2.mp4"])
json.dump({"timeline": timeline, "total": TOTAL}, open(f"{OUT}/timeline.json","w"), ensure_ascii=False)
print("DONE", round(TOTAL,2), "s")

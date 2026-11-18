import os, re, json, subprocess, math, numpy as np, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import gfx, famflap
from lines import LINES
D = "/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad/fam"
K = "/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad/kid"
S = f"{D}/seg"; os.makedirs(S, exist_ok=True)
W, H, FPS = 1280, 720, 30
TEXT = {l: t for _, (_, ls) in LINES.items() for l, _, t in ls}
SPK = {l: ch for ch, (_, ls) in LINES.items() for l, _, _ in ls}
WT = json.load(open(f"{D}/word_times.json"))
COL = {"sami": "#FFB13D", "grandpa": "#7FD8FF", "grandma": "#B6F25A"}
RIG = {"sami": "boy", "grandpa": "gp", "grandma": "gm"}
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
def run(c): subprocess.run(c, check=True)
LD = {l: dur(f"{D}/line_{l}.wav") for l in TEXT}

# ---------- sound effects ----------
def tone(path, freqs, d, vol=0.3, decay=6):
    sr = 44100; t = np.arange(int(sr*d))/sr; y = sum(np.sin(2*np.pi*f*t) for f in freqs)/len(freqs)*np.exp(-decay*t)*vol
    w = wave.open(path, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y*32767).astype(np.int16).tobytes()); w.close()
tone(f"{S}/tick.wav", [880], 0.15, 0.25, 25); tone(f"{S}/ding.wav", [1046, 1318, 1568], 0.9, 0.3, 4); tone(f"{S}/click.wav", [300, 600], 0.2, 0.4, 30)

timeline = []   # (time, wav)
subs = []       # (start, end, text, color)
segs = []; T = [0.0]

def add_seg(path):
    segs.append(path); T[0] += dur(path)

def kb_still(img, d, out, z0=1.0, z1=1.08, blur=0):
    n = int(d*FPS); vf = f"scale=2560:1440,zoompan=z='{z0}+{z1-z0}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}"
    if blur: vf += f",gblur=sigma={blur}"
    run(["ffmpeg","-nostdin","-v","error","-y","-framerate",str(FPS),"-loop","1","-t",f"{d:.3f}","-i",img,"-vf",vf+",setsar=1,format=yuv420p","-frames:v",str(n),"-c:v","libx264","-crf","18",out])

def subtitle_for(l, t0):
    words = re.sub(r"[ً-ْ]", "", TEXT[l]).replace("…", " ").split(); wt = WT.get(l, [])
    chunks, cur = [], []
    for w_ in words:
        cur.append(w_)
        if len(cur) == 3 or re.search(r"[!؟?.،:]$", w_): chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    nw = len(words); wi = 0; out = []
    for c in chunks:
        if wt:
            a = wt[min(len(wt)-1, round(wi*len(wt)/nw))][0]; b = wt[min(len(wt)-1, round((wi+len(c))*len(wt)/nw)-1)][1]
        else: a = LD[l]*wi/nw; b = LD[l]*(wi+len(c))/nw
        out.append([t0 + max(0, a - 0.05), t0 + b + 0.1, " ".join(c), COL[SPK[l]]]); wi += len(c)
    for j in range(len(out)-1): out[j][1] = min(out[j][1], out[j+1][0] - 0.02)
    subs.extend(out)

def say(l, punch=1.0, tail=0.35):
    """character close-up speaking line l"""
    out = f"{S}/say_{l}.mp4"; famflap.render(RIG[SPK[l]], f"{D}/line_{l}.wav", out, punch)
    hold = f"{S}/say_{l}_h.mp4"
    run(["ffmpeg","-nostdin","-v","error","-y","-i",out,"-vf",f"tpad=stop_mode=clone:stop_duration={tail}","-c:v","libx264","-crf","18",hold])
    timeline.append((T[0], f"{D}/line_{l}.wav")); subtitle_for(l, T[0]); add_seg(hold)

def vo(l, make, extra=0.6, minimum=0.0, sub=True):
    """graphic segment with voice-over of line l; make(duration, outpath)"""
    d = max(LD[l] + extra, minimum); out = f"{S}/vo_{l}.mp4"; make(d, out)
    timeline.append((T[0], f"{D}/line_{l}.wav"))
    if sub: subtitle_for(l, T[0])
    add_seg(out)

def graphic(name, make, d, sfx=()):
    out = f"{S}/g_{name}.mp4"; make(d, out)
    for at, s_ in sfx: timeline.append((T[0] + at, f"{S}/{s_}.wav"))
    add_seg(out)

def countdown_sfx(at): return [(at, "tick"), (at+1, "tick"), (at+2, "tick"), (at+3, "ding")]

# ---------------- the episode ----------------
kb_still(f"{D}/crops/hook_boy.jpg", 1.2, f"{S}/hook.mp4", 1.0, 1.06); add_seg(f"{S}/hook.mp4")
say("01")
graphic("title", lambda d, o: gfx.title_card("حروف مع الجد والجدة", "صندوق النقاط", d, o, f"{K}/scene_family_closed.png"), 3.0)
kb_still(f"{K}/scene_family_closed.png", 1.5, f"{S}/wide1.mp4", 1.0, 1.05); add_seg(f"{S}/wide1.mp4")
say("02"); say("04"); say("05", 1.06); say("03"); say("07")
graphic("locks0", lambda d, o: gfx.locks(0, -1, d, o), 2.2)
# ب
vo("08", lambda d, o: gfx.letter_build("ب", d, o, caption="نقطةٌ واحدةٌ تحتَه"), 1.0, 5.2)
graphic("wc_bab", lambda d, o: gfx.word_card("🚪", "باب", d, o, note="الباء في أول الكلمة"), 2.2)
say("09")
graphic("rid_b", lambda d, o: gfx.riddle("🚪", "باب", d, o, count_at=0.4), 4.8, countdown_sfx(0.4))
say("10", 1.06)
graphic("locks1", lambda d, o: gfx.locks(0, 0, d, o), 2.2, [(0.6, "click")])
# ت
vo("11", lambda d, o: gfx.letter_build("ت", d, o, caption="نقطتانِ فوقَه"), 1.0, 5.2)
vo("12", lambda d, o: gfx.choice_quiz("كم نقطةً للتاء، وأين هي؟", [(None, "نقطة تحته"), (None, "نقطتان فوقه"), (None, "ثلاث نقاط")], 1, d, o, count_at=LD["12"] + 0.3), 0, LD["12"] + 4.6, sub=True)
timeline.extend([(T[0] - (4.6 - 0.3) + k, f"{S}/tick.wav") for k in range(3)] + [(T[0] - 1.3, f"{S}/ding.wav")])
say("13")
graphic("rid_t", lambda d, o: gfx.riddle("🌴", "تمر", d, o, count_at=0.4), 4.8, countdown_sfx(0.4))
say("14", 1.06); say("15")
graphic("locks2", lambda d, o: gfx.locks(1, 1, d, o), 2.2, [(0.6, "click")])
# ث
vo("16", lambda d, o: gfx.letter_build("ث", d, o, caption="ثلاثُ نقاطٍ فوقَه"), 1.0, 5.6)
say("17", 1.08)
vo("18", lambda d, o: gfx.choice_quiz("أيُّ حيوانٍ يبدأُ بحرفِ الثاء؟", [("🦊", "ثعلب"), ("🦁", "أسد"), ("🐘", "فيل")], 0, d, o, count_at=LD["18"] + 0.3), 0, LD["18"] + 4.6)
timeline.extend([(T[0] - (4.6 - 0.3) + k, f"{S}/tick.wav") for k in range(3)] + [(T[0] - 1.3, f"{S}/ding.wav")])
say("19")
graphic("rid_th", lambda d, o: gfx.riddle("❄️", "ثلج", d, o, count_at=0.4), 4.8, countdown_sfx(0.4))
graphic("locks3", lambda d, o: gfx.locks(2, 2, d, o), 2.2, [(0.6, "click")])
# ن
say("20", 1.06)
vo("21b", lambda d, o: gfx.letter_build("ن", d, o, caption="نقطةٌ واحدةٌ فوقَها"), 1.0, 5.2)
say("21")
graphic("rid_n", lambda d, o: gfx.riddle("🐝", "نحلة", d, o, count_at=0.4), 4.8, countdown_sfx(0.4))
say("22", 1.06); say("23")
graphic("locks4", lambda d, o: gfx.locks(3, 3, d, o), 2.2, [(0.6, "click")])
# open the chest
kb_still(f"{K}/scene_open.png", 1.6, f"{S}/open.mp4", 1.0, 1.1, blur=16); timeline.append((T[0], f"{S}/ding.wav")); add_seg(f"{S}/open.mp4")
vo("24", lambda d, o: gfx.cubes(f"{K}/scene_open.png", d, o), 0.6, 4.0)
say("25", 1.06); say("26"); say("27", 1.08)
# quick quiz
say("28")
for k, (q, opts, c) in enumerate([("حرفٌ نقطتُه تحتَه؟", [(None, "ب"), (None, "ت"), (None, "ن")], 0),
                                  ("حرفٌ فوقَه نقطتان؟", [(None, "ث"), (None, "ت"), (None, "ب")], 1),
                                  ("كلمة «تمر» تبدأ بحرف…؟", [(None, "ب"), (None, "ث"), (None, "ت")], 2)]):
    graphic(f"qq{k}", lambda d, o, q=q, opts=opts, c=c: gfx.choice_quiz(q, opts, c, d, o, count_at=0.7), 4.6, countdown_sfx(0.7))
say("30"); say("31", 1.0, tail=2.5)
END = T[0]

# ---------- assemble video ----------
open(f"{S}/list.txt", "w").write("".join(f"file '{p}'\n" for p in segs))
run(["ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i",f"{S}/list.txt","-c:v","libx264","-crf","19","-r",str(FPS),f"{S}/video.mp4"])

# ---------- subtitles + end card overlay ----------
F = ImageFont.truetype(gfx.FB, 56)
ov = []
for k, (a, b, t, c) in enumerate(subs):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((W//2, H - 70), t, font=F, anchor="mm", fill=c, stroke_width=7, stroke_fill="#1a1208", direction="rtl")
    p = f"{S}/sub_{k}.png"; im.save(p); ov.append((p, a, b))
im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.rounded_rectangle((W//2 - 400, 40, W//2 + 400, 170), 30, fill=(20, 40, 90, 210))
d.text((W//2, 105), "الحلقة القادمة: عائلة الجيم", font=ImageFont.truetype(gfx.FT, 70), anchor="mm", fill="#FFD54A", direction="rtl")
im.save(f"{S}/end.png"); ov.append((f"{S}/end.png", END - 4.5, END))
# overlay in batches to keep the filter graph small
cur = f"{S}/video.mp4"
for b0 in range(0, len(ov), 25):
    batch = ov[b0:b0+25]; cmd = ["ffmpeg","-nostdin","-v","error","-y","-i",cur]
    for p, _, _ in batch: cmd += ["-i", p]
    fc = ""; last = "0:v"
    for j, (_, a, b) in enumerate(batch):
        fc += f"[{last}][{j+1}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v{j}];"; last = f"v{j}"
    nxt = f"{S}/video_ov{b0}.mp4"; cmd += ["-filter_complex", fc.rstrip(";"), "-map", f"[{last}]", "-c:v","libx264","-crf","19", nxt]; run(cmd); cur = nxt

# ---------- audio ----------
cmd = ["ffmpeg","-nostdin","-v","error","-y"]; fc = ""; lab = []
for i, (at, p) in enumerate(timeline):
    cmd += ["-i", p]; ms = int(at*1000)
    norm = ",loudnorm=I=-16:TP=-2" if "line_" in p else ""
    fc += f"[{i}:a]aresample=44100,aformat=channel_layouts=mono{norm},adelay={ms}|{ms}[a{i}];"; lab.append(f"[a{i}]")
fc += "".join(lab) + f"amix=inputs={len(lab)}:normalize=0:duration=longest,atrim=0:{END:.3f}[m]"
cmd += ["-filter_complex", fc, "-map", "[m]", "-ar", "44100", "-ac", "2", f"{S}/audio.wav"]; run(cmd)
run(["ffmpeg","-nostdin","-v","error","-y","-i",cur,"-i",f"{S}/audio.wav","-c:v","copy","-af","loudnorm=I=-16:TP=-1.5:LRA=9","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",f"{D}/family_ep01.mp4"])
json.dump({"end": END, "subs": len(subs)}, open(f"{S}/info.json", "w")); print("DONE", round(END, 1), "s,", len(subs), "subtitle chunks")

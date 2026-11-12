"""يبني فيديو سرقة المتحف العراقي (1080x1920، 30fps) من جدول اللقطات في shots.py.

إعادة التشغيل بعد تبديل أي صورة أو صوت: python3 build.py
- الصوت: voice/NN.m4a (صوتك) إن وُجد، وإلا audio/NN.mp3 (edge-tts). مدة اللقطة = مدة صوتها + 0.3 ثانية.
- الصورة: clips/NN.mp4 (فيديو مولّد) إن وُجد، وإلا images/NN.png أو images/NN.jpg.
- الموسيقى: music/bg.mp3 أو music/bed.wav (أخفض بـ 22 dB مع ducking)، والمؤثرات sfx/NN.wav أو sfx/NN.mp3 إن وُجدت.
- المخرجات: out/iraq-museum.mp4 و out/sheet.jpg
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
from shots import SHOTS

W, H, FPS = 1080, 1920, 30
GAP = 0.3
FADE_PAIRS = {(2, 3), (16, 17)}          # قطع بـ fade قصير 0.3 ث بين هذه اللقطات فقط
BRIGHT = {1: 1.45, 2: 1.15}               # إطار الخطاف أكثر إضاءة: القرار يُتخذ في أول ثانيتين
WORD_Y = {1: 760}                         # موضع الكلمة الصفراء إن كانت تغطي القطعة (الافتراضي 62%)
YELLOW = (255, 212, 0)
B = "build"
for d in (B, "out"):
    os.makedirs(d, exist_ok=True)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("FAILED: " + " ".join(cmd[:6]) + "\n" + r.stderr[-1500:])
    return r.stdout


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


def first(*paths):
    return next((p for p in paths if os.path.exists(p)), None)


# ---------- 1. الصوت ----------
def prep_audio(n):
    src = first(f"voice/{n:02d}.m4a", f"voice/{n:02d}.wav", f"audio/{n:02d}.mp3")
    if not src:
        sys.exit(f"missing audio for shot {n}: run scripts/tts.py")
    out = f"{B}/a{n:02d}.wav"
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse")
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", trim, "-ac", "1", "-ar", "48000", out])
    return out, duration(out) + GAP


# ---------- 2. الصورة ----------
def grade(im):
    """تدرّج موحّد خفيف (ظلال زرقاء مخضرّة وإضاءة كهرمانية) حتى تبدو صور المصادر المختلفة سلسلة واحدة."""
    a = np.asarray(im.convert("RGB")).astype(float) / 255
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])[..., None]
    w = np.clip((lum - 0.15) / 0.6, 0, 1)
    tone = (np.array([0.06, 0.17, 0.20]) * (1 - w) + np.array([1.0, 0.74, 0.42]) * w) * (0.35 + lum * 1.1)
    out = a * 0.72 + np.clip(tone, 0, 1) * 0.28
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


def prep_image(n):
    src = first(f"images/{n:02d}.png", f"images/{n:02d}.jpg", f"images/{n:02d}.webp")
    if not src:
        sys.exit(f"missing image for shot {n}")
    im = Image.open(src).convert("RGB")
    if src.endswith(".jpg"):                       # صور Pollinations: علامة مائية أسفل اليمين
        im = im.crop((0, 0, im.width, int(im.height * 0.91)))
    im = grade(im)
    if n in BRIGHT:
        im = ImageEnhance.Contrast(ImageEnhance.Brightness(im).enhance(BRIGHT[n])).enhance(1.08)
    # تغطية 2160x3840 (ضعف الدقة) حتى يكون zoompan ناعماً بلا اهتزاز، بدون مطّ
    tw, th = W * 2, H * 2
    s = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - tw) // 2, (im.height - th) // 2
    im = im.crop((l, t, l + tw, t + th))
    im = ImageEnhance.Sharpness(im).enhance(1.15)
    out = f"{B}/i{n:02d}.png"
    im.save(out)
    return out


def zoompan(motion, frames):
    """تعابير zoompan لكل نوع حركة (زوم بين 1.00 و1.12 كحد أقصى)."""
    p = f"(on/{max(frames - 1, 1)})"
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    M = {
        "zin":       (f"1+0.10*{p}", cx, cy),
        "zin_slow":  (f"1+0.05*{p}", cx, cy),
        "zin_fast":  (f"1+0.12*min(1,{p}*2.2)", cx, cy),
        "still_zin": (f"1+0.10*max(0,({p}-0.4)/0.6)", cx, cy),
        "zout":      (f"1.10-0.10*{p}", cx, cy),
        "zout_long": (f"1.12-0.12*{p}", cx, cy),
        "panup":     ("1.10", cx, f"(ih-ih/zoom)*(1-{p})"),
        "pandown":   ("1.10", cx, f"(ih-ih/zoom)*{p}"),
        "panh":      ("1.10", f"(iw-iw/zoom)*{p}", cy),
        "shake":     ("1.08", f"{cx}+14*sin(on*1.9)", f"{cy}+10*cos(on*2.3)"),
    }
    z, x, y = M[motion]
    return f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS}"


# ---------- 3. النص ----------
def text_layers(n, word, en):
    """طبقتان شفافتان: الكلمة الصفراء (للأنيميشن pop) والترجمة الإنجليزية (ثابتة)."""
    ar_font = ImageFont.truetype("fonts/Cairo_900Black.ttf", 112, layout_engine=ImageFont.Layout.RAQM)
    en_font = ImageFont.truetype("fonts/Tajawal_500Medium.ttf", 40)
    word_png = None
    if word:
        d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
        bb = d.textbbox((0, 0), word, font=ar_font, direction="rtl", stroke_width=9)
        tw, th = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
        im = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        sh = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((20 - bb[0], 26 - bb[1]), word, font=ar_font, direction="rtl", fill=(0, 0, 0, 170),
                                stroke_width=9, stroke_fill=(0, 0, 0, 170))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        ImageDraw.Draw(im).text((20 - bb[0], 20 - bb[1]), word, font=ar_font, direction="rtl", fill=YELLOW,
                                stroke_width=9, stroke_fill=(0, 0, 0))
        word_png = f"{B}/w{n:02d}.png"
        im.save(word_png)
    en_png = None
    if en:
        # التفاف السطر داخل 860px
        words, lines, cur = en.split(), [], ""
        for w_ in words:
            t = (cur + " " + w_).strip()
            if en_font.getlength(t) <= 860 or not cur:
                cur = t
            else:
                lines.append(cur); cur = w_
        lines.append(cur)
        lh = 52
        bw = int(max(en_font.getlength(l) for l in lines)) + 48
        bh = lh * len(lines) + 28
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        y0 = 1338
        x0 = (W - bw) // 2
        ImageDraw.Draw(im).rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 14, fill=(0, 0, 0, 140))
        for i, l in enumerate(lines):
            ImageDraw.Draw(im).text((W // 2, y0 + 16 + i * lh), l, font=en_font, fill=(255, 255, 255), anchor="ma")
        en_png = f"{B}/e{n:02d}.png"
        im.save(en_png)
    return word_png, en_png


# ---------- 4. تركيب كل لقطة ----------
def render_shot(i, shot, dur):
    n, _, word, en, _, motion = shot
    frames = round(dur * FPS)
    out = f"{B}/s{n:02d}.mp4"
    clip = first(f"clips/{n:02d}.mp4")
    if clip:
        inputs = ["-stream_loop", "-1", "-i", clip]
        base = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
                f"trim=duration={dur:.3f},setpts=PTS-STARTPTS[bg]")
    else:
        inputs = ["-loop", "1", "-framerate", str(FPS), "-i", prep_image(n)]
        base = f"[0:v]{zoompan(motion, frames)},trim=duration={dur:.3f},setpts=PTS-STARTPTS[bg]"
    word_png, en_png = text_layers(n, word, en)
    fc = [base]
    last = "bg"
    k = 1
    if word_png:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-i", word_png]
        t0 = 0.0 if n == 1 else 0.12            # اللقطة الأولى: النص ظاهر من الإطار صفر
        pop = (f"0.82+0.30*min(1\\,(t-{t0})/0.12)-0.12*min(1\\,max(0\\,(t-{t0}-0.12)/0.10))")
        fc.append(f"[{k}:v]format=rgba,scale=w='trunc(iw*({pop})/2)*2':h=-2:eval=frame,"
                  f"trim=duration={dur:.3f},setpts=PTS-STARTPTS[w]")
        fc.append(f"[{last}][w]overlay=x='(W-w)/2':y='{WORD_Y.get(n, 1190)}-h/2':enable='gte(t,{t0})':eval=frame[v{k}]")
        last = f"v{k}"; k += 1
    if en_png:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-i", en_png]
        fc.append(f"[{k}:v]format=rgba,trim=duration={dur:.3f},setpts=PTS-STARTPTS[e]")
        fc.append(f"[{last}][e]overlay=0:0:enable='gte(t,{0 if n == 1 else 0.12})'[v{k}]")
        last = f"v{k}"; k += 1
    fades = []
    nxt = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else None
    prv = SHOTS[i - 1][0] if i > 0 else None
    if (n, nxt) in FADE_PAIRS:
        fades.append(f"fade=t=out:st={dur - 0.3:.3f}:d=0.3")
    if (prv, n) in FADE_PAIRS:
        fades.append("fade=t=in:st=0:d=0.3")
    fc.append(f"[{last}]" + (",".join(fades) + "," if fades else "") + "format=yuv420p[out]")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc), "-map", "[out]",
         "-frames:v", str(frames), "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", out])
    return out


def main():
    timeline, t = [], 0.0
    for i, shot in enumerate(SHOTS):
        n = shot[0]
        a, dur = prep_audio(n)
        frames = round(dur * FPS)
        dur = frames / FPS                         # المدة مضبوطة على عدد إطارات صحيح حتى لا ينزلق الصوت
        v = render_shot(i, shot, dur)
        timeline.append({"n": n, "start": round(t, 3), "dur": round(dur, 3), "video": v, "audio": a})
        print(f"shot {n:02d}  {t:6.2f}s  +{dur:.2f}s", flush=True)
        t += dur
    json.dump(timeline, open(f"{B}/timeline.json", "w"), indent=1)

    # الفيديو: ربط اللقطات
    with open(f"{B}/concat.txt", "w") as f:
        for s in timeline:
            f.write(f"file '{os.path.basename(s['video'])}'\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{B}/concat.txt", "-c", "copy", f"{B}/video.mp4"])

    # الصوت: كل جملة في بداية لقطتها
    ins, parts = [], []
    for k, s in enumerate(timeline):
        ins += ["-i", s["audio"]]
        ms = int(s["start"] * 1000)
        parts.append(f"[{k}]adelay={ms}|{ms}[d{k}]")
    mix = ";".join(parts) + ";" + "".join(f"[d{k}]" for k in range(len(timeline))) + \
          f"amix=inputs={len(timeline)}:normalize=0,apad,atrim=0:{t:.3f},loudnorm=I=-16:TP=-1.5:LRA=11[v]"
    run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", mix, "-map", "[v]", "-ar", "48000", "-ac", "1", f"{B}/voice.wav"])

    # المؤثرات الصوتية (اختيارية)
    sfx = [(s["start"], first(f"sfx/{s['n']:02d}.wav", f"sfx/{s['n']:02d}.mp3")) for s in timeline]
    sfx = [(st, p) for st, p in sfx if p]
    final_in = ["-i", f"{B}/video.mp4", "-i", f"{B}/voice.wav"]
    graph = ["[1]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[vo][sc]"]
    layers = ["[vo]"]
    k = 2
    music = first("music/bg.mp3", "music/bed.wav")
    if music:
        final_in += ["-stream_loop", "-1", "-i", music]
        graph.append(f"[{k}]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{t:.3f},lowpass=f=5000,"
                     f"loudnorm=I=-38:TP=-9:LRA=11,afade=t=in:d=1.0,afade=t=out:st={t - 2.5:.3f}:d=2.5[m0]")
        graph.append("[m0][sc]sidechaincompress=threshold=0.04:ratio=4:attack=30:release=500[m]")
        layers.append("[m]")
        k += 1
    for st, p in sfx:
        final_in += ["-i", p]
        ms = int(st * 1000)
        graph.append(f"[{k}]aresample=48000,aformat=channel_layouts=stereo,volume=0.5,adelay={ms}|{ms}[x{k}]")
        layers.append(f"[x{k}]")
        k += 1
    graph.append("".join(layers) + f"amix=inputs={len(layers)}:normalize=0:duration=first,atrim=0:{t:.3f},"
                 "loudnorm=I=-14:TP=-1.0:LRA=11[a]")
    run(["ffmpeg", "-y", "-v", "error", *final_in, "-filter_complex", ";".join(graph), "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "out/iraq-museum.mp4"])

    # ورقة المراجعة: إطار من منتصف كل لقطة
    thumbs = []
    for s in timeline:
        p = f"{B}/t{s['n']:02d}.jpg"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s['start'] + s['dur'] * 0.6:.2f}", "-i", "out/iraq-museum.mp4",
             "-frames:v", "1", "-vf", "scale=216:384", p])
        thumbs.append(p)
    sheet = Image.new("RGB", (216 * 8, 384 * 3), (0, 0, 0))
    for i, p in enumerate(thumbs):
        sheet.paste(Image.open(p), ((i % 8) * 216, (i // 8) * 384))
    sheet.save("out/sheet.jpg", quality=88)
    print(f"done: out/iraq-museum.mp4  {t:.1f}s")


if __name__ == "__main__":
    main()

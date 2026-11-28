"""قصيدة «احركني كتله حطب» للشاعر سمير صبيح فوق فيديو النار: كلمة كلمة مع النطق، وتختفي عند التوقف.
المخرجات: out/poem.mp4 (1080x1920، 30fps)."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
AUDIO_DUR = 15.552
SRC_START = 26.8          # المقطع الذي ترتفع فيه النار أكثر
TEXT_Y = 1400             # فوق شريط تيك توك السفلي
# (الكلمة، لحظة ظهورها)، وكل سطر ينتهي عند نهاية نطقه
LINES = [   # النص بإملاء المستخدم
 ([("احركني..", 0.00)], 1.45),
 ([("احركني", 2.00), ("كتله", 2.64), ("حطب", 3.04)], 3.84),
 ([("بيه", 3.84), ("ادفه", 4.10), ("وانه", 4.55), ("احتمل", 4.90)], 5.84),
 ([("كيف", 5.84), ("حركني", 6.50), ("ودفه", 7.20)], 7.96),
 ([("وطفاني", 7.96), ("بعد", 8.98), ("الحرك", 9.20)], 9.96),
 ([("كتله", 9.96), ("ضميرك", 10.42), ("صحه", 11.04)], 11.80),
 ([("لا", 11.80), ("كال", 12.38), ("اريدك", 12.74), ("فحم", 13.22)], 13.98),
 ([("مرتين", 13.98), ("راد", 14.36), ("اشتعل", 14.70)], 15.40),
]
CREDIT = "الشاعر سمير صبيح"

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-1500:])

font = ImageFont.truetype("fonts/NotoNaskhArabic-Bold.ttf", 84, layout_engine=ImageFont.Layout.RAQM)
small = ImageFont.truetype("fonts/NotoNaskhArabic-Bold.ttf", 42, layout_engine=ImageFont.Layout.RAQM)

def words_layout(words):
    """مواضع الكلمات من اليمين إلى اليسار في سطر واحد (أو سطرين إذا طال)."""
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    sp = d.textlength(" ", font=font)
    ws = [d.textlength(w, font=font, direction="rtl", features=["-liga", "-dlig", "-calt"]) for w, _ in words]
    total = sum(ws) + sp * (len(ws) - 1)
    x = (W + total) / 2
    pos = []
    for w in ws:
        pos.append(x - w); x -= w + sp
    return pos

def frame(t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    # اسم الشاعر صغيراً في الأعلى
    # اسم الشاعر (صاحب الشعر والإلقاء) في الأسفل، فوق منطقة وصف تيك توك
    d.text((W - 48, 1770), CREDIT, font=small, fill=(255, 226, 170, 225), anchor="rm", direction="rtl")   # أسفل اليمين
    for words, end in LINES:
        if not (words[0][1] - 0.02 <= t < end): continue
        xs = words_layout(words)
        for (w, ts), x in zip(words, xs):
            if t < ts - 0.02: continue
            k = min(1.0, (t - ts + 0.02) / 0.18)                 # ظهور ناعم مع ارتفاع خفيف
            out = min(1.0, max(0.0, (end - t) / 0.15))           # اختفاء عند التوقف
            a = int(255 * k * out)
            y = TEXT_Y + (1 - k) * 18
            fresh = t - ts < 0.45                                  # الكلمة المنطوقة الآن بلون ذهبي ثم تبيضّ
            col = (255, 214, 140, a) if fresh else (255, 255, 255, a)
            d.text((x, y), w, font=font, fill=col, direction="rtl", anchor="ls", features=["-liga", "-dlig", "-calt"],
                   stroke_width=3, stroke_fill=(0, 0, 0, int(a * .55)))
    shadow = txt.split()[3].filter(ImageFilter.GaussianBlur(10))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(shadow.point(lambda v: int(v * .75)))
    im.alpha_composite(sh); im.alpha_composite(txt)
    return im

# 1) طبقة النص كسلسلة صور
os.makedirs("out/txt", exist_ok=True)
n = round(AUDIO_DUR * FPS)
for i in range(n):
    frame(i / FPS).save(f"out/txt/{i:04d}.png")

# 2) الفيديو: خلفية مموّهة تملأ 9:16، والفيديو كاملاً في الوسط، بلا صوت أصلي، ثم النص والقصيدة
run(["ffmpeg", "-y", "-v", "error", "-ss", str(SRC_START), "-t", f"{AUDIO_DUR:.3f}", "-i", "in/source.mp4",
     "-framerate", str(FPS), "-i", "out/txt/%04d.png", "-i", "in/poem.mp3", "-filter_complex",
     # قص الحواف: 608x1080 من وسط الإطار (النار بين البكسل 144 و578) ثم تكبير إلى 1080x1920 ليملأ الشاشة
     f"[0:v]fps={FPS},crop=608:1080:56:0,scale={W}:{H}:flags=lanczos,unsharp=5:5:0.5[v0];"
     f"[v0][1:v]overlay=0:0,fade=t=out:st={AUDIO_DUR-0.5:.2f}:d=0.5,format=yuv420p[v];"
     f"[2:a]loudnorm=I=-14:TP=-1:LRA=11,afade=t=out:st={AUDIO_DUR-0.4:.2f}:d=0.4[aud]",
     "-map", "[v]", "-map", "[aud]", "-t", f"{AUDIO_DUR:.3f}", "-c:v", "libx264", "-preset", "slow", "-crf", "19",
     "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "out/poem.mp4"])
print("done out/poem.mp4")

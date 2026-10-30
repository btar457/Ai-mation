"""موسيقى تصويرية مولّدة برمجياً: نغمة حزينة، ريح، صفير الانتقالات، ضربات الكشف، نبض قلب، وجرس الختام."""
import wave
import numpy as np
from plan import SHOTS, END, REVEALS

SR = 44100
N = int(END * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] = np.linspace(1, 0, nr)
    return e


def lowpass(x, cutoff):
    # مرشح بسيط من الدرجة الأولى، مكرر لمنحدر أشد
    a = np.exp(-2 * np.pi * cutoff / SR)
    for _ in range(2):
        y = np.empty_like(x)
        acc = 0.0
        for i in range(0, len(x), 4096):
            seg = x[i:i + 4096]
            out = np.empty_like(seg)
            for j, v in enumerate(seg):
                acc = (1 - a) * v + a * acc
                out[j] = acc
            y[i:i + 4096] = out
        x = y
    return x


def place(buf, sig, at):
    i = int(at * SR)
    if i < 0:
        sig, i = sig[-i:], 0
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


mix = np.zeros(N)

# 1) نغمة حزينة (ري صغير) تتنفس ببطء، تشتد قليلاً قبل الكشف
chord = [73.42, 110.0, 146.83, 174.61, 220.0]
pad = np.zeros(N)
for k, f in enumerate(chord):
    detune = 1 + 0.002 * np.sin(2 * np.pi * 0.07 * t + k)
    pad += np.sin(2 * np.pi * f * t * detune) * (0.5 if f < 120 else 0.3)
breath = 0.75 + 0.25 * np.sin(2 * np.pi * t / 9.0)
swell = 1 + 0.6 * np.clip((t - 50) / 12, 0, 1) * (t < 62.4)
pad *= breath * swell * env_adsr(N, 2.5, 3.0)
mix += pad / np.abs(pad).max() * 0.22

# 2) ريح الصحراء
noise = rng.standard_normal(N)
wind = lowpass(noise, 500) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 6.3 + 1))
mix += wind / np.abs(wind).max() * 0.10


# 3) صفير قبل كل قطع
def whoosh(d=0.55):
    n = int(d * SR)
    x = rng.standard_normal(n)
    x = x - lowpass(x, 300 + 0)  # تمرير عالٍ تقريبي
    e = np.linspace(0, 1, n) ** 2.5
    e[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    return x * e


wh = whoosh()
wh /= np.abs(wh).max()
for _, s, _, _, _, _ in SHOTS[1:]:
    place(mix, wh * 0.16, s - 0.55)


# 4) ضربة الكشف
def boom(d=3.0):
    n = int(d * SR)
    tt = np.arange(n) / SR
    f = 55 * np.exp(-tt * 0.8) + 30
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.6)
    hit = rng.standard_normal(n) * np.exp(-tt * 25) * 0.4
    return x + hit


for r in REVEALS:
    place(mix, boom() * 0.6, r)


# 5) نبض قلب أثناء سؤال اللغز
def beat():
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 48 * tt) * np.exp(-tt * 14)


for k in np.arange(45.3, 48.8, 0.85):
    place(mix, beat() * 0.55, k)
    place(mix, beat() * 0.35, k + 0.22)


# 6) جرس الختام
def chime(d=3.5):
    n = int(d * SR)
    tt = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, k in [(880, 1.2), (1320, 1.8), (1760, 2.6)])


place(mix, chime() * 0.12, 82.1)

mix *= env_adsr(N, 0.5, 2.5)
mix = np.clip(mix / max(1.0, np.abs(mix).max() / 0.9), -1, 1)
with wave.open("score.wav", "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("score.wav", END)

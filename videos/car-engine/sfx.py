import sys, numpy as np, wave
SR = 44100
def env(n, a, r):
    e = np.ones(n); a, r = int(a*SR), int(r*SR)
    if a: e[:a] = np.linspace(0, 1, a)
    if r: e[-r:] *= np.linspace(1, 0, r)
    return e
def pad(dur, root=98.0):
    t = np.arange(int(dur*SR))/SR
    s = sum(np.sin(2*np.pi*root*k*t + np.sin(2*np.pi*0.11*k*t))/(1+i) for i, k in enumerate([1, 1.5, 2, 2.4, 3]))
    s *= 0.55 + 0.45*np.sin(2*np.pi*0.07*t)**2
    return 0.18*s/np.abs(s).max()*env(len(t), 1.5, 2.0)
def whoosh(d=1.2):
    n = int(d*SR); x = np.random.randn(n); out = np.zeros(n); y = 0.0
    cut = np.linspace(0.01, 0.35, n)**2
    for i in range(n): y += cut[i]*(x[i]-y); out[i] = y
    return 0.6*out/np.abs(out).max()*env(n, d*0.8, d*0.2)
def boom(d=1.6):
    t = np.arange(int(d*SR))/SR; f = 90*np.exp(-t*4)+38
    return 0.9*(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*2.5) + 0.25*np.random.randn(len(t))*np.exp(-t*18))
def sparkle(d=1.5, count=18):
    n = int(d*SR); out = np.zeros(n)
    for _ in range(count):
        st = np.random.randint(0, n-SR//5); L = SR//5; t = np.arange(L)/SR
        out[st:st+L] += np.sin(2*np.pi*np.random.choice([1760, 2093, 2349, 2637, 3136])*t)*np.exp(-t*25)*0.12
    return out
def chime(d=2.5):
    t = np.arange(int(d*SR))/SR
    return sum(np.sin(2*np.pi*f*t)*np.exp(-t*k) for f, k in [(523.25, 2), (659.25, 2.5), (783.99, 3), (1046.5, 3.5)])*0.12
GEN = {'whoosh': whoosh, 'boom': boom, 'sparkle': sparkle, 'chime': chime}
path, dur = sys.argv[1], float(sys.argv[2]); np.random.seed(7); mix = pad(dur)
for ev in sys.argv[3:]:
    at, kind = ev.split(':'); s = GEN[kind](); at = float(at) - (len(s)/SR if kind == 'whoosh' else 0)
    i = max(0, int(at*SR)); s = s[:len(mix)-i]; mix[i:i+len(s)] += s
mix /= max(1.0, np.abs(mix).max()/0.95)
with wave.open(path, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())

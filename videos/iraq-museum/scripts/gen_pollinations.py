"""صور اللقطات من Pollinations (FLUX مجاني) → images/NN.png. الاستخدام: python gen_pollinations.py 4,5,7 [seed]"""
import os, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shots import SHOTS, STYLE
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
want = sys.argv[1].split(",")
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 7
for n, _, _, _, prompt, _ in SHOTS:
    if str(n) not in want: continue
    q = urllib.parse.quote(f"{STYLE}, {prompt}")
    url = f"https://image.pollinations.ai/prompt/{q}?width=1080&height=1920&model=flux&nologo=true&seed={seed + n}"
    for attempt in range(10):
        try:
            data = urllib.request.urlopen(url, timeout=180).read()
            if len(data) > 20000:
                open(f"images/{n:02d}.jpg", "wb").write(data); print("ok", n, len(data), flush=True); break
        except Exception as e:
            print("retry", n, attempt, str(e)[:80], flush=True)
        time.sleep(12)
    else:
        print("FAIL", n, flush=True)

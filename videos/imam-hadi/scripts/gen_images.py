"""صور من Pollinations → images/ID.jpg. الاستخدام: python gen_images.py [IDs] [seed]"""
import os, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shots import SHOTS, STYLE
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ids = sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] != "all" else list(SHOTS)
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 50
for k, sid in enumerate(ids):
    if os.path.exists(f"images/{sid}.jpg") and len(sys.argv) < 3: continue
    url = (f"https://image.pollinations.ai/prompt/{urllib.parse.quote(STYLE + ', ' + SHOTS[sid])}"
           f"?width=1080&height=1920&model=flux&nologo=true&seed={seed + k}")
    for attempt in range(12):
        try:
            d = urllib.request.urlopen(url, timeout=180).read()
            if len(d) > 20000:
                open(f"images/{sid}.jpg", "wb").write(d); print("ok", sid, flush=True); break
        except Exception as e:
            print("retry", sid, attempt, str(e)[:60], flush=True)
        time.sleep(15)
    else:
        print("FAIL", sid, flush=True)

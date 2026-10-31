"""Plan every shot of episode 1 as a Wan clip (<=5 s), crop close-ups, then generate.
Usage: python3 plan.py plan   -> writes plan.json + crops
       python3 plan.py gen    -> generates missing clips, stops after 3 consecutive quota errors
"""
import json, math, os, sys, shutil, subprocess, time
from PIL import Image
SC = "/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad"
EP = "/home/user/Ai-mation/docs/oasis-team/ep01"
D = f"{SC}/anim2"; os.makedirs(f"{D}/in", exist_ok=True); os.makedirs(f"{D}/clips", exist_ok=True)
sys.path.insert(0, f"{SC}/tts/full")
from lines import LINES
SPK, TAG = {}, {}
for ch, (_, ls) in LINES.items():
    for lid, tag, _ in ls: SPK[lid] = ch; TAG[lid] = tag.split(",")[0]
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
LD = {l: dur(f"{SC}/tts/full/line_{l}.wav") for l in SPK}
GAP = 0.35

WHO = {
 "rahhal": "the cartoon baby camel with the red-and-white headband",
 "shaheen": "the cartoon falcon with the teal satchel",
 "hasat": "the cartoon old tortoise with round glasses",
}
TALK = {
 "rahhal": "talks {e}, his mouth opening and closing clearly as he speaks, lively head and neck movement",
 "shaheen": "talks {e}, his beak opening and closing clearly as he speaks, wings gesturing",
 "hasat": "talks {e} and slowly, her mouth opening and closing as she speaks, gentle hand gestures, blinking behind her glasses",
}
STYLE = ", smooth Pixar-style 3D animation, stable characters, natural motion"

# shot: image, focus map, lines, extra action prompts
SHOTS = [
 ("s01", None, ["01","02"], "the cartoon baby camel looks around worried and lost, turning his head, sand blowing in the wind, slow camera orbit"),
 ("s03", {"rahhal":(0.21,0.45),"shaheen":(0.42,0.5),"hasat":(0.79,0.55)}, ["03","04","05"], "the three friends chat happily at the oasis, palm leaves swaying, water sparkling"),
 ("s04", {"rahhal":(0.2,0.45),"shaheen":(0.47,0.45),"hasat":(0.82,0.45)}, ["06","07","08","09","10","11","12"], "the three friends do morning warm-up exercises together, stretching up, rolling shoulders, jumping in place"),
 ("s05", None, ["13"], "the cartoon falcon flies and dives fast across the blue sky over the dunes, wings flapping strongly"),
 ("s06", {"rahhal":(0.22,0.42),"shaheen":(0.45,0.42),"hasat":(0.8,0.6)}, ["14","15","16"], "the three friends get ready at the start line, leaning forward eagerly"),
 ("s07", None, ["17","18"], "the cartoon baby camel runs fast across the sand dunes, legs galloping, sand kicking up, camera tracking alongside"),
 ("s08", None, ["19"], "strong sandstorm, sand swirling around the cartoon baby camel, he squeezes his eyes shut and lowers his head, scarf flapping"),
 ("s09", None, ["20"], "the cartoon baby camel sits sadly on the sand and looks at the camera, ears drooping, gentle breathing"),
 ("s10", {"rahhal":(0.3,0.5),"shaheen":(0.65,0.55)}, ["21","22","23","24","25"], "the falcon and the camel talk in the desert, looking up at the bright sun"),
 ("s11b", None, ["26","28"], "the camel and the falcon look surprised, eyes wide, mouths open"),
 ("s11", None, ["27","29"], "the old tortoise sits smiling at the red rock and waves her hand warmly"),
 ("s12", {"rahhal":(0.22,0.45),"shaheen":(0.45,0.5),"hasat":(0.8,0.5)}, ["30","31"], "the three friends drink water from the spring and smile, water rippling"),
 ("s13", {"rahhal":(0.3,0.45),"shaheen":(0.5,0.5),"hasat":(0.72,0.5)}, ["32","33","34"], "the three friends stand together at sunset, swaying happily, warm light"),
 ("s14", None, ["35","36"], "the cartoon falcon on a palm branch at night looks up amazed at a glowing golden shape twinkling among the stars, stars twinkling"),
]

def crop(img, fx, fy, out, zoom=1.6):
    im = Image.open(f"{EP}/{img}.jpg"); w, h = im.size
    cw, ch = int(w/zoom), int(h/zoom)
    x = min(max(0, int(fx*w - cw/2)), w-cw); y = min(max(0, int(fy*h - ch/2)), h-ch)
    im.crop((x, y, x+cw, y+ch)).resize((w, h), Image.LANCZOS).save(out, quality=95)

def plan():
    jobs = []
    for img, focus, lines, action in SHOTS:
        for i, l in enumerate(lines):
            spk = SPK[l]; need = LD[l] + GAP + (0.6 if i == len(lines)-1 else 0)
            n = math.ceil(need / 5.0)
            for k in range(n):
                cid = f"{l}_{k}"
                if spk in WHO and k % 2 == 0:
                    src = f"{EP}/{img}.jpg"
                    if focus and spk in focus and not (i == 0 and k == 0):
                        src = f"{D}/in/{img}_{spk}.jpg"
                        if not os.path.exists(src): crop(img, *focus[spk], src)
                    who = WHO[spk]
                    prompt = f"{who} {TALK[spk].format(e=TAG[l])}"
                    if src.endswith(f"{img}.jpg"): prompt = f"{action}; {prompt}"
                else:
                    src = f"{EP}/{img}.jpg"; prompt = action if spk == "narrator" or k else action
                    if spk in WHO and k % 2 == 1: prompt = f"{action}; the friends listen and react with expressive faces"
                dd = min(5.0, max(2.0, need - 5.0*k))
                jobs.append(dict(id=cid, line=l, src=src, prompt=prompt + STYLE, dur=round(dd, 2)))
    json.dump(jobs, open(f"{D}/plan.json","w"), ensure_ascii=False, indent=1)
    print(len(jobs), "clips,", round(sum(j['dur'] for j in jobs),1), "s total")

def gen():
    from gradio_client import Client, handle_file
    jobs = json.load(open(f"{D}/plan.json")); fails = 0
    c = Client('zerogpu-aoti/wan2-2-fp8da-aoti-faster', verbose=False)
    for j in jobs:
        out = f"{D}/clips/{j['id']}.mp4"
        if os.path.exists(out): continue
        try:
            r = c.submit(input_image=handle_file(j['src']), prompt=j['prompt'], steps=6, duration_seconds=j['dur'], seed=42, randomize_seed=False, api_name='/generate_video').result(timeout=300)
            shutil.copy(r[0], out); fails = 0; print("ok", j['id'], flush=True)
        except Exception as e:
            msg = str(e)[:160]; print("FAIL", j['id'], msg, flush=True); fails += 1
            if fails >= 5: print("STOP: repeated failures (quota?)", flush=True); break
            time.sleep(15)
            try: c = Client('zerogpu-aoti/wan2-2-fp8da-aoti-faster', verbose=False)
            except Exception: pass
    done = len([f for f in os.listdir(f"{D}/clips") if f.endswith('.mp4')])
    print(f"DONE {done}/{len(jobs)}", flush=True)

if __name__ == "__main__":
    plan() if sys.argv[1] == "plan" else gen()

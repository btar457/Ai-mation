"""صور الفيديو من FLUX.1-Krea على Hugging Face. الاستخدام: python gen_img.py T,N,E [seed]"""
import os, sys, json, shutil
from gradio_client import Client

STYLE = (", cinematic Arabian Nights film still, medieval Abbasid Baghdad and Mamluk Cairo, photorealistic, warm amber "
         "lamp light against deep teal night shadows, film grain, no text, no letters, no watermark, no logo")
M = ("a Baghdadi merchant in his forties with a short black beard, olive skin, kind tired eyes, wearing a white turban "
     "and a long deep-indigo robe over a cream tunic")
W = ("a heavy-set Mamluk-era Cairo governor in his fifties with a thick grey beard, a large white turban wrapped around a "
     "red cap, an ornate gold brocade kaftan, seated on a cushioned divan in a lamp-lit hall")
P = {
 "R": (f"{M}, standing proudly in his rich shop in a medieval Baghdad souq, piles of silk bolts, brass lamps and a chest of gold coins, warm golden light", 768, 1344),
 "X": (f"{M}, now ruined, sitting alone on the bare floor of an empty room with cracked plaster walls, head in his hands, one beam of cold light from a small window", 768, 1344),
 "D": (f"{M}, asleep on a simple mattress at night, and a tall glowing faceless figure of golden light and smoke leaning over him whispering into his ear, magical", 768, 1344),
 "J": (f"{M}, seen from behind walking alone with a staff along a long desert road toward the horizon at sunset, long shadow, vast dunes", 768, 1344),
 "C": (f"medieval Cairo at night, the courtyard of an old mosque with hanging lamps and minarets, {M} asleep on a straw mat near a column", 768, 1344),
 "T": ("three masked thieves in dark clothes climbing over a mud-brick wall at night with a sack of loot, medieval Cairo rooftops and a minaret behind, moonlight", 768, 1344),
 "G": (f"night, city guards with torches and spears grabbing {M} by the arms inside a mosque courtyard, he looks shocked and confused, smoke and torchlight", 768, 1344),
 "P": (f"{M}, bruised and exhausted, sitting on the floor of a dark stone prison cell, chains, light through iron bars", 768, 1344),
 "W": (f"{W}, stern and suspicious, leaning forward and staring down at the camera", 768, 1344),
 "L": (f"{W}, laughing loudly with his head thrown back, holding his belly, mocking", 768, 1344),
 "K": (f"{M}, kneeling humbly on a carpet before a governor's divan in a lamp-lit hall, seen from the side, guards beside him", 768, 1344),
 "F": (f"extreme close-up of the face of {M}, eyes wide in sudden realization, lips parted, lamp light on one side of his face", 768, 1344),
}
keys = sys.argv[1].split(",")
c = Client(os.environ.get("SPACE","mcp-tools/FLUX.1-Krea-dev"), token=os.environ.get("HF_TOKEN", "hf_dummy"))
seeds = json.load(open("seeds.json")) if os.path.exists("seeds.json") else {}
for k in keys:
    p, w, h = P[k]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 2000 + ord(k)
    try:
        res, s = c.predict(p + STYLE, seed, False, w, h, 4.5, 28, api_name="/infer")
        path = res["path"] if isinstance(res, dict) else res
        shutil.copy(path, f"img/{k}.png")
        seeds[k] = s
        print("OK", k, s, flush=True)
    except Exception as e:
        print("ERR", k, e, flush=True)
    json.dump(seeds, open("seeds.json", "w"))

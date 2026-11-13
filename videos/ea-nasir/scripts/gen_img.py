"""صور الفيديو من FLUX.1-Krea على Hugging Face. الاستخدام: python gen_img.py T,N,E [seed]"""
import os, sys, json, shutil
from gradio_client import Client

STYLE = (", cinematic film still from a historical drama, Old Babylonian Mesopotamia around 1750 BC, photorealistic, "
         "warm low-key lighting, earthy clay and copper tones, film grain, no text, no letters, no watermark, no logo")
NANNI = ("a furious Old Babylonian Mesopotamian man in his forties, long thick black beard in tight curls, long dark hair "
         "tied back, bare head, wearing a heavy fringed wool garment draped over his left shoulder, deep furrowed brow, "
         "burning angry eyes")
EA = ("a sly wealthy Old Babylonian copper merchant in his fifties, oiled grey-black beard in curls, bald head, "
      "wearing a fine fringed wool robe with a coloured border draped over one shoulder, bronze bracelets, a smug half smile")
P = {
 "T": ("A small rectangular baked clay tablet the size of a smartphone, covered edge to edge with dense tiny cuneiform "
       "wedge-shaped signs in neat horizontal ruled lines, slightly chipped corners, warm terracotta clay, museum object "
       "photograph on a pure black background, soft top light, sharp macro detail, the whole tablet visible in the centre", 1024, 1024),
 "N": (f"Close portrait of {NANNI}, sitting in a dim mudbrick room, holding a wet clay tablet in one hand and pressing a reed "
       "stylus into it with the other, leaning toward the camera, oil lamp light on his face", 768, 1344),
 "E": (f"{EA}, standing in the courtyard of a mudbrick house in the city of Ur, a pile of rough round copper ingots at his "
       "feet, arms folded, looking at the camera, late afternoon light", 768, 1344),
 "B": ("Ancient Bronze Age wooden sailing ships with square reed-mat sails, loaded with rough copper ingots, arriving at a "
       "harbour on the Persian Gulf at sunset, palm trees on the shore, calm water, wide shot", 768, 1344),
 "I": ("Close-up of rough cracked low quality copper ingots, round bun-shaped ingots with pitted surfaces and green "
       "corrosion patches, piled on a woven reed mat, dramatic side light, dark background", 1024, 1024),
 "M": ("Two tired Mesopotamian messengers in simple wool kilts walking back empty-handed across a dusty plain at dusk, "
       "long shadows, distant burnt watchtower on the horizon, tense dangerous mood, wide shot", 768, 1344),
 "U": ("The Great Ziggurat of Ur, a massive stepped mudbrick temple tower with long central stairways, rising above a "
       "dense mudbrick city with flat roofs and palm groves, golden hour, haze, epic wide shot", 768, 1344),
 "X": ("Black and white 1920s photograph of an archaeological excavation in the southern Iraqi desert, local workers with "
       "baskets digging out the low mudbrick walls of ancient houses, a British archaeologist in a pith helmet and white "
       "shirt holding a small clay tablet, wide shot", 1024, 1024),
 "G": ("A single small cuneiform clay tablet displayed alone on a stand inside a glass museum case, a narrow spotlight "
       "from above, dark museum gallery, reflections on the glass", 768, 1344),
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

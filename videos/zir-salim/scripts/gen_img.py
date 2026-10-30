import os, sys, json, shutil
from gradio_client import Client
OLD = ("a handsome dignified elderly Arab chieftain-poet in his late sixties, a strikingly handsome noble face with strong "
       "cheekbones, a straight nose and piercing intelligent dark eyes, a neatly groomed long silver-white beard, upright "
       "proud posture, wearing a finely wrapped white linen turban with a tail hanging behind, a rich striped Yemeni burd "
       "mantle in saffron and indigo with embroidered gold-thread borders over a fine plain linen tunic with no buttons and "
       "no pockets, a silver-hilted straight sword at his side, an aura of fallen nobility, no agal, no modern keffiyeh")
YOUNG = ("a 6th-century pre-Islamic Arab warrior-chieftain in his thirties, black beard, intense dark eyes, iron conical "
         "helmet with a mail aventail over a wrapped turban, long chainmail coat belted at the waist, striped Yemeni burd "
         "mantle, a straight double-edged Arabian sword, round leather shield, no plate armor, no agal")
SLAVES = ("two young bearded men, servants, in rough undyed brown wool tunics and simple cloth head wraps, barefoot, "
          "their faces hidden in deep shadow")
DAUGHTER = ("a young pre-Islamic Bedouin Arab woman in her twenties, dark eyes, black hair covered by a long dark red wool "
            "khimar head cover draping over her shoulders, long dark woven wool dress, simple silver bracelets and a bead "
            "necklace, clean natural skin, no face paint, no forehead jewelry, no bindi")
STYLE = (", cinematic film still from an epic historical drama, 6th century pre-Islamic Arabia, photorealistic, "
         "dramatic lighting, rich colors, film grain, vertical composition, the upper third of the frame is empty dark "
         "sky or shadow with nothing in it, no text, no letters, no watermark, no logo, no signature")
P = {
 "A": f"Silhouette of {OLD} riding a camel alone across vast desert dunes at night, huge full moon behind, long shadow on the sand, wide shot, subject in the lower half",
 "B": "Close-up of two curved Arabian daggers half drawn from their sheaths, gleaming under cold moonlight, two hands in shadow, desert night, subject in the lower half",
 "C": f"{YOUNG} on a rearing black horse raising a straight double-edged sword, desert battlefield at sunset, dust in the air, low angle, subject in the lower two thirds",
 "D": "Pre-Islamic Arab tribal battle in the desert, Bedouin horsemen and camel riders in turbans and chainmail clashing with long lances and straight swords and round leather shields, thick clouds of golden dust, epic wide shot, action in the lower two thirds",
 "E": f"Close portrait of {OLD}, tired wise eyes looking into the distance, golden late afternoon light, desert background softly blurred, face in the lower half of the frame",
 "F": f"{OLD} riding a camel followed by {SLAVES} walking beside their camels, crossing golden sand dunes, tiny figures, very wide shot, figures in the lower third",
 "G": f"{SLAVES} sitting side by side behind a small campfire at night, both facing the camera, one man speaks secretly behind his raised hand while the other listens with his eyes turned sideways in suspicion, a gap between their heads, an old man sleeping wrapped in a mantle in the dark background, orange firelight, conspiracy mood, subject in the lower half",
 "H": f"{OLD} sitting alone beside a small campfire at night in the desert, calm knowing expression, orange firelight on his face, a curved sword resting beside him, subject in the lower half",
 "I": "Dark desert night, glowing embers and sparks rising from a dying campfire in the lower part of the frame, deep black and dark blue tones, large empty dark area above, moody atmosphere",
 "K": "Interior of a long low black goat-hair Bedouin tent at night, wooden tent poles, woven wool carpets and cushions, lit by small clay oil lamps, tribe elders in wrapped turbans and wool mantles seated on the carpets listening gravely, two men in brown tunics standing with their backs to the camera, subject in the lower half",
 "L": f"Close-up of {DAUGHTER} standing inside a black goat-hair tent lit by firelight, sharp suspicious look, eyes narrowed with realization, face in the lower half of the frame",
 "M": "An abandoned curved sword and an indigo wool cloak lying half buried in desert sand at dawn, wind blowing fine sand, soft pink and gold light, empty dunes, objects in the lower third",
 "N": f"Tribesmen with torches at night seizing {SLAVES}, the two men kneeling in the sand with their backs to the camera, dramatic torchlight and smoke, subject in the lower half",
 "O": "A lonely rough stone pile marking a grave in the empty desert at dawn, warm golden sunrise on the horizon, wind blowing sand, peaceful and solemn, grave in the lower third",
}
keys = sys.argv[1].split(",")
c = Client("mcp-tools/FLUX.1-Krea-dev", token=os.environ["HF_TOKEN"])
seeds = json.load(open("seeds.json")) if os.path.exists("seeds.json") else {}
for k in keys:
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1000 + ord(k)
    try:
        res, s = c.predict(P[k] + STYLE, seed, False, 768, 1344, 4.5, 28, api_name="/infer")
        path = res["path"] if isinstance(res, dict) else res
        shutil.copy(path, f"img/{k}.png")
        seeds[k] = s
        print("OK", k, s, flush=True)
    except Exception as e:
        print("ERR", k, e, flush=True)
json.dump(seeds, open("seeds.json", "w"))

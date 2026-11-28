STYLE = "cinematic painting, 9th century Abbasid Baghdad, warm oil-lamp light and deep teal shadows, volumetric light, film grain, no text"
BISHR = "a handsome Baghdadi man in his thirties with a short black beard and wavy black hair, olive skin"
IMAM = "a holy man in a simple dark wool robe whose face is hidden by radiant white light"
SHOTS = {
 "B1": f"{BISHR}, in a rich silk robe, running barefoot through a narrow mud-brick alley of old Baghdad at night, glistening tears on his cheeks, desperate face, hanging brass oil lanterns, motion",
 "B2": f"night party in a rich Baghdad mansion, {BISHR} reclining on silk cushions laughing with a wine cup, musicians with lutes and drums, dancers, candles and lamps",
 "B3": f"{IMAM} walking alone at night along a quiet old Baghdad street past the brightly lit gate of a rich mansion",
 "B4": "a young servant girl in a simple dress and headscarf at the gate of a rich Baghdad mansion at night, tossing a basket of rubbish into the street, looking up surprised, lamp light from the gate",
 "B5": f"close-up of {BISHR} on silk cushions, his wine cup frozen in his hand, face shocked and pale as realization hits him, eyes filling with tears, candle light",
 "B6": f"dawn in a dusty Baghdad street, {BISHR}, barefoot, kneeling and weeping at the feet of {IMAM} who rests a hand gently on his shoulder, golden light",
 "B7": f"{BISHR}, now older and ascetic in a simple coarse wool robe, walking barefoot through a busy Baghdad market, people turning to look at his bare feet",
 "B8": "close-up of bare dusty feet walking on a stone road in old Baghdad, morning light, dust",
}
# الجولة الثانية: إزالة التكرار، وخطاف بلا خطوط سوداء على العينين
SHOTS.update({
 "B1": f"{BISHR}, in a rich silk robe, running barefoot through a narrow mud-brick alley of old Baghdad at night, his eyes red and wet, desperate anguished face, hanging brass oil lanterns, clean face, motion",
 "B9": f"{BISHR}, barefoot, bursting out of the great carved wooden gate of his lit Baghdad mansion at night, servants and musicians staring after him in surprise",
 "B10": f"seen from behind, {BISHR} running barefoot down a long dark Baghdad alley at night toward a distant figure surrounded by soft white light at the end of the alley",
 "B11": f"{BISHR} on silk cushions with a wine cup, turning to a young servant girl in a headscarf who stands before him speaking, candle-lit room, musicians blurred behind",
 "B12": "seen from behind, a holy man in a simple dark wool robe with a soft glow of light around his head, standing at the lit gate of a rich Baghdad mansion at night, speaking to a young servant girl holding a basket",
 "B13": "close-up of a young servant girl in a simple headscarf at a mansion gate at night, surprised wide eyes, looking up at someone, lamp light on her face",
 "B14": f"{BISHR}, older and ascetic in a simple coarse wool robe, barefoot, praying alone on a straw mat in a quiet old mosque at dawn, peaceful, rays of light",
 "B15": "close-up of a man's bare dusty feet walking on an old stone road in Baghdad, the hem of a coarse wool robe, warm morning light, dust",
})
ROUND2 = ["B1", "B15", "B9", "B10", "B11", "B13", "B12", "B14"]

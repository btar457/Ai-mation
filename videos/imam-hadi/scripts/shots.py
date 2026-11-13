"""اللقطات: (المعرّف، البرومبت). الإمام دائماً بلا ملامح: وجهه نور."""
STYLE = ("cinematic painting, epic Islamic historical drama, 9th century Abbasid Samarra, deep teal shadows and warm "
         "golden candle light, volumetric light, film grain, no text")
IMAM = "a holy man in a simple dark wool robe whose face is hidden by radiant white light"
CALIPH = "an Abbasid caliph with black turban, black beard and gold robe"
SHOTS = {
 "H1": f"inside a lavish candle-lit Abbasid palace hall at night, {CALIPH} sitting on a golden throne frozen in shock holding a golden wine cup, a tear on his cheek, and {IMAM} standing before him seen from behind, glowing light around the holy man",
 "H2": "the city of Samarra at night seen from above, the giant spiral minaret of Samarra (Malwiya, a tall cone-shaped spiral tower) glowing under the moon, palaces with lamps, the Tigris river",
 "H3": "a vast Abbasid palace banquet hall at night, hundreds of candles, silk curtains, carpets, low tables with golden cups and fruit, musicians in the corners, courtiers reclining",
 "S1": f"two sly courtiers whispering into the ear of {CALIPH} in a dim palace corner, candle light, conspiracy mood",
 "S2": f"close-up of {CALIPH} frowning with suspicion, narrowed eyes, candle light on half his face",
 "S3": "armed Turkish soldiers of the Abbasid army with helmets, lances and flaming torches riding horses fast through narrow mud-brick streets of Samarra at night, dust and smoke",
 "S4": "soldiers with torches smashing open the wooden door of a humble mud-brick house at night, splinters flying, torch light",
 "S5": f"a small bare dark room with no furniture, the floor covered only with sand and pebbles, {IMAM} kneeling alone reading a Quran on a simple wooden stand, a small clay oil lamp, peaceful holy light filling the room",
 "S6": f"seen from behind: armed soldiers with torches frozen in the doorway of a bare room, staring at {IMAM} kneeling in prayer inside, light from the holy man spilling toward them",
 "S7": "soldiers searching an empty bare room with torches, overturned simple mats, finding nothing, only sand and pebbles on the floor",
 "S8": f"night, armed soldiers with torches escorting {IMAM} through the dark streets of Samarra toward a great palace, the spiral minaret in the distance",
 "S9": "huge ornate palace doors opening at night revealing a bright golden banquet hall full of candles inside, guards on both sides",
 "S10": f"{CALIPH} reclining on silk cushions drinking from a golden wine cup, candles and musicians around him, decadent mood",
 "S11": f"{CALIPH} on cushions extending a golden wine cup toward {IMAM} who is seated calmly beside him, the glowing light of the holy man",
 "S12": "close-up of a calm hand in a dark wool sleeve gently raised to refuse a golden wine cup held out by a hand with jeweled rings, soft holy light",
 "S13": f"{CALIPH} leaning forward commanding with a raised finger, arrogant smirk, candle-lit palace hall behind him",
 "P1": "a mighty fortress on the peaks of steep mountains at night, armored guards with spears standing watch on the walls, cold moonlight, clouds",
 "P2": "a row of royal stone tombs and sand graves in a desolate desert at dusk, a golden crown lying abandoned on a grave, wind blowing sand",
 "P3": "an abandoned royal throne room covered in dust and cobwebs, empty golden thrones, crowns and silk robes lying on the dusty floor, beams of pale light",
 "P4": "an abandoned ruined palace at night, torn silk curtains and canopies swaying in the wind, moonlight through broken arches, no people",
 "P5": "inside an ancient dark stone tomb, a cracked golden crown resting on a dusty stone sarcophagus, dust in a beam of light, eerie silence",
 "P6": "an overturned royal banquet table in a ruined hall, spilled golden cups, scattered rotten fruit, dust and dry leaves, desolation",
 "E1": "frightened courtiers in a candle-lit palace hall looking anxiously toward the throne, holding their breath",
 "E2": f"{CALIPH} weeping, head bowed, tears running into his black beard, his golden wine cup falling from his hand, candle light",
 "E3": "palace servants carrying away clay wine jars and golden cups from a banquet hall, candles being put out",
 "E4": f"dawn, {IMAM} walking out through the great gate of the palace, guards lowering their heads respectfully, golden morning light",
 "E5": "the ruins of the Abbasid palaces of Samarra at sunset, crumbling mud-brick walls and arches, the giant spiral minaret of Samarra (Malwiya) in the background, empty and silent",
}
# لقطات مخصصة إضافية (ملاحظات المستخدم: لا تكرار، والصورة تطابق الكلام، وتأثر الحاضرين)
COURT = "courtiers and servants in turbans and silk robes"
SHOTS.update({
 "E2": f"close-up of {CALIPH} weeping uncontrollably, tears streaming down his cheeks into his black beard, head bowed, his golden wine cup slipping from his trembling hand, candle light",
 "E1": f"{COURT} in a candle-lit palace hall weeping, some covering their faces with their hands, others with tears on their cheeks, deeply moved, heads bowed",
 "R1": f"close-up of {CALIPH} listening in shock, face turned pale, eyes wide and glistening, holding a golden wine cup frozen in mid-air, candle light, silence",
 "R2": f"{COURT} frozen in fear in a candle-lit palace hall, holding their breath, staring anxiously toward the throne",
 "S10": f"{CALIPH} reclining on silk cushions drinking from a golden wine cup, musicians with lutes and drums around him, candle-lit palace hall, decadent night feast",
 "S11": f"{CALIPH} on silk cushions holding out a golden wine cup toward {IMAM} seated calmly beside him, candle-lit palace hall",
 "S12": "close-up of a calm hand in a dark wool sleeve raised gently to refuse a golden wine cup offered by a hand with jeweled gold rings, soft holy light, candle light",
 "E4": f"dawn, {IMAM} walking out through the great gate of the palace, guards lowering their heads respectfully, golden morning light",
})
PRIORITY = ["E2", "E1", "R1", "R2", "S10", "S11", "S12", "E4"]

"""جدول اللقطات من iraq-museum-video.md (القسم 3): (الرقم، التعليق، نص الشاشة، الترجمة الإنجليزية، برومبت الصورة، الحركة)."""
STYLE = ("cinematic 2D illustrated style, muted warm palette with dusty amber and deep teal shadows, film grain, "
         "dramatic volumetric light, vertical 9:16 composition, no text, no logos, no real identifiable faces")
BASSETKI = ("the Bassetki statue: a seated nude male figure in dark copper, cast only from the waist down, round base "
            "with an Akkadian inscription")
WARKA = ("the Warka Vase: a tall slender alabaster vase, about one meter high, carved in horizontal bands of reliefs "
         "showing water, plants, animals and a procession of naked men carrying offerings")
MASK = "the Mask of Warka: a life-size white marble female face, empty eye sockets and eyebrows, calm expression"
# motion: zin, zout, panup, pandown, panh, shake, still_zin
SHOTS = [
 (1, "تمثال عمره أربع آلاف سنة…", "4000 سنة", "A 4,000-year-old statue…",
  f"close-up of {BASSETKI} half-submerged in dark sludge inside a cesspit, flashlight beam hitting it", "zin"),
 (2, "لكوه مدفون بحفرة مجاري… مدهون بالشحم.", "بحفرة مجاري", "…found in a cesspit, smeared with grease.",
  f"hands in gloves lifting the greasy copper statue ({BASSETKI}) out of a pit at night, mud dripping", "panup"),
 (3, "بس شلون وصل هناك؟", "شلون وصل؟", "But how did it get there?",
  "empty dark museum hall, a single empty display pedestal under a spotlight", "zin"),
 (4, "نرجع لنيسان ألفين وثلاثة. بغداد بنص الحرب.", "نيسان 2003", "April 2003. Baghdad, mid-war.",
  "wide view of the Baghdad city skyline at dusk with domes and minarets, several thick black smoke columns rising into an orange sky, dark silhouettes of date palm trees in the foreground, war atmosphere", "panh"),
 (5, "وبنص هاي الفوضى، أكو بناية وحدة بيها تاريخ العالم كله.", "المتحف العراقي", "The Iraq Museum.",
  "exterior of a grand museum building with arched entrance, empty street, dust in the air", "zin"),
 (6, "المتحف العراقي. بيه قطع من أول مدن عرفها البشر.", "أول المدن", "Relics from humanity's first cities.",
  f"interior gallery: {WARKA} in a glass case, ancient tablets and statues around it, warm light", "panh"),
 (7, "الموظفين طلعوا قبل القتال… والأبواب بقت بلا حماية.", "بلا حماية", "The staff left. The doors stood unguarded.",
  "heavy museum doors slightly open, street outside empty, scattered papers on the floor", "zout"),
 (8, "وبعد يومين، ناس دخلت.", "دخلوا", "Then people came in.",
  "silhouettes of many people running through a museum corridor, motion blur, dust", "shake"),
 (9, "كسروا الواجهات، شالوا اللي يكدرون يشيلوه.", "", "They smashed cases and took what they could carry.",
  "close-up of a looted museum room: several glass display cases with their glass smashed, sharp glass shards and broken ancient clay pots scattered on the floor, dusty footprints", "zin"),
 (10, "وإناء الوركاء، عمره خمس آلاف سنة… اختفى.", "اختفى", "The Warka Vase, 5,000 years old, was gone.",
  "an empty glass museum display case with only a small round stone base left inside, light falling on it, broken glass around", "zin"),
 (11, "لما رجعوا الموظفين، بيوم اثنعش نيسان، لكوا النهب بعده مستمر.", "12 نيسان", "When staff returned on April 12, the looting was still going on.",
  "museum staff in 2003 clothes standing frozen at a doorway, seen from behind, chaos inside", "still_zin"),
 (12, "بالبداية قالوا: مية وسبعين ألف قطعة انسرقت.", "170,000؟", "Early reports: 170,000 items stolen.",
  "newspaper pages and TV screens filled with breaking news, blurred headlines, no readable text", "zin_fast"),
 (13, "الرقم الحقيقي طلع أقل… بحدود ثلاثطعش ألف. بس اللي صدم المحققين شي ثاني.", "13,000", "The real number was about 13,000. But investigators found something stranger.",
  "an investigator with a flashlight walking down a dark staircase into a basement, seen from behind", "pandown"),
 (14, "اللغز الأول: السرداب.", "اللغز الأول", "Mystery 1: the basement.",
  "dark underground storeroom, rows of metal cabinets, flashlight beam cutting through dust", "zin"),
 (15, "خمس آلاف ختم انسرقت من خزائن مقفلة تحت الأرض. شلون عرفوا مكانها؟", "خزائن مقفلة", "5,000 seals taken from locked cabinets underground. How did they know where to look?",
  "open metal drawers, empty trays that held cylinder seals, a few tiny stone cylinder seals scattered on the floor", "zin"),
 (16, "أكو من شك إنها شغلة من الداخل… بس لليوم محد أثبتها.", "ما انحسمت", "Some suspected an inside job. It was never proven.",
  "extreme close-up of a single old brass key lying on a dusty dark concrete floor, a thin beam of light falling on the key, everything else in darkness, macro shot, no people", "zin_slow"),
 (17, "اللغز الثاني: الذهب.", "اللغز الثاني", "Mystery 2: the gold.",
  "front view of a massive round steel bank vault door with thick locking bolts and a big wheel handle, in a dark concrete basement, deep shadows, no people", "zin"),
 (18, "ذهب النمرود كان مخبى بقبو البنك المركزي. القبو غرق بمياه المجاري… بس لما فتحوه، الذهب طلع سالم.", "سالم", "The Nimrud gold, hidden in a flooded bank vault, survived.",
  "flooded bank vault with murky water, a glint of ancient Assyrian gold jewelry inside metal boxes", "zin"),
 (19, "اللغز الثالث: ليش رجعوه؟", "اللغز الثالث", "Mystery 3: why bring it back?",
  "an old car parked in front of a museum gate in daytime, trunk closed", "zin"),
 (20, "المتحف أعلن عفو. وبيوم اثنعش حزيران، وكفت سيارة كدام المتحف… وبصندوقها إناء الوركاء. مكسّر، بس موجود.", "12 حزيران", "On June 12, a car pulled up. The Warka Vase was in the trunk, broken but there.",
  f"an open car trunk with a blanket revealing the broken pieces of {WARKA}", "zin"),
 (21, "وقناع الوركاء، وجه عمره أكثر من خمس آلاف سنة، لكوه مدفون ورا مزرعة شمال بغداد.", "", "The Mask of Warka was found buried behind a farm north of Baghdad.",
  f"{MASK}, half-buried in farm soil among palm trees, morning light", "panup"),
 (22, "والتمثال اللي بدينا بيه؟ تمثال باسطكي. طلع من حفرة المجاري، ورجع للمتحف بيوم إحدعش تشرين الثاني، ويّا أكثر من ثمنمية قطعة رجّعوها.", "رجع", "The Bassetki statue returned to the museum on Nov 11, 2003.",
  f"the clean {BASSETKI} back on a museum pedestal, spotlight, other recovered small artifacts around", "zout"),
 (23, "آلاف القطع رجعت… وآلاف بعدها ضايعة لليوم. تتوقع وين صارت؟ اكتبلي بالتعليقات.", "وين صارت؟", "Thousands are still missing. Where do you think they went?",
  "long museum hall with some empty pedestals among filled ones, dramatic light", "zout_long"),
]

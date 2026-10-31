# فريق الواحة: بطاقات الشخصيات

قناة يوتيوب للأطفال من 6 إلى 10 سنوات، بالفصحى المبسطة. تجمع المغامرة والتعليم والرياضة.

## قالب الأسلوب الثابت (يُلصق في آخر كل برومبت)

```
Pixar-like stylized 3D render for a children's animated series, soft rounded shapes,
big expressive eyes, vibrant saturated colors, soft warm morning light, clean simple
background, friendly cheerful mood, high detail
```

البرومبت السلبي:

```
text, watermark, logo, humans, scary, realistic photo, extra limbs, deformed, blurry, low resolution
```

## الشخصيات

| | رحّال | شاهين | حَصاة |
|---|---|---|---|
| النوع | جمل صغير | صقر شاب | سلحفاة عجوز |
| الدور | الرياضة والحماس | المعلومة والخريطة | الحكمة والحل |
| العيب المحبَّب | يتسرّع | يتباهى بما يعرف | بطيئة جداً |
| العلامة الثابتة | عصابة رأس حمراء ووشاح أحمر | حقيبة مستكشف فيروزية فيها خريطة | نظارة مستديرة وعصا خشبية |
| اللون الغالب | كراميل وأحمر | بني وكريمي وذهبي | زيتوني وبيج |
| العبارة المتكررة | "هيا نتسابق!" | "من فوق أرى كل شيء!" | "على مهلك يا صغيري…" |

العلامة الثابتة هي ما يحفظ هوية الشخصية بين اللقطات، فلا تُحذف من أي برومبت.

## البرومبتات

### 1. صورة الفريق (16:9)، المرجع الأول

```
Character lineup for a children's 3D animated series, three cute original cartoon animal
friends standing side by side on a warm golden sand dune at a desert oasis with palm trees
and blue water: LEFT a small energetic baby camel with soft caramel fur, big round shiny
brown eyes, a fluffy tuft of hair on his head, one hump, wearing a red sports headband and
a small red neck scarf, jumping with a joyful open smile; CENTER a young falcon with brown
and cream feathers, golden eyes, wearing a tiny teal explorer satchel with a rolled map,
one wing pointing forward, confident smile; RIGHT a gentle old tortoise with an olive-green
patterned shell, small round spectacles, kind eyes, holding a little wooden walking stick,
calm warm smile. Full body, clear silhouettes, + قالب الأسلوب
```

### 2. رحّال (1:1)، أمامي وجانبي

```
Character turnaround sheet, front view and side view of the same small energetic baby camel,
soft caramel fur, big round shiny brown eyes, fluffy tuft of hair on head, one hump,
red sports headband, small red neck scarf, joyful open smile, plain light sand background,
+ قالب الأسلوب
```

### 3. شاهين (1:1)

```
Character turnaround sheet, front view and side view of the same young falcon, brown and
cream feathers, golden eyes, tiny teal explorer satchel with a rolled map, confident smile,
one wing raised, plain light sky-blue background, + قالب الأسلوب
```

### 4. حَصاة (1:1)

```
Character turnaround sheet, front view and side view of the same gentle old tortoise,
olive-green patterned shell, small round spectacles, kind eyes, little wooden walking stick,
calm warm smile, plain light green background, + قالب الأسلوب
```

## طريقة التوليد

1. ولّد صورة الفريق أولاً بـ seed ثابت (2026)، واختر أفضل نسخة من 3–4 محاولات.
2. ولّد بطاقة كل شخصية من صورة الفريق عبر FLUX Kontext أو img2img بقوة نحو 0.55، لا من الصفر، حتى يبقى الأسلوب واحداً.
3. كل مشهد لاحق يبدأ من بطاقة الشخصية نفسها.

النماذج المقترحة: Qwen-Image على Hugging Face لأنه الأقوى في الأسلوب الكرتوني، أو FLUX klein عبر Worker الخاص بك في Cloudflare.

## الصور المرجعية المعتمدة (31 أكتوبر 2026)

| الملف | المصدر |
|---|---|
| `refs/team.png` | Qwen-Image، 16:9، seed 314، برومبت الفريق بعد التصحيح |
| `refs/rahhal.png` · `refs/shaheen.png` · `refs/hasat.png` | FLUX.1 Kontext Dev من قصّ صورة الفريق، seed 2026 |

تصحيحات لازمة في برومبت الفريق: "clearly a camel with a long curved neck, long thin legs, one round hump"، وإلا خرج رحّال كخروف. و"pointing with its wing feathers, bird wings only"، وإلا أشار شاهين بإصبع بشري. ووجه حَصاة يحتاج "olive-green skin, not white".

كل مشهد قادم يبدأ من هذه الملفات عبر Kontext، لا من الصفر.

## دروس توليد المشاهد (الحلقة 1)

- **مشاهد المجموعة تبدأ من `refs/team-canvas.png`**، وهي البطاقات الأمامية الثلاث على خلفية فاتحة، لا من `team.png`. صورة الفريق الأولى فيها وجه حَصاة أبيض، فكان يعود في كل مشهد.
- اكتب "Exactly one of each character"، وإلا تكرّر الصقر أو تحوّل الجمل إلى سلحفاة.
- لا تطلب من شاهين حركة بجناحه حين يكون رحّال في الصورة نفسها، فـ Kontext يضع الجناح على الجمل. اطلب نظرة أو تعبيراً فقط، وحرّك الجناح لاحقاً في التحريك.
- اللقطات الفردية تبدأ من البطاقة الأمامية للشخصية على لوحة 16:9.
- البرومبت نفسه مع الـ seed نفسه يعيد الصورة نفسها، فاحفظهما لكل لقطة معتمدة.
- نجاح أول محاولة: 9 من 13. والفشل كان في مشاهد الشخصيتين أو الثلاث.

## الأصوات (صوت مصطفى، عينة 31 أكتوبر)

معالجة كل سطر بـ ffmpeg: `highpass=70, afftdn=nf=-42:nr=14, rubberband, silenceremove (وقفات أطول من 0.45 ث), acompressor`، ثم `loudnorm=I=-16`.

| الشخصية | pitch (rubberband) | tempo | formant | الطبقة الناتجة |
|---|---|---|---|---|
| رحّال | 1.33 (+5 درجات) | 1.08–1.12 | shifted، ليصير صوت طفل | نحو 245 Hz |
| شاهين | 1.20 (+3) | 1.03 | preserved | نحو 165 Hz |
| حَصاة | 0.72 (−6) | 0.93 | preserved | نحو 130 Hz |
| الراوي | 1.00 | 1.00 | — | نحو 140 Hz |

- أداء حَصاة في التسجيل الخام كان أعلى من أداء شاهين (176 مقابل 139 Hz)، لذلك احتاج خفضاً كبيراً. الأفضل أن تُؤدّى حَصاة بصوت أعمق من الأصل.
- ضجيج الغرفة في الخام نحو ‎-42 dB، وهو مرتفع قليلاً.

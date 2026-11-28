# آخر رجل في بغداد (قصة خيالية)

فيديو 9:16، 52 ثانية. شاب يستيقظ فيجد بغداد فارغة، ويصرخ على الشط، ثم يرى في زجاج محل أن الشارع خلفه مزدحم: بغداد لم تفرغ، هو الذي اختفى.

- النص: `scripts/lines.py` (12 جملة بالعامية البغدادية).
- الصوت: `scripts/tts.py` (Gemini TTS، Orus) ثم التضخيم بـ ffmpeg → `voice/voice_a.wav`، ثم `scripts/assemble.py` → `voice/voice.wav` و`timeline.json`.
- الصور: L1–L8 من FLUX.1-Krea (`gen_krea.py`)، وL9–L12 من HiDream-O1 (`gen_hidream.py`). L8 طُليت شاشته، وL12g نسخة الشبح.
- البناء: `python scripts/prep.py` ثم `node scripts/render.cjs video ../out/video_silent.mp4 30` (من داخل scripts) ثم `bash scripts/mix.sh`.
- الناتج: `out/last-man-tiktok.mp4`.

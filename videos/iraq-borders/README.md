# لماذا حدود العراق بهذا الشكل؟ (فيديو تجريبي)

فيديو بأسلوب صحافة الخرائط، مدته 77 ثانية، مبني بـ Remotion. الملف الجاهز: `iraq-borders-demo.mp4`.

## إعادة البناء
```bash
npm install
python3 sfx.py public/music.wav 77 12.1:whoosh 22.9:whoosh 37.3:whoosh 49.4:whoosh 60.6:whoosh 9.3:boom 45.6:boom 19.6:sparkle 69.4:whoosh 74.6:chime
npx remotion ffmpeg -i public/vo.mp3 -i public/music.wav -filter_complex "[0:a]aresample=44100,apad=whole_dur=77[v];[1:a]volume=0.32[m];[v][m]amix=inputs=2:duration=longest:normalize=0[a]" -map "[a]" -ac 2 -t 77 public/mix.wav
npx remotion render src/index.ts Story out/video.mp4 --codec=h264 --crf=20
```
- `geo.mjs`: يستخرج حدود الدول من world-atlas إلى `src/geo.json`.
- `align.py`: يطابق جمل `phrases.txt` مع فترات الصمت في الصوت ليولد `src/subs.json`.

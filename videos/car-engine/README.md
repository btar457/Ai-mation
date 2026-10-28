# كيف يعمل محرّك السيارة؟ (فيديو تجريبي ثلاثي الأبعاد)

فيديو مدته 110 ثوانٍ مبني بـ Remotion و Three.js (عبر @remotion/three). الملف الجاهز: `car-engine-demo.mp4`.

- `src/Engine.tsx`: نموذج المحرك الإجرائي (مكابس، أذرع، كرنك، صمامات، كامات، شمعات) والمشاهد والواجهة.
- `lines.json`: نص التعليق الصوتي، ومولّد بصوت Piper العربي (ar_JO-kareem) في `public/vo/`.
- `src/timeline.json`: توقيت كل جملة وكل مشهد، ومنه يُحسب كل شيء.
- `music.py`: يولّد الموسيقى والمؤثرات وصوت المحرك إلى `public/music.wav`.

## إعادة البناء
```bash
npm install
python3 music.py
npx remotion render src/index.ts Engine out/engine.mp4 --gl=angle --concurrency=3 --timeout=240000
```
ملاحظة: الخامات من نوع Matcap عن قصد، لأن خامات PBR مع خريطة بيئة تجعل الرندر بدون كرت شاشة أبطأ بحوالي 10 مرات.

# مساحة إنتاج فريق الواحة

كل ما يلزم لإكمال الحلقة 1 في أي جلسة جديدة:

```bash
bash production/oasis/restore_workspace.sh <مجلد العمل المؤقت>
```

| المجلد | المحتوى |
|---|---|
| `tts/` | السطور الـ 36 بأصوات Gemini، بصيغة wav ومقصوصة ومفحوصة |
| `anim2/clips/` | 28 لقطة Wan معتمدة. الناقص 25، وقائمتها في `docs/oasis-team/ep01-fix-plan.md` |
| `anim2/in/` | قصّات قريبة للمتكلم من صور المشاهد |
| `anim2/plan.json` | خطة اللقطات الـ 53: الصورة، والبرومبت، والمدة |
| `fonts/` | Cairo ExtraBold وLalezar (رخصة OFL) |
| `scripts/` | `lines.py` للسطور، و`gen_full.py` لأصوات Gemini، و`split.py` للقص والفحص بـ Whisper، و`plan.py` لخطة Wan وتوليدها، و`build2.py` للمونتاج |

**الأسرار المطلوبة في البيئة (Network secrets):**
- Gemini: هيدر `x-goog-api-key` على `generativelanguage.googleapis.com`.
- Hugging Face: `Authorization: Bearer` على `huggingface.co` و`*.hf.space`.

**الخطوة التالية:** `docs/oasis-team/ep01-fix-plan.md`.

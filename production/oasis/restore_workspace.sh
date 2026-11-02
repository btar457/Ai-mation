#!/usr/bin/env bash
# يعيد بناء مساحة العمل المؤقتة لإنتاج فريق الواحة في أي جلسة جديدة.
# الاستخدام: bash production/oasis/restore_workspace.sh <مجلد العمل المؤقت (scratchpad)>
set -euo pipefail
SC="${1:?اكتب مسار مجلد العمل المؤقت}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
P="$REPO/production/oasis"
OLD="/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad"
mkdir -p "$SC"/mouth "$SC"/lip/flap "$SC"/lip/clips "$SC"/lip/sh "$SC"/lip/crops "$SC"/tts/full "$SC"/anim "$SC"/anim2/clips "$SC"/anim2/in "$SC"/fonts "$SC"/edit/png "$SC"/edit/seg
cp "$P"/tts/line_*.wav "$SC"/tts/full/
cp "$P"/scripts/lines.py "$P"/scripts/gen_full.py "$P"/scripts/split.py "$SC"/tts/full/
cp "$P"/scripts/tts2.py "$P"/scripts/check.py "$SC"/tts/ 2>/dev/null || true
cp "$REPO"/docs/oasis-team/ep01/anim/*.mp4 "$P"/scripts/wan.py "$SC"/anim/
cp "$P"/anim2/clips/*.mp4 "$SC"/anim2/clips/; cp "$P"/anim2/in/*.jpg "$SC"/anim2/in/
cp "$P"/anim2/plan.json "$P"/scripts/plan.py "$SC"/anim2/
cp "$P"/fonts/*.ttf "$SC"/fonts/
cp "$P"/scripts/build.py "$P"/scripts/build2.py "$P"/scripts/build3.py "$SC"/edit/
cp "$P"/tts/word_times.json "$SC"/tts/full/
cp "$P"/lip/clips/*.mp4 "$SC"/lip/clips/; cp "$P"/lip/sh/* "$SC"/lip/sh/; cp "$P"/lip/crops/*.jpg "$SC"/lip/crops/
cp "$P"/lip/flap/*.mp4 "$SC"/lip/flap/; cp "$P"/mouth/*.py "$SC"/mouth/
cp "$P"/scripts/jobs.py "$P"/scripts/shaheen.py "$P"/scripts/lc.py "$SC"/lip/
# المسار القديم مكتوب داخل السكربتات، فنستبدله بالجديد
grep -rl "$OLD" "$SC" --include=*.py | xargs -r sed -i "s#$OLD#$SC#g"
pip install -q gradio_client faster-whisper praat-parselmouth >/dev/null 2>&1 || true
echo "تمت الاستعادة في $SC"
echo "LongCat: $(ls "$SC"/lip/clips | wc -l) · شاهين: $(ls "$SC"/lip/sh/*.mp4 | wc -l) · لقطات Wan: $(ls "$SC"/anim2/clips | wc -l)/53 · سطور الصوت: $(ls "$SC"/tts/full/line_*.wav | wc -l)/36"

#!/bin/bash
# دمج الصوت (‎-16 LUFS) مع الموسيقى (أخفض بنحو 15 dB) فوق الفيديو الصامت.
set -e
cd "$(dirname "$0")/.."
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 video_silent.mp4)
# الموسيقى أخفض بنحو 17-18 dB، بلا ترددات عالية تصطدم بالسين والصاد، وتنخفض أكثر تحت الكلام
# الموسيقى 30 ثانية: نكررها مرتين بتداخل 3 ثوانٍ، ثم نضبط مستواها
ffmpeg -y -v error -i music/bed.wav -i music/bed.wav -filter_complex \
 "[0][1]acrossfade=d=3:c1=tri:c2=tri,aresample=48000,atrim=0:$D,lowpass=f=3200,highpass=f=60,loudnorm=I=-35:TP=-9:LRA=11,afade=t=in:d=0.6,afade=t=out:st=$(echo "$D-1.8"|bc):d=1.8[m]" \
 -map "[m]" -ar 48000 -ac 2 music/bed_mix.wav
ffmpeg -y -v error -i video_silent.mp4 -i voice/voice_paused.wav -i music/bed_mix.wav -filter_complex \
 "[1]aresample=48000,pan=stereo|c0=c0|c1=c0,apad,asplit[v][sc];[2][sc]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=400[m];[v][m]amix=inputs=2:duration=longest:normalize=0,atrim=0:$D,alimiter=limit=0.89[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart baghdad-treasure-tiktok.mp4
ffmpeg -hide_banner -i baghdad-treasure-tiktok.mp4 -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1

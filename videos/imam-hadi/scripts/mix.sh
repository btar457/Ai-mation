#!/bin/bash
# يدمج الصوت (‎-16 LUFS) والموسيقى (أخفض بنحو 22 dB مع ducking) فوق الفيديو الصامت → out/imam-hadi.mp4 (‎-14 LUFS)
set -e
cd "$(dirname "$0")/.."
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out/video_silent.mp4)
ffmpeg -y -v error -i out/video_silent.mp4 -i voice/voice.wav -stream_loop -1 -i music/bed.wav -filter_complex \
 "[1]aresample=48000,pan=stereo|c0=c0|c1=c0,apad,asplit=2[v][sc];\
  [2]aresample=48000,aformat=channel_layouts=stereo,atrim=0:$D,lowpass=f=4000,loudnorm=I=-38:TP=-9:LRA=11,afade=t=in:d=1.5,afade=t=out:st=$(echo "$D-3"|bc):d=3[m0];\
  [m0][sc]sidechaincompress=threshold=0.04:ratio=4:attack=30:release=600[m];\
  [v][m]amix=inputs=2:normalize=0:duration=first,atrim=0:$D,loudnorm=I=-14:TP=-1:LRA=11[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart out/imam-hadi.mp4
ffmpeg -hide_banner -i out/imam-hadi.mp4 -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1

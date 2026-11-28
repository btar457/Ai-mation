#!/bin/bash
# الصوت = الدعاء المولّد كما هو (فيه خلفيته)، يُوحَّد إلى ‎-14 LUFS → out/dua-kumayl.mp4
set -e
cd "$(dirname "$0")/.."
ffmpeg -y -v error -i out/video_silent.mp4 -i voice/voice.wav -filter_complex "[1]aresample=48000,loudnorm=I=-14:TP=-1:LRA=11,afade=t=out:st=$(echo "$(ffprobe -v error -show_entries format=duration -of csv=p=0 out/video_silent.mp4)-2"|bc):d=2[a]" \
 -map 0:v -map "[a]" -c:v libx264 -b:v 4300k -maxrate 6000k -bufsize 9000k -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart out/dua-kumayl.mp4

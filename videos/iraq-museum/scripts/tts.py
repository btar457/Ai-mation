"""التعليق الصوتي لكل لقطة بـ edge-tts (ar-IQ-BasselNeural, rate -5%) → audio/NN.mp3"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shots import SHOTS
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env = dict(os.environ, SSL_CERT_FILE="/root/.ccr/ca-bundle.crt")
only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
for n, vo, *_ in SHOTS:
    out = f"audio/{n:02d}.mp3"
    if only and str(n) not in only: continue
    if os.path.exists(out) and not only: continue
    cmd = ["edge-tts", "--voice", "ar-IQ-BasselNeural", "--rate=-5%", "--text", vo, "--write-media", out]
    if os.environ.get("HTTPS_PROXY"): cmd[1:1] = ["--proxy", os.environ["HTTPS_PROXY"]]
    subprocess.run(cmd, check=True, env=env, capture_output=True)
    print("ok", out)

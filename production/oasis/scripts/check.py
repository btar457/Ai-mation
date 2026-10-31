import wave, sys, numpy as np, parselmouth
from faster_whisper import WhisperModel
m=WhisperModel("medium",device="cpu",compute_type="int8")
for n in sys.argv[1:]:
    w=wave.open('t_'+n+'.wav'); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    segs,info=m.transcribe(a,language='ar',beam_size=5); segs=list(segs)
    f=parselmouth.Sound(n+'.wav').to_pitch(pitch_floor=60,pitch_ceiling=500).selected_array['frequency']; f=f[f>0]
    print(n, f"{len(a)/16000:.1f}s {int(np.median(f))}Hz conf {np.exp(np.mean([s.avg_logprob for s in segs])):.2f} |", ' '.join(s.text.strip() for s in segs), flush=True)

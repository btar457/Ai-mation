import subprocess, re, sys, wave, difflib, numpy as np
from lines import LINES
from faster_whisper import WhisperModel
m=WhisperModel("medium",device="cpu",compute_type="int8")
def strip(s): return re.sub(r'[ً-ْـ…!?؟،.,:\-"]','',s).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي').strip()
for ch in sys.argv[1:]:
    voice, lines = LINES[ch]; K=len(lines)
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f'{ch}.wav']))
    out=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-i',f'{ch}.wav','-af','silencedetect=n=-40dB:d=0.3','-f','null','-'],capture_output=True,text=True).stderr
    st=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',out)]; en=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',out)]
    sil=[(e-s,s,e) for s,e in zip(st,en) if s>0.05 and e<dur-0.05]
    cuts=sorted(sorted(sil,reverse=True)[:K-1],key=lambda x:x[1])
    bounds=[0]+[ (s+e)/2 for _,s,e in cuts]+[dur]
    for i,(lid,tag,txt) in enumerate(lines):
        a,b=bounds[i],bounds[i+1]; f=f'line_{lid}.wav'
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-ss',str(a),'-to',str(b),'-i',f'{ch}.wav','-af','silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse','-ar','16000',f't_{lid}.wav'])
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-ss',str(a),'-to',str(b),'-i',f'{ch}.wav','-af','silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.1','-ar','44100',f])
        w=wave.open(f't_{lid}.wav'); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
        segs=list(m.transcribe(x,language='ar',beam_size=5)[0]); hyp=' '.join(s.text for s in segs)
        r=difflib.SequenceMatcher(None,strip(hyp),strip(txt)).ratio()
        print(f"{lid} {ch:8s} {len(x)/16000:4.1f}s match {r:.2f} {'OK ' if r>0.7 else 'CHK'} | {hyp.strip()}",flush=True)

import json, numpy as np, wave, importlib.util
spec=importlib.util.spec_from_file_location('sfx','sfx.py')
src=open('sfx.py').read().split('GEN =')[0]; ns={}; exec(src,ns)
SR=44100; T=json.load(open('src/timeline.json')); D=T['total']; S=T['scenes']
np.random.seed(3); mix=ns['pad'](D, root=87.3)*0.8
def add(at,s,g=1.0):
    i=max(0,int(at*SR)); s=s[:len(mix)-i]; mix[i:i+len(s)]+=s*g
for k in ['parts','intake','compress','power','exhaust','cycle','fact']:
    w=ns['whoosh'](); add(S[k][0]+0.5-len(w)/SR, w, 0.7)
pw=[l for l in T['lines'] if l['scene']=='power'][1]['start']-0.2
add(pw, ns['boom'](), 1.0)
add(D-4.4, ns['chime'](), 1.0)
# engine hum: cycle -> end
t0=S['cycle'][0]; t1=D-4.0; n=int((t1-t0)*SR); tt=np.arange(n)/SR
f=np.interp(tt,[0,9,t1-t0],[22,70,78]); ph=2*np.pi*np.cumsum(f)/SR
eng=sum(np.sign(np.sin(k*ph))*0.6/k + np.sin(k*ph)/k for k in (1,2,3,4))
eng+=np.random.randn(n)*0.3
# lowpass
y=0.0; out=np.zeros(n); a=0.08
for i in range(n): y+=a*(eng[i]-y); out[i]=y
out=out/np.abs(out).max()*0.22*np.minimum(1,np.minimum(tt/1.5,(t1-t0-tt)/1.0))
add(t0,out)
mix/=max(1.0,np.abs(mix).max()/0.9)
with wave.open('public/music.wav','wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((mix*32767).astype(np.int16).tobytes())
print('ok',D)

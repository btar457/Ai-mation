import shutil, sys, time
from gradio_client import Client, handle_file
img, wav, prompt, out = sys.argv[1:5]
c=Client('victor/LongCat-Video-Avatar-1.5',verbose=False); t=time.time()
r=c.submit(image_path=handle_file(img),audio_path=handle_file(wav),prompt=prompt,resolution='480p',seed=42,vocal_mode='Clean speech (fast)',acceleration='DBCache faster',api_name='/generate').result(timeout=840)
p=r if isinstance(r,str) else (r.get('video') if isinstance(r,dict) else r[0])
if isinstance(p,dict): p=p.get('video') or p.get('path')
shutil.copy(p,out); print('ok',out,round(time.time()-t),'s',flush=True)

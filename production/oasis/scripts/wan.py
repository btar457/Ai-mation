import sys, shutil
from gradio_client import Client, handle_file
c=Client('zerogpu-aoti/wan2-2-fp8da-aoti-faster',verbose=False)
E='/home/user/Ai-mation/docs/oasis-team/ep01/'
jobs={
 's01':'the cartoon baby camel stands on a sand dune and turns its head left and right looking around worried and lost, sand blowing in the wind, slow camera orbit, smooth 3D animation',
 's08':'strong desert sandstorm, sand swirling and blowing hard around the cartoon baby camel, the camel squeezes its eyes shut and lowers its head against the wind, scarf flapping, smooth 3D animation',
 's05':'the cartoon falcon flies and dives fast across the blue sky over the dunes, wings flapping strongly, dynamic smooth 3D animation',
 's06':'the three cartoon friends are ready to race, then the camel dashes forward fast out of the frame, the falcon flaps its wings and takes off, the tortoise takes one slow step, smooth 3D animation',
}
for k in sys.argv[1:]:
    try:
        r=c.predict(input_image=handle_file(E+k+'.jpg'),prompt=jobs[k],steps=6,duration_seconds=3.5,seed=42,randomize_seed=False,api_name='/generate_video')
        shutil.copy(r[0],f'{k}.mp4'); print('ok',k,flush=True)
    except Exception as e: print('FAIL',k,str(e)[:200],flush=True)

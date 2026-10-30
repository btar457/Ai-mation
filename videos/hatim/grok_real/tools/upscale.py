import onnxruntime as ort, numpy as np, cv2, subprocess, sys, imageio_ffmpeg, os
s = ort.InferenceSession('/root/upscale/model.onnx'); inp = s.get_inputs()[0].name
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
for src in sys.argv[1:]:
    out = src.replace('/grok/', '/grok/up/')
    if os.path.exists(out): continue
    cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS) or 24
    p = subprocess.Popen([FF, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                          '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    n = 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        x = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB).astype(np.float32).transpose(2, 0, 1)[None] / 255
        y = (np.clip(s.run(None, {inp: x})[0][0].transpose(1, 2, 0), 0, 1) * 255).astype(np.uint8)
        y = cv2.cvtColor(y, cv2.COLOR_RGB2BGR)
        h, w = y.shape[:2]; sc = max(W / w, H / h)
        y = cv2.resize(y, (round(w * sc), round(h * sc)), interpolation=cv2.INTER_AREA)
        oy, ox = (y.shape[0] - H) // 2, (y.shape[1] - W) // 2
        p.stdin.write(np.ascontiguousarray(y[oy:oy + H, ox:ox + W]).tobytes()); n += 1
    p.stdin.close(); p.wait(); print('ok', out, n, flush=True)

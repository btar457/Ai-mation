import numpy as np, cv2, subprocess, sys, json, imageio_ffmpeg, onnxruntime as ort
W, H, FPS, DUR = 1080, 1920, 30, 8.0
FF = imageio_ffmpeg.get_ffmpeg_exe()
ds = ort.InferenceSession('/root/depth/model.onnx')
def depth(im):
    h, w = im.shape[:2]; Hh, Ww = 518, int(round(518 * w / h / 14) * 14)
    x = cv2.resize(cv2.cvtColor(im, cv2.COLOR_BGR2RGB), (Ww, Hh), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    d = ds.run(None, {'pixel_values': x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0]
    d = cv2.resize(d, (w, h), interpolation=cv2.INTER_CUBIC); return (d - d.min()) / (d.max() - d.min() + 1e-9)
def ease(x): return x * x * (3 - 2 * x)
def render(src, out, z0, z1, x0, x1, y0, y1, k=1.0, gx0=0, gx1=0, gy0=0, gy1=0):
    img = cv2.imread(src)
    s = max(W * 1.12 / img.shape[1], H * 1.12 / img.shape[0])
    img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LANCZOS4)
    dep = depth(img).astype(np.float32)
    dep = cv2.dilate(dep, np.ones((15, 15), np.uint8)); dep = cv2.GaussianBlur(dep, (0, 0), 6)
    ih, iw = dep.shape; cx, cy = iw / 2, ih / 2
    uu, vv = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    p = subprocess.Popen([FF, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    N = int(DUR * FPS)
    for f in range(N):
        t = ease(f / (N - 1)); sway = np.sin(f / FPS * 0.9) * 3
        z = z0 + (z1 - z0) * t; px = (x0 + (x1 - x0) * t + sway) * k; py = (y0 + (y1 - y0) * t) * k
        gx = gx0 + (gx1 - gx0) * t; gy = gy0 + (gy1 - gy0) * t
        X = uu + (iw - W) / 2 + gx; Y = vv + (ih - H) / 2 + gy
        d = cv2.remap(dep, X, Y, cv2.INTER_LINEAR)
        sc = 1 + z * (0.35 + 0.9 * d) * k
        mx = cx + gx + (X - cx - gx) / sc - px * d; my = cy + gy + (Y - cy - gy) / sc - py * d
        fr = cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait(); print('ok', out, flush=True)
G = '/root/hatim/grok/'
J = {
 '01': (G+'scenes/s01.jpg', dict(z0=0.0, z1=0.10, x0=0, x1=0, y0=10, y1=-10)),
 '02': (G+'scenes/s02.jpg', dict(z0=0.02, z1=0.10, x0=-20, x1=20, y0=0, y1=0)),
 '03': (G+'scenes/s03.jpg', dict(z0=0.02, z1=0.13, x0=0, x1=0, y0=25, y1=-20)),
 '04': (G+'scenes/s04.jpg', dict(z0=0.04, z1=0.07, x0=0, x1=0, y0=0, y1=0, gx0=-650, gx1=450)),
 '06': (G+'scenes/s06.jpg', dict(z0=0.03, z1=0.10, x0=-35, x1=35, y0=0, y1=0)),
 '07': (G+'derived/s07_up.jpg', dict(z0=0.03, z1=0.09, x0=40, x1=-40, y0=0, y1=0)),
 '09': (G+'scenes/s09.jpg', dict(z0=0.00, z1=0.10, x0=-20, x1=20, y0=0, y1=0)),
 '12': (G+'scenes/s12.jpg', dict(z0=0.00, z1=0.08, x0=0, x1=0, y0=-15, y1=15)),
 '13': (G+'scenes/s13.jpg', dict(z0=0.03, z1=0.11, x0=-30, x1=20, y0=0, y1=0)),
 '15': (G+'derived/s15_up.jpg', dict(z0=0.02, z1=0.12, x0=-25, x1=25, y0=0, y1=0)),
 '16': (G+'scenes/s17.jpg', dict(z0=0.0, z1=0.02, x0=0, x1=0, y0=0, y1=0, gy0=-95, gy1=-40)),
 '17': (G+'scenes/s17.jpg', dict(z0=0.02, z1=0.10, x0=0, x1=0, y0=0, y1=-20, gy0=-40, gy1=0)),
 '19': (G+'derived/s19_up.jpg', dict(z0=0.00, z1=0.14, x0=0, x1=0, y0=0, y1=0)),
 '20': (G+'scenes/s20.jpg', dict(z0=0.00, z1=0.12, x0=0, x1=0, y0=15, y1=-10)),
}
for n in sys.argv[1:]:
    src, kw = J[n]; render(src, f'/root/hatim/grok/par/p{n}.mp4', **kw)

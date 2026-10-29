import numpy as np, cv2, subprocess, sys
W, H, FPS, DUR = 1080, 1920, 30, 8.0
FF = ['/usr/local/lib/python3.13/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2']
# per-scene camera: zoom start/end, pan x start/end, pan y start/end (in px at depth=1), parallax strength
P = {
 2: (0.00, 0.10, 0, 0, 0, 0, 1.0), 3: (0.02, 0.12, 0, 0, 30, -20, 1.0), 6: (0.04, 0.06, -60, 60, 0, 0, 1.0),
 7: (0.04, 0.07, 60, -60, 0, 0, 1.0), 8: (0.00, 0.10, 20, -20, 0, 0, 1.0), 11: (0.02, 0.14, 0, 0, 10, -10, 1.0),
 13: (0.03, 0.10, -40, 20, 0, 0, 1.0), 14: (0.02, 0.11, 30, -10, 0, 0, 1.0), 15: (0.03, 0.10, -30, 30, 0, 0, 1.0),
 16: (0.05, 0.08, 0, 0, -60, 45, 1.1), 17: (0.04, 0.10, 0, 0, 50, -30, 1.0), 18: (0.02, 0.10, -20, 20, 0, 0, 1.0),
 19: (0.02, 0.12, 0, 0, 0, -20, 1.0), 20: (0.00, 0.12, 0, 0, 20, -10, 1.0), 21: (0.00, 0.18, 0, 0, 0, 0, 0.8),
 22: (0.04, 0.16, -15, 15, 0, 0, 0.8),
}
def ease(x): return x * x * (3 - 2 * x)
def render(n):
    z0, z1, x0, x1, y0, y1, k = P[n]
    img = cv2.imread(f'/root/hatim/img/scenes/s{n:02d}.png')
    dep = cv2.imread(f'/root/hatim/depth/s{n:02d}.png', 0).astype(np.float32) / 255
    s = max(W * 1.12 / img.shape[1], H * 1.12 / img.shape[0])
    img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4)
    dep = cv2.resize(dep, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    dep = cv2.dilate(dep, np.ones((15, 15), np.uint8)); dep = cv2.GaussianBlur(dep, (0, 0), 6)
    ih, iw = dep.shape; cx, cy = iw / 2, ih / 2
    uu, vv = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    ox, oy = (iw - W) / 2, (ih - H) / 2
    sharpen = np.array([[0, -0.4, 0], [-0.4, 2.6, -0.4], [0, -0.4, 0]], np.float32)
    p = subprocess.Popen(FF + ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                               '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', f'/root/hatim/vid/p{n:02d}.mp4'], stdin=subprocess.PIPE)
    N = int(DUR * FPS)
    for f in range(N):
        t = ease(f / (N - 1)); sway = np.sin(f / FPS * 0.9) * 4
        z = z0 + (z1 - z0) * t; px = (x0 + (x1 - x0) * t + sway) * k; py = (y0 + (y1 - y0) * t) * k
        X = uu + ox; Y = vv + oy
        d = cv2.remap(dep, X, Y, cv2.INTER_LINEAR)
        scale = 1 + z * (0.35 + 0.9 * d) * k
        mx = cx + (X - cx) / scale - px * d
        my = cy + (Y - cy) / scale - py * d
        fr = cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        p.stdin.write(cv2.filter2D(fr, -1, sharpen).tobytes())
    p.stdin.close(); p.wait(); print('ok', n, flush=True)
for n in map(int, sys.argv[1:]): render(n)

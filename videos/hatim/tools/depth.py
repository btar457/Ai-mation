import numpy as np, onnxruntime as ort, cv2, glob, os
s = ort.InferenceSession('/root/depth/model.onnx')
for f in sorted(glob.glob('/root/hatim/img/scenes/s*.png')):
    im = cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2RGB)
    h, w = im.shape[:2]; H, W = 518, int(round(518 * w / h / 14) * 14)
    x = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    d = s.run(None, {'pixel_values': x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0]
    d = cv2.resize(d, (w, h), interpolation=cv2.INTER_CUBIC)
    d = (d - d.min()) / (d.max() - d.min() + 1e-9)
    cv2.imwrite('/root/hatim/depth/' + os.path.basename(f), (d * 255).astype(np.uint8))
    print(os.path.basename(f), flush=True)

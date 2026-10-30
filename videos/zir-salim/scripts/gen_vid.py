import os, sys, shutil, time
from gradio_client import Client, handle_file
M = {
 "A": "The old man walks slowly forward across the sand leaning on his staff, his striped mantle and turban tail move in the wind, the moon stays fixed in the sky.",
 "B": "The two hands slowly draw the curved daggers upward, the blades gleam in the moonlight, the moon stays still.",
 "C": "The black horse stamps and tosses its head, the knight holds the straight sword high and steady, dust blows across the battlefield.",
 "D": "The horsemen charge forward through clouds of golden dust, banners flutter in the wind, the camera slowly pushes in.",
 "E": "The old man slowly raises his proud gaze toward the horizon, his silver beard and turban tail move gently in the wind, his hand stays on the sword hilt, the camera stays still.",
 "F": "The camel walks slowly forward carrying the old man, the two men walk beside it, fine sand blows in the wind.",
 "G": "The man on the left whispers secretly behind his hand, the man on the right slowly turns his eyes sideways in suspicion, the campfire flickers, their heads stay apart and they do not touch.",
 "H": "The campfire flickers and sparks rise, the old man slowly closes his eyes, the sword stays still on the ground.",
 "I": "Sparks and glowing embers rise slowly from the campfire into the dark night sky, the flames flicker.",
 "K": "The oil lamps flicker, the seated elders slowly turn their heads toward the two standing men, nobody else moves.",
 "L": "The young woman's eyes slowly widen with realization, the firelight flickers on her face, her head cover stays still.",
 "M": "Fine sand blows across the dunes over the cloak, the sword stays still, the dawn light slowly brightens.",
 "N": "The torches flicker and smoke drifts, the two kneeling men slowly lower their heads in shame, the tribesmen stand still.",
 "O": "Sand blows gently across the desert, the sun slowly rises above the horizon, the stone pile stays still.",
}
NEG = ("色调艳丽, 过曝, 静态, 细节模糊不清, 字幕, 风格, 作品, 画作, 画面, 静止, 整体发灰, 最差质量, 低质量, JPEG压缩残留, 丑陋的, 残缺的, "
       "多余的手指, 画得不好的手部, 画得不好的脸部, 畸形的, 毁容的, 形态畸形的肢体, 手指融合, 静止不动的画面, 杂乱的背景, 三条腿, 背景人很多, 倒着走, "
       "extra people, new person appearing, text, watermark")
c = Client("zerogpu-aoti/wan2-2-fp8da-aoti-faster", token=os.environ["HF_TOKEN"])
for k in sys.argv[1].split(","):
    if os.path.exists(f"clips/{k}.mp4"):
        print("SKIP", k, flush=True); continue
    for attempt in range(2):
        t = time.time()
        try:
            vid, s = c.predict(handle_file(f"img/{k}.png"), M[k], 6, NEG, 5, 1, 1, 42, False, api_name="/generate_video")
            path = vid["video"] if isinstance(vid, dict) else vid
            shutil.copy(path, f"clips/{k}.mp4")
            print("OK", k, round(time.time() - t), flush=True)
            break
        except Exception as e:
            print("ERR", k, str(e)[:300], flush=True)
            time.sleep(20)

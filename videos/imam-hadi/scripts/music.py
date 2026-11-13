"""موسيقى خلفية محلية بـ MusicGen-small (CPU)."""
import sys, torch, scipy.io.wavfile as wf
from transformers import AutoProcessor, MusicgenForConditionalGeneration
torch.manual_seed(int(sys.argv[2]) if len(sys.argv) > 2 else 7)
P = ("solemn spiritual ambient underscore, soft low string drone and distant airy choir pad, slow and reverent, deep and calm, no drums, no percussion, 50 bpm, instrumental")
proc = AutoProcessor.from_pretrained("facebook/musicgen-small")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
inp = proc(text=[P], padding=True, return_tensors="pt")
audio = model.generate(**inp, do_sample=True, guidance_scale=3, max_new_tokens=int(50 * 30))
sr = model.config.audio_encoder.sampling_rate
wf.write(sys.argv[1], sr, audio[0, 0].numpy())
print("done", sr)

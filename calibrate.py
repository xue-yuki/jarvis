"""Run this to find the right CLAP_THRESHOLD for your mic."""
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
chunk_size = int(SAMPLE_RATE * 0.02)

print("Calibrating mic — listening for 10 seconds.")
print("Stay quiet for 3s, then clap a few times, then stay quiet again.\n")

results = []
with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
    for i in range(500):
        chunk, _ = stream.read(chunk_size)
        peak = float(np.abs(chunk).max())
        results.append(peak)
        bar = "#" * int(peak * 40)
        print(f"\r[{i:3d}] peak={peak:.4f}  {bar:<40}", end="", flush=True)

print("\n")
ambient = sorted(results)[:100]
clap_peaks = sorted(results)[-20:]
print(f"Ambient noise max : {max(ambient):.4f}")
print(f"Clap peaks avg    : {sum(clap_peaks)/len(clap_peaks):.4f}")
suggested = (max(ambient) + min(clap_peaks)) / 2
print(f"\nSuggested CLAP_THRESHOLD: {suggested:.2f}")
print(f"Set this value in config.py")

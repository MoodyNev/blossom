import wave
import numpy as np

CHUNK_SIZE = 2048

audio = wave.open("shelter2.wav", "rb")

audio.setpos(48000)
raw_data = audio.readframes(CHUNK_SIZE)

samples = np.frombuffer(raw_data, dtype="<i2")

print("raw bytes:", len(raw_data))
print("sample values:", len(samples))
print(samples[:1000])

print("non-zero samples:", np.count_nonzero(samples))
print(
    "peak:",
    np.max(np.abs(samples.astype(np.int32)))
)

print("raw bytes:", len(raw_data))
print("sample values:", len(samples))
print(samples[:20])


audio.close()
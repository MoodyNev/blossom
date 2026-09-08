"""
foundations
sample rate → resolution in TIME
bit depth   → resolution in AMPLITUDE
samples     → waveform measurements
channels    → separate waveforms (L/R)
peak        → largest sample magnitude
FFT         → frequency content
"""

import wave
import numpy as np

CHUNK_SIZE = 2048

audio = wave.open("shelter2.wav", "rb")

audio.setpos(48000)
raw_data = audio.readframes(CHUNK_SIZE)

#here is where we take the raw samples from the audio itself
samples = np.frombuffer(raw_data, dtype="<i2")
#the problem is that the audio is streo, we need the waves from two sides at the same time
#reshape means we have tuples of two, one left and right
#-1 means numpy figure out how many of those tupples we need 
samples = samples.reshape(-1,2)

#now we also gotta average those two waves
samples = samples.astype(np.float32)

#we now have mono audio :3
#this is more like mathematically mono = (left + right) / 2
#axis = 1 -> average across each row
mono = np.mean(samples, axis=1)

#16-bit PCM -> 
#-32768 ................ 0 ................ +32767
#to this
#-1.0 .................. 0 ................ +1.0
#we are doing this to make the calculation easier
mono = mono / 32768.0

#lil exkurs
#so the sample rate is how often we measure 
#and the bit rate is how precisely each mesurement needs to be stored
#16 bit means 2^16 = 65536
#and for pcm (pulse code modulation) that means the positive negative 32k values

print("shape:", mono.shape)
print("first samples:", mono[:10])
print("peak:", np.max(np.abs(mono)))

peak_index = np.argmax(np.abs(mono))

print("peak index:", peak_index)
print("actual sample:", mono[peak_index])
print("absolute peak:", abs(mono[peak_index]))


audio.close()
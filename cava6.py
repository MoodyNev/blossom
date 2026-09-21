import numpy as np
import wave
import sounddevice as sd
import sys
import subprocess

import time
fps = 0.0
fps_frames = 0
fps_timer = time.perf_counter()

#DEBUG
read_ms = 5.0
analysis_ms = 0.0
render_ms = 0.0
total_ms = 0.0
maxr = 0 
minr = 0
read_times = []

#smoothing stuff simply put e
#how much audio the fft looks at
FFT_SIZE = 2048
#how much new audio arrives each update (step size or such)
HOP_SIZE = 960 #768

SAMPLE_RATE = 48000
#CHUNK_SIZE = 2048
NUM_BANDS = 20
MAX_HEIGHT = 50
CHANNELS = 2
BYTES_PER_SAMPLE= 2

DEVICE = "bluez_output.88_8E_68_E1_9E_A8.1.monitor"

#smoothing constants
smoothed = np.zeros(NUM_BANDS)
ATTACK = 0.75
RELEASE = 0.15
peak_level = 0.01
PEAK_ATTACK = 0.8
PEAK_RELEASE = 0.005

#audio import
#audio = wave.open("shelter2.wav","rb") ee
#SAMPLE_RATE = audio.getframerate()
#CHANNELS = audio.getnchannels()

stream = subprocess.Popen(
    [
        "parec",
        "--raw",
        f"--device={DEVICE}",
        "--format=s16le",
        "--rate=48000",
        "--channels=2",

        "--latency-msec=20",
        "--process-time-msec=10"
    ],
    stdout=subprocess.PIPE
)


#this here defines the regions for the frequencies
window = np.hanning(FFT_SIZE)
band_edges = np.geomspace(40,16000, NUM_BANDS +1)
frequencies = np.fft.rfftfreq(FFT_SIZE, d=1/SAMPLE_RATE)

#hide terminal cursor
print("\033[?25l", end="")

#we are going to read the first complete window
raw_data = stream.stdout.read(FFT_SIZE * CHANNELS * BYTES_PER_SAMPLE)

samples = np.frombuffer(raw_data,dtype="<i2").reshape(-1,CHANNELS)
analysis_buffer = np.mean(samples.astype(np.float32),axis=1) / 32768.0

try:
    while True:
        loop_start = time.perf_counter()

        #DEBUG
        t0 = time.perf_counter()

        raw_data = stream.stdout.read(HOP_SIZE * CHANNELS * BYTES_PER_SAMPLE)

        #DEBUG
        t1 = time.perf_counter()

        read_times.append((t1 - t0) * 1000)

        #if there are no more chunks left then the song ended
        if len(raw_data) == 0:
            break

        samples = np.frombuffer(raw_data,dtype="<i2").reshape(-1, CHANNELS)

        #analysis_samples = samples.astype(np.float32)

        #now we make it mono
        mono = np.mean(samples, axis=1) / 32768.0

        #if the final chunk is smaller than 2048
        #we stop for now
        if len(mono) != HOP_SIZE:
            break

        analysis_buffer[:-HOP_SIZE] = analysis_buffer[HOP_SIZE:].copy()
        analysis_buffer[-HOP_SIZE:] = mono

        #fft
        spectrum = np.fft.rfft(analysis_buffer * window)
        magnitudes = (2* np.abs(spectrum)/np.sum(window))

        #convert fft bins into 16 bands
        band_magnitudes = []

        for i in range(NUM_BANDS):
            low = band_edges[i]
            high = band_edges[i + 1]

            mask = ((frequencies >= low) & (frequencies < high))
            band_values = magnitudes[mask]
            if len(band_values) > 0:
                band_magnitude = np.sqrt(np.mean(band_values ** 2))
            else:
                band_magnitude = 0.0
            band_magnitudes.append(band_magnitude)

        band_magnitudes = np.array(band_magnitudes)

        POWER = 0.5 #here is a variable you can play with but id rather not
        band_magnitudes = band_magnitudes ** POWER

        #kind of looks similar to geompace, but instead of potentials we evenly divide the spaces between values
        weights = np.linspace(0.5,2.0,NUM_BANDS)

        band_magnitudes *= weights

        current_peak = np.max(band_magnitudes)
        if current_peak > peak_level:
            peak_level += PEAK_ATTACK * (current_peak - peak_level)
        else:
            peak_level += PEAK_RELEASE * (current_peak - peak_level)

        normalized = band_magnitudes / max(peak_level, 1e-6)

        normalized = np.clip(normalized, 0.0, 1.0)

        going_up = normalized > smoothed 

        coefficients = np.where(going_up, ATTACK, RELEASE)

        smoothed += coefficients * (normalized - smoothed)

        #DEBUG
        t2 = time.perf_counter()

        heights = []
        for value in smoothed:
            height = int(value *MAX_HEIGHT)
            height = max(0,min(MAX_HEIGHT,height))
            heights.append(height)

        #move the cursor back to top
        #print("\033[H", end="")

        

        #mirrored output :3
        lines = []
        for row in range(MAX_HEIGHT, 0, -1):
            line = ""
            for height in heights:
                if height >= row:
                    line += "██ "
                else:
                    line += "   "
            for height in reversed(heights):
                if height >= row:
                    line += "██ "
                else:
                    line += "   "
            

            lines.append(line)
        fps_frames += 1
        now = time.perf_counter()
        
        if now - fps_timer >= 1.0:
            fps = fps_frames / (now - fps_timer)
            fps_frames = 0
            fps_timer = now
        #DEBUG
        lines.append(
            f"FPS {fps:5.1f} | "
            f"read {read_ms:5.1f} ms | "
            f"analysis {analysis_ms:5.1f} ms | "
            f"render {render_ms:5.1f} ms | "
            f"total {total_ms:5.1f} ms "
            f"max {maxr:5.1f} | "
            f"min {minr:5.1f} "
        )
        #if len(read_times) >= 300:
        #    times = np.array(read_times)
#
##            instant = np.sum(times < 1.0)
#
 #           print(
 #               f"min={times.min():.2f} | "
  #              f"avg={times.mean():.2f} | "
   #             f"p50={np.percentile(times, 50):.2f} | "
    #            f"p95={np.percentile(times, 95):.2f} | "
  #              f"max={times.max():.2f} | "
   #             f"<1ms={instant}/{len(times)}"
    #        )

     #       read_times.clear()
        lines.append("── " * NUM_BANDS * 2)

        frame = "\n".join(lines)

        sys.stdout.write("\033[H" + frame + "\033[J")
        sys.stdout.flush()

        #DEBUG 
        t3 = time.perf_counter()
        read_ms = (t1 - t0) * 1000
        maxr = max(maxr,read_ms)
        minr = (minr + read_ms) / 2
        analysis_ms = (t2 - t1) * 1000
        render_ms = (t3 - t2) * 1000
        total_ms = (t3 - loop_start) * 1000
        

finally:
    #calling cursor back
    print("\033[?25h", end="")
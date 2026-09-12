import numpy as np
import wave
import sounddevice as sd
import sys
import subprocess

#smoothing stuff simply put
#how much audio the fft looks at
FFT_SIZE = 2048
#how much new audio arrives each update (step size or such)
HOP_SIZE = 768

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
#audio = wave.open("shelter2.wav","rb")
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
        raw_data = stream.stdout.read(HOP_SIZE * CHANNELS * BYTES_PER_SAMPLE)

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

        heights = []
        for value in smoothed:
            height = int(value *MAX_HEIGHT)
            height = max(0,min(MAX_HEIGHT,height))
            heights.append(height)

        #move the cursor back to top
        print("\033[H", end="")

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
        lines.append("── " * NUM_BANDS * 2)

        frame = "\n".join(lines)

        sys.stdout.write("\033[H" + frame + "\033[J")
        sys.stdout.flush()



finally:
    #calling cursor back
    print("\033[?25h", end="")
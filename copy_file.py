#DELETE THIS LATER

import numpy as np
import sounddevice as sd
import sys
import subprocess
import threading

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
#how many samples does the audio thread grab at once?
READ_SIZE = 960
TARGET_FPS = 120
REFERENCE_FPS = 60

SAMPLE_RATE = 48000
#CHUNK_SIZE = 2048
NUM_BANDS = 20
MAX_HEIGHT = 50
CHANNELS = 2
BYTES_PER_SAMPLE= 2

DEVICE = "bluez_output.88_8E_68_E1_9E_A8.1.monitor"

#smoothing constants
smoothed = np.zeros(NUM_BANDS)
ATTACK = .5
RELEASE = 0.15
peak_level = 0.01
PEAK_ATTACK = 1
PEAK_RELEASE = 0.005

#so we add more unicodes here :3
PARTIAL_BLOCKS = " ▁▂▃▄▅▆▇█"

audio_buffer = np.zeros(FFT_SIZE, dtype=np.float32)
buffer_lock = threading.Lock()

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

def capture_audio():
    global audio_buffer

    while True:
        raw_data = stream.stdout.read(READ_SIZE * CHANNELS * BYTES_PER_SAMPLE)

        if not raw_data:
            break

        samples = np.frombuffer(raw_data, dtype="<i2").reshape(-1, CHANNELS)
        mono = np.mean(samples.astype(np.float32), axis = 1) / 32768.0

        with buffer_lock:
            audio_buffer[:-READ_SIZE] = audio_buffer[READ_SIZE:]
            audio_buffer[-READ_SIZE:] = mono

audio_thread = threading.Thread(target= capture_audio, daemon=True)

audio_thread.start()

#this here defines the regions for the frequencies
window = np.hanning(FFT_SIZE)
band_edges = np.geomspace(40,16000, NUM_BANDS +1)
#band_edges = np.geomspace(30,500, NUM_BANDS +1)
frequencies = np.fft.rfftfreq(FFT_SIZE, d=1/SAMPLE_RATE)

#hide terminal cursor
print("\033[?25l", end="")

#we are going to read the first complete window
raw_data = stream.stdout.read(FFT_SIZE * CHANNELS * BYTES_PER_SAMPLE)

samples = np.frombuffer(raw_data,dtype="<i2").reshape(-1,CHANNELS)
analysis_buffer = np.mean(samples.astype(np.float32),axis=1) / 32768.0

FRAME_TIME = 1.0 / TARGET_FPS
next_frame = time.perf_counter()
last_frame_time = 0
    
try:
    while True:
        with buffer_lock:
            analysis_buffer = audio_buffer.copy()

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

        now = time.perf_counter()
        dt = now - last_frame_time
        last_frame_time = now

        #this is to prevent time count after terminal cancel
        dt = min(dt,0.1)

        #we make attack and relase so that it adapts to passing time (aka the time betwen the frames)
        attack = 1 - (1 - ATTACK) ** (dt * REFERENCE_FPS)
        release = 1 - (1- RELEASE) ** (dt * REFERENCE_FPS)

        going_up = normalized > smoothed

        coefficients = np.where(going_up, attack, release)

        smoothed += coefficients * (normalized - smoothed)

        bar_height = smoothed[i] * MAX_HEIGHT

        whole = int(bar_height)
        #float
        fraction = bar_height - whole

        partial_index = round(fraction * 8)
        partial = PARTIAL_BLOCKS[partial_index] + PARTIAL_BLOCKS[partial_index]
        
        heights = []
        for value in smoothed:
            height = int(value *MAX_HEIGHT)
            height = max(0,min(MAX_HEIGHT,height))
            heights.append(height)
        render_heights = []

        for value in smoothed * MAX_HEIGHT:
            whole = int(value)
            fraction = value - whole

            partial_index = round(fraction * 8)

            if partial_index == 8:
                whole += 1
                partial_index = 0

            partial = PARTIAL_BLOCKS[partial_index]

            render_heights.append((whole,partial))

        #mirrored output :3
        lines = []
       
        for row in range(MAX_HEIGHT, 0, -1):
            line = ""

            #left side 
            for whole, partial in reversed(render_heights):
                if row <= whole:
                    line += "██ "
                elif row == whole + 1 and partial != " ":
                    line += partial * 2 + " "
                else:
                    line += "   "

            #right side
            for whole, partial in render_heights:
                if row <= whole:
                    line += "██ "
                elif row == whole + 1 and partial != " ":
                    line += partial * 2 + " "
                else:
                    line += "   "
            

            lines.append(line)
        fps_frames += 1
        now = time.perf_counter()
        
        if now - fps_timer >= 1.0:
            fps = fps_frames / (now - fps_timer)
            fps_frames = 0
            fps_timer = now

        lines.append("── " * NUM_BANDS * 2)

        frame = "\n".join(lines)

        sys.stdout.write("\033[H" + frame + "\033[J")
        sys.stdout.flush()

        next_frame += FRAME_TIME

        sleep_time = next_frame - time.perf_counter()

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            #just in case the terminal is late
            next_frame = time.perf_counter()
        

finally:
    #calling cursor back
    print("\033[?25h", end="")
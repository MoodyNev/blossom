import numpy as np
import wave
import sounddevice as sd
import sys

SAMPLE_RATE = 48000
CHUNK_SIZE = 2048
NUM_BANDS = 20
MAX_HEIGHT = 50

#smoothing constants
smoothed = np.zeros(NUM_BANDS)

ATTACK = 0.75
RELEASE = 0.15
peak_level = 0.01
PEAK_ATTACK = 0.8
PEAK_RELEASE = 0.005

#audio import
audio = wave.open("shelter2.wav","rb")
SAMPLE_RATE = audio.getframerate()
CHANNELS = audio.getnchannels()

stream = sd.OutputStream(samplerate=SAMPLE_RATE,
                         channels=CHANNELS,
                         dtype="int16",
                         blocksize=CHUNK_SIZE)

stream.start()

#this here defines the regions for the frequencies
#band_edges = np.linspace(30,500, NUM_BANDS +1)
band_edges = np.geomspace(40,16000, NUM_BANDS +1)
frequencies = np.fft.rfftfreq(CHUNK_SIZE, d=1/SAMPLE_RATE)

#hide terminal cursor
print("\033[?25l", end="")
try:
    while True:
        #read the next chunk
        raw_data = audio.readframes(CHUNK_SIZE)

        #if there are no more chunks left then the song ended
        if len(raw_data) == 0:
            break

        samples = np.frombuffer(raw_data,dtype="<i2")
        #here we have stereo
        samples = samples.reshape(-1, CHANNELS)
        stream.write(samples)

        analysis_samples = samples.astype(np.float32)

        #now we make it mono
        mono = np.mean(analysis_samples, axis=1)
        # we are turning the 16 bit into calculateable floats
        mono /= 32768.0

        #if the final chunk is smaller than 2048
        #we stop for now
        if len(mono) != CHUNK_SIZE:
            break

        #window
        window =np.hanning(CHUNK_SIZE)
        windowed = mono*window

        #fft
        spectrum = np.fft.rfft(windowed)
        magnitudes = (2* np.abs(spectrum)/np.sum(window))

        #convert fft bins into 16 bands
        band_magnitudes = []

        for i in range(NUM_BANDS):
            low = band_edges[i]
            high = band_edges[i + 1]

            mask = ((frequencies >= low) & (frequencies < high))
            band_magnitude = np.max(magnitudes[mask])

            band_magnitudes.append(band_magnitude)

        band_magnitudes = np.array(band_magnitudes)

        #kind of looks similar to geompace, but instead of potentials we evenly divide the spaces between values
        weights = np.linspace(0.5,2.0,NUM_BANDS)

        band_magnitudes *= weights 

        #temporarily normalize every frame
        #maximum = np.max(band_magnitudes)
        #if maximum > 0:
        #    normalized = (band_magnitudes /maximum)
        #else: 
        #    normalized = band_magnitudes

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
            

            ligit snes.append(line)
        lines.append("───" * NUM_BANDS * 2)

        frame = "\n".join(lines)

        sys.stdout.write("\033[H" + frame + "\033[J")
        sys.stdout.flush()



finally:
    audio.close()
    #calling cursor back
    print("\033[?25h", end="")
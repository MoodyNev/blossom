import numpy as np
#sample is the mesurement of the audio in an instant of time
#sample rate is how many per second?
#so the computer takes 48k mesurements per second

#and a buffer or chunk is a group of mesurements

#the raw data coming from pipewire doesnt tell us the frequencies that is why we are applying the fft to find out the frequencies
#the fft is capable of calculating all those waves and their magnitude

SAMPLE_RATE = 48000
DURATION = 1.0
FREQUENCY = 440
#constants are written in capital
#np.arange is more like a for loop with variables (or allows you to create arrays with listed numbers faster)
#np.sin is simply the sin function

#this generates time points
#so we list start, stop, reset
t = np.arange(
    0,
    DURATION,
    1 / SAMPLE_RATE
)

#this generates a 440Hz sin wave
#only taking a simple input: samples = np.sin(2 * np.pi * FREQUENCY * t)
#here we are adjusting the deal for 100 and 1000 hz
samples = (np.sin(2* np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 1000 * t))

# Reduce spectral leakage 
#i think this is more like a gauß average or sth (not the exact name but it smoothens out stuff)
#we are making the samples we created earlier smoother
window = np.hanning(len(samples))
windowed_samples = samples * window

#applies fourier transformation, it is something that turns the information to waves
# Convert time-domain samples -> frequency-domain values
spectrum = np.fft.rfft(windowed_samples)

# Get the frequency represented by each FFT bin
frequencies = np.fft.rfftfreq(len(samples), d=1 / SAMPLE_RATE)

# We care about magnitude, not complex FFT values
magnitudes = np.abs(spectrum)
# Find strongest frequency
#largest_bin formula: largest_bin = np.argmax(magnitudes)
#for target in [100, 440, 1000]:
#    index = np.argmin(np.abs(frequencies - target))
#    print(
#        f"{target:4} Hz -> magnitude {magnitudes[index]:.1f}"
#   )
# older detected frequency formula: detected_frequency = frequencies[largest_bin]

NUM_BANDS = 16

# so to say an exponential range between numbers
band_edges = np.geomspace(40, 16000, NUM_BANDS + 1)
band_magnitudes = []  

for i in range(NUM_BANDS):
    low = band_edges[i]
    high = band_edges[i + 1]

    mask = (frequencies >= low) & (frequencies < high)

    band_magnitude =np.max(magnitudes[mask])

    band_magnitudes.append(band_magnitude)

    print(f"{low:6.0f} - {high:6.0f} Hz : {band_magnitude:.1f}")

band_magnitudes = np.array(band_magnitudes)

max_magnitude = np.max(band_magnitudes)

normalized = band_magnitudes /max_magnitude

MAX_HEIGHT = 20

for value in normalized:
    height = int(value * MAX_HEIGHT)
    print("█" * height)


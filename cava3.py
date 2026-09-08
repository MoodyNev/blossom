import numpy as np
import time 

#here we are doing a vertical test code

#48k mesurements per second
SAMPLE_RATE = 48000
#just a set of 2048 group of boxes that take input in a time (this is in waveform)
CHUNK_SIZE = 2048

NUM_BANDS = 16
MAX_WIDTH = 30

#this here defines the regions for the frequencies
band_edges = np.geomspace(40,16000, NUM_BANDS +1)

frame = 0

while True:

    start_time = frame * CHUNK_SIZE / SAMPLE_RATE

    t = (start_time + np.arange(CHUNK_SIZE) /SAMPLE_RATE)

    bass_amplitude = (0.5 + 0.5 *np.sin(2 * np.pi *1.0 * start_time))

    samples = (bass_amplitude * np.sin(2 * np.pi * 100*t) + 0.4 * np.sin(2 * np.pi * 1000 * t))

    window = np.hanning(CHUNK_SIZE)

    windowed_samples = samples * window

    #this is where the input of waves turns into frequency inputs
    spectrum = np.fft.rfft(windowed_samples)
    frequencies = np.fft.rfftfreq(CHUNK_SIZE, d=1/SAMPLE_RATE) #this creates more like the "labels" of the waveform, frequencies as the name suggests

    #this tell us how strong each one is
    #you can think it more like the height of each box 
    magnitudes = (2 * np.abs(spectrum)/np.sum(window))

    band_magnitudes = []

    for i in range(NUM_BANDS):
        low = band_edges[i]
        high = band_edges[i+1]

        mask = (frequencies >= low) & (frequencies < high)

        band_magnitude = np.max(magnitudes[mask])

        band_magnitudes.append(band_magnitude)

    MAX_HEIGHT = 20 

    heights = []

    for value in band_magnitudes:
        height = int(value*MAX_HEIGHT)

        height = max(0,min(MAX_HEIGHT,height))

        heights.append(height)

    print("\033[2J\033[H", end="")

    for row in range(MAX_HEIGHT, 0 , -1):
        for height in heights:
            if height >= row:
                print("██ ", end="")
            else:
                print("   ", end="")
        print()

    print("───" * NUM_BANDS)


    frame += 1

    time.sleep(0.04)

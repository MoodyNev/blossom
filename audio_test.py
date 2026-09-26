import subprocess
import numpy as np
import time

CHUNK_SIZE = 2048
CHANNELS = 2 # simply means stero

DEVICE = "bluez_output.88_8E_68_E1_9E_A8.1.monitor"

stream = subprocess.Popen(
    [
        "parec",
        "--raw",
        f"--device={DEVICE}",
        "--format=s16le",
        "--rate=48000",
        "--channels=2",
    ],
    stdout=subprocess.PIPE
)

#this is the amount of bytes we read per second
bytes_to_read = CHUNK_SIZE * CHANNELS * 2

try:
    while True:
        

        start = time.perf_counter()

        raw_data = stream.stdout.read(bytes_to_read)

        end = time.perf_counter()

        print("read took:", end - start)
        samples = np.frombuffer(raw_data,dtype="<i2").reshape(-1,CHANNELS)
        samples = samples.astype(np.float32)

        mono = np.mean(samples, axis= 1) / 32768.0
        nonzero = np.flatnonzero(mono)

        #if len(nonzero) > 0:
            #print("first nonzero index:", nonzero[0])
            #print("first nonzero value:", mono[nonzero[0]])
        #print("peak:", np.max(np.abs(mono)))

finally:
    stream.terminate()
#this is the one where we put everything really in motion nicely synced with the music
import shutil 
import time
import math
import numpy as np
import sounddevice as sd
import sys
import subprocess
import threading

#this is mostly from the blossom stuff
UI_ROWS = 0
ASPECT_X = 1.25 #this because fonts work in a weird way

#this is for the audio import stuff
TARGET_FPS = 60
FFT_SIZE = 2048
READ_SIZE = 960
TARGET_FPS = 120
REFERENCE_FPS = 60
SAMPLE_RATE = 48000
CHANNELS = 2
BYTES_PER_SAMPLE= 2
#-------------------------------------------constants-----------------------------------------------

#audio porcessing 
DEVICE = "bluez_output.88_8E_68_E1_9E_A8.1.monitor"

audio_buffer = np.zeros(FFT_SIZE, dtype=np.float32)
buffer_lock = threading.Lock() 

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
window = np.hanning(FFT_SIZE)
frequencies = np.fft.rfftfreq(FFT_SIZE, d=1/SAMPLE_RATE)
#--------------------------------------audio import-------------------------------------------------------------

BRAILLE_BASE = 0x2800 #this is the empty char unicodeeeee

#we use a 8 bit system to represent this in programming
#so here are the cursed bit values of 
DOT_BITS = {
    (0,0): 0x01, #dot 1 
    (0,1): 0x02, #dot 2
    (0,2): 0x04, #dot 3
    (0,3): 0x40, #dot 7

    (1,0): 0x08, #dot 4
    (1,1): 0x10, #dot 5
    (1,2): 0x20, #dot 6
    (1,3): 0x80, #dot 8
}

#here comes more like the audio processing part
#since this is cooked we gonna make array representing cells (since individuals pixel darstellung would be cooked)
#this deals with the maths i dont want to calculate everytime
def create_canvas(cols,rows):
    return[
        [0 for _ in range(cols)]
        for _ in range(rows)
    ]

def set_pixel(canvas, x, y):
    rows = len(canvas)
    cols= len(canvas[0])

    cell_x = x // 2
    cell_y = y // 4

    if not (0 <= cell_x < cols and 0 <= cell_y < rows):
        return

    dot_x = x % 2
    dot_y = y % 4

    #this is the or operation in python
    #bit system, we can convert the orders by converting them
    canvas[cell_y][cell_x] |= DOT_BITS[(dot_x,dot_y)]

#makes the output
def render_canvas(canvas):
    lines = []

    for row in canvas:
        line = "".join(chr(BRAILLE_BASE + cell)for cell in row)
        lines.append(line)

    return "\n".join(lines)

#we will also make a 2d array representing terminal cells:
def get_terminal_canvas():
    terminal = shutil.get_terminal_size()

    cols = terminal.columns
    rows = max(1, terminal.lines - UI_ROWS)

    pixel_width = cols  * 2
    pixel_height = rows * 4

    center_x = pixel_width // 2
    center_y = pixel_height // 2

    max_radius = min(pixel_width, pixel_height) // 2
    return {
        "cols" : cols,
        "rows" : rows,      
        "width" : pixel_width, 
        "height" : pixel_height,    
        "center_x" : center_x,
        "center_y" : center_y, 
        "max_radius" : max_radius,
    }
#---------------------------------------setting up braille and canvas--------------------------------------

#draws a flower as the name suggests, it walks around a circle so to say and then changes the distance based on degree, which creates a flower like circle pattern
def draw_flower(canvas, center_x, center_y, base_radius, petal_size, petals):
    #so we collect sth hereee
    points =[]

    # we repeat that for each degree
    for degree in range(360):
        theta = math.radians(degree)

        radius = (base_radius + petal_size * math.sin(petals * theta))

        x = (center_x + radius * math.cos(theta) * ASPECT_X)

        y = (center_y - radius * math.sin(theta))

        points.append((x,y))

    #then we save the locations for each coordinate 
    #and send in the drawing functions
    #this simply connects the dots we calculated before and draws em
    for i in range(len(points)):
        x1,y1 = points[i]
        x2,y2 = points[(i+1) % len(points)]

        draw_line(canvas,x1,y1,x2,y2)

#waves we mostly use sin for it
def draw_waves(canvas, center_x, center_y, terminal_length, number_of_waves, height_of_waves,lol):
    points = []
    for times in range(2):
        for point in range(terminal_length):
            #point is interpreted in radians do we need theta for transformation
            #while defining theta we can also define the wave number
            theta = (point / terminal_length) * lol * math.pi * number_of_waves
            x = point + (terminal_length*times)
            y = center_y + math.sin(theta) * height_of_waves
            points.append((x,y))

    #drawing
    for i in range(len(points) -1):
        x1, y1 = points [i]
        x2, y2 = points[(i +1)]
        draw_line(canvas, x1,y1,x2,y2)


def draw_circle(canvas, center_x, center_y, radius):
    points = []

    for degree in range(360):
        theta = math.radians(degree)

        x = center_x + radius * math.cos(theta) * ASPECT_X
        y = center_y - radius * math.sin(theta)

        points.append((x,y))

    for i in range(len(points)):
        x1, x2 = points[i]
        y1, y2 = points[(i + 1) % len(points)]

        draw_line(canvas, x1,x2,y1,y2)

def draw_line(canvas, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1

    steps = math.ceil(max(abs(dx), abs(dy)))

    if steps == 0:
        set_pixel(canvas, round(x1), round(x2))
        return

    for i in range(steps + 1):
        t = i / steps

        x = x1 + dx * t
        y = y1 + dy * t

        set_pixel(canvas, round(x), round(y))
last_size = None

terminal = shutil.get_terminal_size()
canvas = create_canvas(terminal.columns,terminal.lines)
canvas_info = get_terminal_canvas()

canvas = create_canvas(canvas_info["cols"], canvas_info["rows"])

#draw_circle(canvas, canvas_info["center_x"], canvas_info["center_y"], canvas_info["max_radius"] * 0.5)
#draw_flower(canvas, canvas_info["center_x"], canvas_info["center_y"], base_radius=20, petal_size=50, petals=6)
#draw_waves(canvas, canvas_info["center_x"], canvas_info["center_y"], canvas_info["cols"], 4, 20)

print(render_canvas(canvas))

#HERE I WILL TRY TO PUT IN THE ACTUAL CODE IN A LOOP


raw_data = stream.stdout.read(FFT_SIZE * CHANNELS * BYTES_PER_SAMPLE)

samples = np.frombuffer(raw_data,dtype="<i2").reshape(-1,CHANNELS)
analysis_buffer = np.mean(samples.astype(np.float32),axis=1) / 32768.0

FRAME_TIME = 1.0 / TARGET_FPS
next_frame = time.perf_counter()
last_frame_time = 0

#lil debug
NUM_BANDS = 20
band_edges = np.geomspace(40,16000, NUM_BANDS +1)
try:
    while True:
        with buffer_lock:
            analysis_buffer = audio_buffer.copy()

        #fftt
        #more e updates e
        spectrum = np.fft.rfft(analysis_buffer * window)
        magnitudes = (2* np.abs(spectrum)/np.sum(window))

        low = band_edges[1]
        high = band_edges[1 + 1]
        mask = ((frequencies >= low) & (frequencies < high))
        band_values = magnitudes[mask]
        band_magnitude = np.sqrt(np.mean(band_values ** 2))
        #print(band_magnitude)
        canvas = create_canvas(canvas_info["cols"], canvas_info["rows"])
        draw_waves(canvas, canvas_info["center_x"], canvas_info["center_y"], canvas_info["cols"], 4, 20, band_magnitude)
        sys.stdout.write("\033[H" + render_canvas(canvas) + "\033[J")
        sys.stdout.flush()

        #normally we used to convert the input into bands, now we are gonna try convert em into waves
        #we used to divide the input into bands using geomspace, now we have a wider range where we can go wild
        #first of all we know that our limits are the terminal height and the frequency we want to process
        #instead of bands we can try to use terminal widthe

        

finally:
    #calling cursor back
    print("\033[?25h", end="")
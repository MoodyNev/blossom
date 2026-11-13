import shutil 
import time
import math
import numpy as np
import sounddevice as sd
import sys
import subprocess
import threading
from scipy.interpolate import CubicSpline
from scipy.interpolate import PchipInterpolator

#----------------------------------------USER SPECIFIC CONSTANTS----------------------------------------------
#adjust this variable depending on your font, otherwise waves and the flower will appear a little ugly 
#(best way to test is drawing a circle and change the values until you see a proper circle in the terminal)
ASPECT_X = 1.25  
#change your device name so the code can detect device output
DEVICE = "bluez_output.88_8E_68_E1_9E_A8.1.monitor"
#-------------------------------------------------------------------------------------------------------------

#MORE CONSTANTS
UI_ROWS = 0
TARGET_FPS = 60
FFT_SIZE = 2048
READ_SIZE = 960
REFERENCE_FPS = 60
SAMPLE_RATE = 48000
CHANNELS = 2
BYTES_PER_SAMPLE= 2

#AUDIO PROCESSING
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

#BRAILLE SETUP
BRAILLE_BASE = 0x2800 #this is the empty character unicode

#we use a 8 bit system to represent this in programming
#so here are the cursed bit values of braille if you are curious
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

#CREATE AND SETUP CANVAS
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

def render_canvas(canvas):
    lines = []

    for row in canvas:
        line = "".join(chr(BRAILLE_BASE + cell)for cell in row)
        lines.append(line)

    return "\n".join(lines)

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

#DRAWING FUNCTIONS
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
def draw_waves(canvas, center_x, center_y, terminal_length, number_of_waves, height_of_waves):
    points = []
    for times in range(2):
        for point in range(terminal_length):
            #point is interpreted in radians do we need theta for transformation
            #while defining theta we can also define the wave number
            theta = (point / terminal_length) * 2 * math.pi * number_of_waves
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
        set_pixel(canvas, round(x1), round(y1))
        return

    for i in range(steps + 1):
        t = i / steps

        x = x1 + dx * t
        y = y1 + dy * t

        set_pixel(canvas, round(x), round(y))

#a little preperation before the loop
last_size = None
terminal = shutil.get_terminal_size()
canvas = create_canvas(terminal.columns,terminal.lines)
canvas_info = get_terminal_canvas()
raw_data = stream.stdout.read(FFT_SIZE * CHANNELS * BYTES_PER_SAMPLE)
samples = np.frombuffer(raw_data,dtype="<i2").reshape(-1,CHANNELS)
analysis_buffer = np.mean(samples.astype(np.float32),axis=1) / 32768.0

#lil debug

#increasing num bands too much creates loops for some bands since the maths for the frequency spacing calculation is: SAMPLE_RATE / FFT_SIZE. 
#for our current constants the value is: 48000 / 2048 ~ 23 there fore any band number greater than 23 creates gaps
#increasing these values may cause lags, so i am gonna add some other maths while we are drawing the lines at the loop
NUM_BANDS = 20
FRAME_TIME = 1.0 / TARGET_FPS
next_frame = time.perf_counter()
last_frame_time = 0
smoothed = np.zeros(NUM_BANDS)
ATTACK = .5
RELEASE = 0.15
peak_level = 0.01
PEAK_ATTACK = 1
PEAK_RELEASE = 0.005
MAX_HEIGHT = 50
fps = 0.0
fps_frames = 0
fps_timer = time.perf_counter()

band_edges = np.geomspace(40,16000, NUM_BANDS +1)

#-----------FIND THE PART THAT EXACTLY TELLS THE HEIGHT OF THE BARS-------------------------------
# and then store them in an array, then use it for the coordinates
# perhaps you can try by just drawing points first and then turn them into waves

#ACTUAL MAIN PART
#TO-DO LIST:
#terminal changes are not detected (checking them every frame is expensive though)
#blossom is really cpu heavy atm, so we have to minimize and generalize the maths a little
#we could pack all frequencies in an array and make the computer respond to them differently
#because that was the initial plan i kinda forgot that along the wayy
try:
    while True:
        with buffer_lock:
            analysis_buffer = audio_buffer.copy()

        #fft
        #i wanted to remove abs here to get negative values but apparently that isnt possible, we are using abs to convert some complex numbers
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

        for i in range(len(smoothed)):
            bar_height = smoothed[i] * MAX_HEIGHT

        whole = int(bar_height)
        #float
        fraction = bar_height - whole
        
        heights = []
        for value in smoothed:
            height = int(value *MAX_HEIGHT)
            height = max(0,min(MAX_HEIGHT,height))
            heights.append(height)

        render_heights = []
        for value in smoothed * MAX_HEIGHT:
            whole = int(value)
            render_heights.append(whole)

        #task: give a proper shape to waveforms
        #since we are not increasing the sample rate, we are gonna use sin to create more wavelike forms


        debug_value = 1
        previous_x = 0
        previous_y = canvas_info["center_y"]
        s_value = (int) (canvas_info["cols"] / NUM_BANDS)
        lol = 1

        pointxy = ([[0, canvas_info["center_y"]]])

        for whole in render_heights:
            x_value = s_value * debug_value
            y_value = canvas_info["center_y"] - whole
            theta = (x_value / (canvas_info["cols"] * 2)) * 2 * math.pi * 15
            # dont forget to make everything in a way that everything meets at a single point
            # so we gotta play with the max length in a way so that when the whole is 0 the terminal length is also 0
            y_value = canvas_info["center_y"] - whole * canvas_info["rows"] * np.sin(theta) * 0.04

            # kinda want the flower to rotate and i dont want it to be perfecty symmetrical
            # make the curves smoother
            # the flower doent meet at the center atm
            # also test adding a little rotation to the flower 
            # also the petal number shouldnt be based on the loop count but different frequencies
            if(debug_value % 4 == 0):
                draw_flower(canvas, canvas_info["center_x"], canvas_info["center_y"], y_value / 4 * whole * 0.05, whole / lol , 4 * lol )
                lol += 1
                if lol % 4 == 0:
                    lol = 1
            
            #making curves smoother requires somepthing called curved interpolation
            pointxy.append([x_value,y_value])
            debug_value += 1
            previous_x = x_value
            previous_y = y_value

        debug_value = 1
        for whole in reversed(render_heights):
            x_value = s_value * debug_value + canvas_info["center_x"]
            y_value = canvas_info["center_y"] - whole *2
            theta = (x_value / (canvas_info["cols"]* 2)) * 2 * math.pi * 15
            y_value = canvas_info["center_y"] - whole * canvas_info["rows"] * np.sin(theta) * 0.04
            pointxy.append([x_value,y_value])
            debug_value += 1
            previous_x = x_value
            previous_y = y_value

        #here is the interpolation
        pointxy.append([canvas_info["cols"] * 2, canvas_info["center_y"]])
        xs,ys = zip(*pointxy)
        cs = CubicSpline(xs,ys)
        smooth_x = np.linspace(xs[0], xs[-1], 500)
        smooth_y = cs(smooth_x)

        previous_x = smooth_x[0]
        previous_y = smooth_y[0]
        for i in range(500):
            draw_line(canvas, previous_x, previous_y, smooth_x[i], smooth_y[i])
            previous_x = smooth_x[i]
            previous_y = smooth_y[i]

        draw_line(canvas, previous_x, previous_y, canvas_info["cols"] *2 , canvas_info["center_y"])
        
        fps_frames += 1
        now = time.perf_counter()
        
        if now - fps_timer >= 1.0:
            fps = fps_frames / (now - fps_timer)
            fps_frames = 0
            fps_timer = now

        sys.stdout.write("\033[H" + render_canvas(canvas) + "\033[J")
        sys.stdout.flush()
        canvas = create_canvas(canvas_info["cols"], canvas_info["rows"])

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
#we are adding the wave formed lines now
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
ASPECT_X = 1.25

#this is for the audio import stuff
TARGET_FPS = 60
FFT_SIZE = 2048
READ_SIZE = 960
TARGET_FPS = 120
REFERENCE_FPS = 60
SAMPLE_RATE = 48000
#NUM_BANDS = 20
#MAX_HEIGHT = 50 dotn forget to  implement this right for the wave and folower part
CHANNELS = 2
BYTES_PER_SAMPLE= 2

DEVICE = "bluez_output.88_8E_68_E1_9E_A8.1.monitor"

BRAILLE_BASE = 0x2800 #this is the empty char unicode

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

#draw waves, yeah.. this is drawing waves
#
#
def draw_waves(canvas, center_x, center_y, terminal_length, number_of_waves, height_of_waves):
    points = []
    for times in range(2):
        print(times)
        for point in range(terminal_length):
            #point is interpreted in radians do we need theta for transformation
            #while defining theta we can also define the wave number
            theta = (point / terminal_length) * 2 * math.pi * number_of_waves
            x = point + (terminal_length*times)
            print(x)
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
#draw_line(canvas, 0, 400,0,400)
#draw_line(canvas, 1, 401,1,401)
canvas_info = get_terminal_canvas()

canvas = create_canvas(canvas_info["cols"], canvas_info["rows"])

#draw_circle(canvas, canvas_info["center_x"], canvas_info["center_y"], canvas_info["max_radius"] * 0.5)
draw_flower(canvas, canvas_info["center_x"], canvas_info["center_y"], base_radius=20, petal_size=50, petals=6)
draw_waves(canvas, canvas_info["center_x"], canvas_info["center_y"], canvas_info["cols"], 4, 20)

print(render_canvas(canvas))


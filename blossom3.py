#understanding 
#we are using the braille system unicode, yk that lang used for blind people
#the weird order comes from the initial braille being numbered from 1 to 6 from top to bottom and new row
#later they added two more dots underneath to represent mfore chars, which lead to the numbering of bottom left as 7 and right as 8 e
import shutil 
import time
import math

TARGET_FPS = 60 
UI_ROWS = 0

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

#since this is cooked we gonna make array representing cells (since individuals pixel darstellung would be cooked)
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

def draw_circle(canvas, center_x, center_y, radius):
    points = []

    for degree in range(630):
        theta = math.radians(degree)

        x = center_x + radius * math.cos(theta)
        y = center_y - radius * math.sin(theta)

        points.append((x,y))

    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]

        draw_line(canvas, x1,y1,x2,y2)
def draw_line(canvas, x1, x2, y1, y2):
    dx = x2 - x1
    dy = y2 - y1

    steps = max(abs(dx), abs(dy))

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

draw_circle(canvas, canvas_info["center_x"], canvas_info["center_y"], canvas_info["max_radius"] * 0.5)
print(render_canvas(canvas))


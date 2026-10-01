#understanding 
#we are using the braille system unicode, yk that lang used for blind people
#the weird order comes from 
import shutil 
import time

TARGET_FPS = 60 
UI_ROWS = 0

BRAILLE_BASE = 0x2800 #this is the empty char unicode

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

last_size = None

terminal = shutil.get_terminal_size()

canvas = create_canvas(terminal.columns,terminal.lines)
set_pixel(canvas, 20, 20)

print(render_canvas(canvas))

for x in range(200):
    set_pixel(canvas, x ,40)
print(render_canvas(canvas))
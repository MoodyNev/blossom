#testing whether the code can detect canvas
#and it can :smile:
import shutil 
import time

TARGET_FPS = 60 
UI_ROWS = 0

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

while True:
    terminal_size = shutil.get_terminal_size()

    if terminal_size != last_size:
        last_size = terminal_size
        canvas = get_terminal_canvas()

        print(
            f"\r"
            f"terminal={canvas['cols']}x{canvas['rows']} | "
            f"pixels={canvas['width']}x{canvas['height']} | "
            f"center=({canvas['center_x']}, {canvas['center_y']}) | "
            f"radius={canvas['max_radius']}",
            end=""
        )

    time.sleep(1 / TARGET_FPS)
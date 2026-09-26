"""KidsCanvas: an interactive drawing app powered by CG algorithms."""

import colorsys
import os
from math import cos, pi, sin

# GLUT creates a GLX context on Linux; select the matching PyOpenGL backend.
os.environ["PYOPENGL_PLATFORM"] = "glx"

from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_LINES,
    GL_LINE_LOOP,
    GL_MODELVIEW,
    GL_POINTS,
    GL_PROJECTION,
    GL_QUADS,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SCISSOR_TEST,
    GL_SRC_ALPHA,
    glBegin,
    glBlendFunc,
    glClear,
    glClearColor,
    glColor3ub,
    glColor4ub,
    glDisable,
    glEnable,
    glEnd,
    glLineWidth,
    glLoadIdentity,
    glMatrixMode,
    glPointSize,
    glPopMatrix,
    glPushMatrix,
    glRasterPos2i,
    glScalef,
    glScissor,
    glTranslatef,
    glVertex2i,
    glViewport,
)
from OpenGL.GLU import gluOrtho2D
from OpenGL.GLUT import (
    GLUT_ACTIVE_CTRL,
    GLUT_BITMAP_8_BY_13,
    GLUT_DOWN,
    GLUT_DOUBLE,
    GLUT_LEFT_BUTTON,
    GLUT_MIDDLE_BUTTON,
    GLUT_RGBA,
    glutBitmapCharacter,
    glutCreateWindow,
    glutDisplayFunc,
    glutGetModifiers,
    glutInit,
    glutInitDisplayMode,
    glutInitWindowSize,
    glutKeyboardFunc,
    glutLeaveMainLoop,
    glutMainLoop,
    glutMotionFunc,
    glutMouseFunc,
    glutReshapeFunc,
    glutSetWindowTitle,
    glutSwapBuffers,
)

from algorithms.boundary_fill import boundary_fill
from algorithms.cohen_sutherland import cohen_sutherland_clip
from algorithms.flood_fill import flood_fill
from algorithms.transformations import screen_to_world
from tools.drawing_tools import (
    make_circle,
    make_line,
    make_polyline,
    make_rectangle,
    make_triangle,
)


WINDOW_WIDTH = 1320
WINDOW_HEIGHT = 800
SIDEBAR_WIDTH = 320
CANVAS_WIDTH = 1200
CANVAS_HEIGHT = WINDOW_HEIGHT
WHITE = (255, 255, 255)
BLACK = (25, 32, 48)

PRESET_HUES = (None, 0.0, 0.06, 0.13, 0.25, 0.36, 0.50, 0.58, 0.66, 0.82)


def make_preset_colors():
    """Create a compact matrix of neutral and shaded hue presets."""
    colors = []
    for row in range(8):
        saturation = 0.12 + row * 0.88 / 7
        value = 1.0 - row * 0.78 / 7
        for hue in PRESET_HUES:
            if hue is None:
                color = (round(value * 255),) * 3
            else:
                color = tuple(round(channel * 255) for channel in
                              colorsys.hsv_to_rgb(hue, saturation, value))
            colors.append(color)
    return colors


COLORS = make_preset_colors()
TOOL_BUTTONS = [
    ("LINE", "line"), ("CIRCLE", "circle"), ("RECT", "rectangle"),
    ("TRI", "triangle"), ("CURVE", "polyline"), ("FILL", "flood"),
    ("BOUND", "boundary"), ("CLIP", "clip"), ("PAN", "pan"),
    ("ERASE", "eraser"),
]

# Each object keeps its algorithm-generated pixels and its own color.
drawing_objects = []
undo_stack = []
redo_stack = []
pending_points = []
active_tool = "line"
selected_color = (25, 32, 48)
selected_alpha = 255
picker_hue, picker_saturation, picker_value = colorsys.rgb_to_hsv(
    *(channel / 255 for channel in selected_color)
)
active_rgb_channel = None
active_picker_drag = None
clip_window = None
zoom = 1.0
pan_x = SIDEBAR_WIDTH
pan_y = 0.0
window_width = WINDOW_WIDTH
window_height = WINDOW_HEIGHT
pan_anchor = None
status_message = "Choose a tool, then click on the canvas."


def draw_text(x, y, text, color=(38, 45, 62)):
    """Draw short bitmap text for toolbar labels and status."""
    glColor3ub(*color)
    glRasterPos2i(x, y)
    for character in text:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(character))


def draw_ui_rectangle(left, bottom, right, top, color):
    """Draw a filled screen-space toolbar rectangle."""
    glColor3ub(*color)
    glBegin(GL_QUADS)
    glVertex2i(left, bottom)
    glVertex2i(right, bottom)
    glVertex2i(right, top)
    glVertex2i(left, top)
    glEnd()


def render_objects():
    """Render every saved object's Bresenham/fill pixels."""
    glPointSize(2.0)
    for drawing_object in drawing_objects:
        glColor4ub(*drawing_object["color"], drawing_object.get("alpha", 255))
        glBegin(GL_POINTS)
        for x, y in drawing_object["pixels"]:
            glVertex2i(x, y)
        glEnd()


def sidebar_button_rectangles():
    """Return fixed screen-space rectangles for the sidebar tool buttons."""
    button_width = 137
    button_height = 28
    columns = 2
    left_edge = 12
    column_gap = 8
    first_top = window_height - 527
    row_gap = 32
    rectangles = []
    for index, (name, tool) in enumerate(TOOL_BUTTONS):
        row, column = divmod(index, columns)
        left = left_edge + column * (button_width + column_gap)
        top = first_top - row * row_gap
        rectangles.append((name, tool, left, top - button_height, left + button_width, top))
    return rectangles


def palette_swatch_rectangles():
    """Return an eight-row, ten-column grid of shaded preset colors."""
    width = 25
    height = 12
    step_x = 28
    first_left = 14
    first_top = window_height - 352
    row_gap = 15
    rectangles = []
    for index, color in enumerate(COLORS):
        row, column = divmod(index, 10)
        left = first_left + column * step_x
        top = first_top - row * row_gap
        rectangles.append((color, left, top - height, left + width, top))
    return rectangles


def draw_alpha_rectangle(left, bottom, right, top, color, alpha):
    """Draw a colored OpenGL rectangle with the selected transparency."""
    glColor4ub(*color, alpha)
    glBegin(GL_QUADS)
    glVertex2i(left, bottom)
    glVertex2i(right, bottom)
    glVertex2i(right, top)
    glVertex2i(left, top)
    glEnd()


def draw_color_picker():
    """Draw the saturation/value square, hue and alpha sliders, and RGB fields."""
    panel_left, panel_right = 8, SIDEBAR_WIDTH - 8
    panel_top = window_height - 53
    panel_bottom = window_height - 319
    draw_ui_rectangle(panel_left + 2, panel_bottom - 3, panel_right + 2, panel_top - 3,
                      (211, 219, 232))
    draw_ui_rectangle(panel_left, panel_bottom, panel_right, panel_top, (255, 255, 255))

    square_left = 14
    square_size = 180
    square_top = window_height - 92
    square_bottom = square_top - square_size
    divisions = 36
    cell_size = square_size / divisions
    glBegin(GL_QUADS)
    for row in range(divisions):
        value = row / (divisions - 1)
        bottom = round(square_bottom + row * cell_size)
        top = round(square_bottom + (row + 1) * cell_size)
        for column in range(divisions):
            saturation = column / (divisions - 1)
            left = round(square_left + column * cell_size)
            right = round(square_left + (column + 1) * cell_size)
            rgb = colorsys.hsv_to_rgb(picker_hue, saturation, value)
            glColor3ub(*(round(channel * 255) for channel in rgb))
            glVertex2i(left, bottom)
            glVertex2i(right, bottom)
            glVertex2i(right, top)
            glVertex2i(left, top)
    glEnd()

    marker_x = round(square_left + picker_saturation * square_size)
    marker_y = round(square_bottom + picker_value * square_size)
    for radius, color in ((6, (30, 36, 48)), (4, (255, 255, 255))):
        glColor3ub(*color)
        glBegin(GL_LINE_LOOP)
        for index in range(20):
            angle = 2 * pi * index / 20
            glVertex2i(round(marker_x + cos(angle) * radius),
                       round(marker_y + sin(angle) * radius))
        glEnd()

    hue_left, hue_width = 205, 14
    alpha_left, alpha_width = 230, 14
    slider_height = square_size
    slider_steps = 48
    for index in range(slider_steps):
        hue = index / (slider_steps - 1)
        bottom = square_bottom + round(index * slider_height / slider_steps)
        top = square_bottom + round((index + 1) * slider_height / slider_steps)
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        draw_ui_rectangle(hue_left, bottom, hue_left + hue_width, top,
                          tuple(round(channel * 255) for channel in rgb))

    checker_columns, checker_rows = 2, 24
    for row in range(checker_rows):
        bottom = square_bottom + round(row * slider_height / checker_rows)
        top = square_bottom + round((row + 1) * slider_height / checker_rows)
        for column in range(checker_columns):
            left = alpha_left + column * (alpha_width // checker_columns)
            right = alpha_left + (column + 1) * (alpha_width // checker_columns)
            checker = (222, 226, 234) if (row + column) % 2 else (255, 255, 255)
            draw_ui_rectangle(left, bottom, right, top, checker)
    for index in range(slider_steps):
        alpha = round(index * 255 / (slider_steps - 1))
        bottom = square_bottom + round(index * slider_height / slider_steps)
        top = square_bottom + round((index + 1) * slider_height / slider_steps)
        draw_alpha_rectangle(alpha_left, bottom, alpha_left + alpha_width, top,
                             selected_color, alpha)

    hue_marker = square_bottom + round(picker_hue * slider_height)
    alpha_marker = square_bottom + round(selected_alpha / 255 * slider_height)
    for x, y in ((hue_left, hue_marker), (alpha_left, alpha_marker)):
        glColor3ub(255, 255, 255)
        glBegin(GL_LINE_LOOP)
        glVertex2i(x - 1, y - 3)
        glVertex2i(x + 15, y - 3)
        glVertex2i(x + 15, y + 3)
        glVertex2i(x - 1, y + 3)
        glEnd()

    field_bottom = window_height - 300
    channel_labels = "RGB"
    for channel, label in enumerate(channel_labels):
        left = 14 + channel * 60
        right = left + 49
        border = (90, 151, 238) if active_rgb_channel == channel else (221, 226, 235)
        draw_ui_rectangle(left - 1, field_bottom - 1, right + 1, field_bottom + 21, border)
        draw_ui_rectangle(left, field_bottom, right, field_bottom + 20, (250, 251, 253))
        draw_text(left + 5, field_bottom + 6, str(selected_color[channel]))
        draw_text(left + 36, field_bottom + 7, "^", (91, 101, 123))
        draw_text(left + 36, field_bottom + 1, "v", (91, 101, 123))
        draw_text(left + 17, field_bottom - 13, label, (130, 137, 151))


def draw_sidebar():
    """Draw the color picker, shaded swatches, and drawing tools."""
    draw_ui_rectangle(0, 0, SIDEBAR_WIDTH, window_height, (241, 246, 255))
    draw_text(18, window_height - 27, "KIDSCANVAS", (35, 69, 125))
    draw_text(18, window_height - 46, "DRAW + COLOR + CREATE", (91, 101, 123))

    draw_text(18, window_height - 72, "COLOR PICKER", (91, 101, 123))
    draw_color_picker()
    draw_text(18, window_height - 328, "PREDEFINED COLORS", (91, 101, 123))
    for color, left, bottom, right, top in palette_swatch_rectangles():
        draw_ui_rectangle(left - 2, bottom - 2, right + 2, top + 2, (255, 255, 255))
        draw_ui_rectangle(left, bottom, right, top, color)
        if color == selected_color:
            glColor3ub(38, 45, 62)
            glBegin(GL_LINE_LOOP)
            glVertex2i(left - 3, bottom - 3)
            glVertex2i(right + 3, bottom - 3)
            glVertex2i(right + 3, top + 3)
            glVertex2i(left - 3, top + 3)
            glEnd()

    draw_text(18, window_height - 505, "DRAWING TOOLS", (91, 101, 123))
    for name, tool, left, bottom, right, top in sidebar_button_rectangles():
        button_color = (90, 151, 238) if tool == active_tool else (219, 228, 243)
        text_color = (255, 255, 255) if tool == active_tool else (38, 45, 62)
        draw_ui_rectangle(left, bottom, right, top, button_color)
        draw_text(left + 8, bottom + 9, name, text_color)

    draw_text(15, 132, status_message[:29], (68, 103, 166))
    draw_text(15, 111, "Wheel: zoom | Middle drag: pan", (84, 96, 118))
    draw_text(15, 91, "Ctrl-click: delete | C: clear", (84, 96, 118))
    draw_text(15, 71, "Ctrl+Z: undo | Ctrl+Y: redo", (84, 96, 118))


def display():
    """Draw the transformed canvas, clipping window, and fixed toolbar."""
    glClear(GL_COLOR_BUFFER_BIT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glEnable(GL_SCISSOR_TEST)
    glScissor(SIDEBAR_WIDTH, 0, max(1, window_width - SIDEBAR_WIDTH), window_height)
    glPushMatrix()
    glTranslatef(pan_x, pan_y, 0.0)
    glScalef(zoom, zoom, 1.0)
    render_objects()

    if clip_window is not None:
        xmin, ymin, xmax, ymax = clip_window
        glColor3ub(148, 70, 210)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2i(xmin, ymin)
        glVertex2i(xmax, ymin)
        glVertex2i(xmax, ymax)
        glVertex2i(xmin, ymax)
        glEnd()
        glLineWidth(1.0)

    if pending_points:
        preview_pixels = []
        if active_tool == "line" and len(pending_points) == 1:
            preview_pixels = pending_points
        elif active_tool == "circle" and len(pending_points) == 1:
            preview_pixels = pending_points
        elif active_tool in ("polyline", "triangle", "rectangle"):
            preview_pixels = make_polyline(pending_points)
        if preview_pixels:
            glColor4ub(*selected_color, selected_alpha)
            glPointSize(4.0)
            glBegin(GL_POINTS)
            for x, y in preview_pixels:
                glVertex2i(x, y)
            glEnd()

    glPopMatrix()
    glDisable(GL_SCISSOR_TEST)
    glLoadIdentity()
    draw_sidebar()
    glutSwapBuffers()


def reshape(width, height):
    """Update the screen projection while preserving a fixed logical canvas."""
    global window_width, window_height
    window_width = max(width, 1)
    window_height = max(height, 720)
    glViewport(0, 0, window_width, window_height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def add_object(kind, pixels, color=None):
    """Add an algorithm-generated drawing object and record it for undo."""
    if not pixels:
        return
    drawing_object = {
        "kind": kind,
        "pixels": pixels,
        "color": selected_color if color is None else color,
        "alpha": selected_alpha,
    }
    drawing_objects.append(drawing_object)
    undo_stack.append(("add", drawing_object))
    redo_stack.clear()


def remove_object(index):
    """Remove one object while saving enough information to undo it."""
    drawing_object = drawing_objects.pop(index)
    undo_stack.append(("remove", index, drawing_object))
    redo_stack.clear()


def find_object_at(x, y):
    """Find the nearest object pixel within a small screen-sized tolerance."""
    tolerance = max(2, round(8 / zoom))
    closest_distance = tolerance * tolerance
    closest_index = None
    for index in range(len(drawing_objects) - 1, -1, -1):
        for pixel_x, pixel_y in drawing_objects[index]["pixels"]:
            distance = (pixel_x - x) ** 2 + (pixel_y - y) ** 2
            if distance < closest_distance:
                closest_distance = distance
                closest_index = index
    return closest_index


def undo():
    """Reverse the most recent add, delete, or clear action."""
    global status_message
    if not undo_stack:
        status_message = "Nothing to undo yet."
        return
    action = undo_stack.pop()
    if action[0] == "add":
        drawing_object = action[1]
        for index, item in enumerate(drawing_objects):
            if item is drawing_object:
                drawing_objects.pop(index)
                break
    elif action[0] == "remove":
        drawing_objects.insert(action[1], action[2])
    else:
        drawing_objects[:] = action[1]
    redo_stack.append(action)
    status_message = "Undo complete. Press Ctrl+Y to redo."


def remove_last_curve_point(points):
    """Undo one click from a curve that has not yet been committed."""
    if not points:
        return False
    points.pop()
    return True


def redo():
    """Reapply the most recently undone action."""
    global status_message
    if not redo_stack:
        status_message = "Nothing to redo yet."
        return
    action = redo_stack.pop()
    if action[0] == "add":
        drawing_objects.append(action[1])
    elif action[0] == "remove":
        if action[1] < len(drawing_objects):
            drawing_objects.pop(action[1])
    else:
        drawing_objects[:] = []
    undo_stack.append(action)
    status_message = "Redo complete. Press Ctrl+Z to undo."


def canvas_raster():
    """Build the current colored pixel canvas used by both fill algorithms."""
    canvas = [[WHITE for _ in range(CANVAS_WIDTH)] for _ in range(CANVAS_HEIGHT)]
    for drawing_object in drawing_objects:
        color = drawing_object["color"]
        for x, y in drawing_object["pixels"]:
            if 0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT:
                canvas[y][x] = color
    return canvas


def fill_at(x, y, use_boundary_fill=False):
    """Fill a connected raster region and keep its pixels as an undoable object."""
    global status_message
    if not (0 <= x < CANVAS_WIDTH and 0 <= y < CANVAS_HEIGHT):
        return

    canvas = canvas_raster()
    before = [row.copy() for row in canvas]
    # কী করছে: ক্লিক করা অঞ্চলে Flood Fill বা Boundary Fill চালাচ্ছে।
    # কখন লাগছে: ব্যবহারকারী রঙের বালতি টুল দিয়ে আবদ্ধ জায়গায় ক্লিক করলে।
    # real world-এ এটা কোথায় দেখা যায়: পেইন্ট প্রোগ্রামের bucket tool-এ।
    if use_boundary_fill:
        changed = boundary_fill(canvas, x, y, selected_color, BLACK)
    else:
        changed = flood_fill(canvas, x, y, selected_color)

    if not changed:
        status_message = "Nothing to fill here. Boundary fill uses dark outlines."
        return

    pixels = [
        (pixel_x, pixel_y)
        for pixel_y, row in enumerate(canvas)
        for pixel_x, color in enumerate(row)
        if color != before[pixel_y][pixel_x]
    ]
    add_object("boundary_fill" if use_boundary_fill else "flood_fill", pixels)
    status_message = f"Filled {changed:,} pixels."


def complete_clip_window(first, second):
    """Store the rectangular region used to clip subsequently drawn lines."""
    global clip_window, status_message
    clip_window = (
        min(first[0], second[0]), min(first[1], second[1]),
        max(first[0], second[0]), max(first[1], second[1]),
    )
    status_message = "Clipping window set; new lines are clipped to it. Press X to remove it."


def finish_polyline():
    """Turn the current connected points into a saved drawing object."""
    global pending_points, status_message
    if len(pending_points) >= 2:
        add_object("polyline", make_polyline(pending_points))
        status_message = "Connected Bresenham segments added."
    else:
        status_message = "A curve-like polyline needs at least two points."
    pending_points = []


def finish_shape(point):
    """Use the active drawing tool to create one algorithm-backed object."""
    global pending_points, status_message, active_picker_drag
    pending_points.append(point)
    required_points = {"line": 2, "circle": 2, "rectangle": 2, "triangle": 3, "clip": 2}
    needed = required_points.get(active_tool)
    if needed is None or len(pending_points) < needed:
        status_message = f"Choose {needed - len(pending_points)} more point(s)."
        return

    first = pending_points[0]
    second = pending_points[1]
    if active_tool == "clip":
        complete_clip_window(first, second)
    elif active_tool == "line":
        if clip_window is None:
            pixels = make_line(first, second)
        else:
            # কী করছে: Cohen–Sutherland দিয়ে রেখার দৃশ্যমান অংশ সীমাবদ্ধ করছে।
            # কখন লাগছে: ক্লিপ উইন্ডো সক্রিয় রেখে নতুন রেখা আঁকলে।
            # real world-এ এটা কোথায় দেখা যায়: GPU-তে পর্দার বাইরে থাকা রেখা বাদ দিতে।
            clipped = cohen_sutherland_clip(*first, *second, *clip_window)
            pixels = [] if clipped is None else make_line(
                (round(clipped[0]), round(clipped[1])),
                (round(clipped[2]), round(clipped[3])),
            )
        add_object("line", pixels)
        status_message = "Line drawn with Bresenham." if pixels else "Line is outside the clipping window."
    elif active_tool == "circle":
        add_object("circle", make_circle(first, second))
        status_message = "Circle drawn with Bresenham's 8-way symmetry."
    elif active_tool == "rectangle":
        add_object("rectangle", make_rectangle(first, second))
        status_message = "Rectangle drawn from four Bresenham edges."
    elif active_tool == "triangle":
        add_object("triangle", make_triangle(pending_points))
        status_message = "Triangle drawn from three Bresenham edges."
    pending_points = []


def select_sidebar_item(screen_x, screen_y):
    """Handle picker, preset swatch, and tool-button interaction."""
    global active_tool, selected_color, selected_alpha, picker_hue
    global picker_saturation, picker_value, active_rgb_channel
    global pending_points, status_message
    if screen_x >= SIDEBAR_WIDTH:
        return False

    square_left, square_size = 14, 180
    square_top = window_height - 92
    square_bottom = square_top - square_size
    if square_left <= screen_x <= square_left + square_size and square_bottom <= screen_y <= square_top:
        active_picker_drag = "sv"
        picker_saturation = min(1.0, max(0.0, (screen_x - square_left) / square_size))
        picker_value = min(1.0, max(0.0, (screen_y - square_bottom) / square_size))
        selected_color = tuple(round(channel * 255) for channel in
                               colorsys.hsv_to_rgb(picker_hue, picker_saturation, picker_value))
        active_rgb_channel = None
        status_message = f"Color selected: RGB {selected_color}."
        display()
        return True

    if square_bottom <= screen_y <= square_top and 205 <= screen_x <= 219:
        active_picker_drag = "hue"
        picker_hue = min(1.0, max(0.0, (screen_y - square_bottom) / square_size))
        selected_color = tuple(round(channel * 255) for channel in
                               colorsys.hsv_to_rgb(picker_hue, picker_saturation, picker_value))
        status_message = f"Hue selected: RGB {selected_color}."
        display()
        return True

    if square_bottom <= screen_y <= square_top and 230 <= screen_x <= 244:
        active_picker_drag = "alpha"
        selected_alpha = round(min(1.0, max(0.0, (screen_y - square_bottom) / square_size)) * 255)
        status_message = f"Opacity: {round(selected_alpha * 100 / 255)}%."
        display()
        return True

    field_bottom = window_height - 300
    if field_bottom - 1 <= screen_y <= field_bottom + 21:
        for channel in range(3):
            left = 14 + channel * 60
            if left - 1 <= screen_x <= left + 50:
                active_rgb_channel = channel
                rgb = list(selected_color)
                if screen_x >= left + 34:
                    rgb[channel] = min(255, rgb[channel] + 1) if screen_y >= field_bottom + 10 else max(0, rgb[channel] - 1)
                    selected_color = tuple(rgb)
                    picker_hue, picker_saturation, picker_value = colorsys.rgb_to_hsv(
                        *(component / 255 for component in selected_color))
                status_message = f"RGB {selected_color}. Use the arrows to adjust the selected channel."
                display()
                return True

    for color, left, bottom, right, top in palette_swatch_rectangles():
        if left <= screen_x <= right and bottom <= screen_y <= top:
            selected_color = color
            selected_alpha = 255
            picker_hue, picker_saturation, picker_value = colorsys.rgb_to_hsv(
                *(component / 255 for component in color))
            active_rgb_channel = None
            status_message = f"Color selected: RGB {color}."
            display()
            return True

    for _name, tool, left, bottom, right, top in sidebar_button_rectangles():
        if left <= screen_x <= right and bottom <= screen_y <= top:
            if active_tool == "polyline" and pending_points and tool != "polyline":
                finish_polyline()
            active_tool = tool
            pending_points = []
            status_message = f"{tool.replace('_', ' ').title()} tool selected."
            display()
            return True
    # Clicks elsewhere in the sidebar should never paint on the canvas.
    return True


def zoom_at(screen_x, screen_y, factor):
    """Zoom around the mouse point so that point stays under the cursor."""
    global zoom, pan_x, pan_y
    old_zoom = zoom
    new_zoom = min(8.0, max(0.25, zoom * factor))
    if new_zoom == old_zoom:
        return
    world_x, world_y = screen_to_world(screen_x, screen_y, old_zoom, pan_x, pan_y)
    zoom = new_zoom
    pan_x = screen_x - world_x * zoom
    pan_y = screen_y - world_y * zoom


def mouse(button, state, mouse_x, mouse_y):
    """Handle palette clicks, drawing points, fill, delete, pan, and zoom."""
    global pending_points, pan_anchor, pan_x, pan_y, status_message, active_picker_drag
    screen_x = mouse_x
    screen_y = window_height - 1 - mouse_y

    if button in (3, 4) and state == GLUT_DOWN:
        if screen_x >= SIDEBAR_WIDTH:
            zoom_at(screen_x, screen_y, 1.2 if button == 3 else 1 / 1.2)
            display()
        return

    if button == GLUT_MIDDLE_BUTTON:
        pan_anchor = (screen_x, screen_y) if state == GLUT_DOWN and screen_x >= SIDEBAR_WIDTH else None
        return
    if button != GLUT_LEFT_BUTTON:
        return

    if state != GLUT_DOWN:
        pan_anchor = None
        active_picker_drag = None
        return
    if select_sidebar_item(screen_x, screen_y):
        return

    if active_tool == "pan":
        pan_anchor = (screen_x, screen_y)
        return

    world_x, world_y = screen_to_world(screen_x, screen_y, zoom, pan_x, pan_y)
    point = (round(world_x), round(world_y))
    if not (0 <= point[0] < CANVAS_WIDTH and 0 <= point[1] < CANVAS_HEIGHT):
        return

    if glutGetModifiers() & GLUT_ACTIVE_CTRL:
        # কী করছে: Ctrl-ক্লিকের কাছে থাকা একটি অবজেক্ট মুছে দিচ্ছে।
        # কখন লাগছে: আলাদা রেখা বা আকৃতি সরাতে Ctrl চেপে সেটিতে ক্লিক করলে।
        # real world-এ এটা কোথায় দেখা যায়: গ্রাফিক্স এডিটরে অবজেক্ট নির্বাচন করে মুছতে।
        index = find_object_at(*point)
        if index is not None:
            remove_object(index)
            status_message = "Selected object deleted. Ctrl+Z restores it."
        else:
            status_message = "No drawing close to that point."
        pending_points = []
        display()
        return

    if active_tool == "eraser":
        index = find_object_at(*point)
        if index is not None:
            remove_object(index)
            status_message = "Object erased. Ctrl+Z restores it."
        else:
            status_message = "Click close to a drawing to erase it."
    elif active_tool == "flood":
        fill_at(*point)
    elif active_tool == "boundary":
        fill_at(*point, use_boundary_fill=True)
    elif active_tool == "polyline":
        pending_points.append(point)
        status_message = f"Curve points: {len(pending_points)}. Press Enter to finish."
    elif active_tool != "pan":
        finish_shape(point)
    display()


def motion(mouse_x, mouse_y):
    """Drag a picker control or pan the canvas while the mouse is held."""
    global pan_anchor, pan_x, pan_y, picker_hue, picker_saturation
    global picker_value, selected_color, selected_alpha
    if pan_anchor is None:
        if active_picker_drag is None:
            return
    screen_x = mouse_x
    screen_y = window_height - 1 - mouse_y
    if active_picker_drag is not None and screen_x < SIDEBAR_WIDTH:
        square_left, square_size = 14, 180
        square_bottom = window_height - 92 - square_size
        position = min(1.0, max(0.0, (screen_y - square_bottom) / square_size))
        if active_picker_drag == "sv":
            picker_saturation = min(1.0, max(0.0, (screen_x - square_left) / square_size))
            picker_value = position
        elif active_picker_drag == "hue":
            picker_hue = position
        elif active_picker_drag == "alpha":
            selected_alpha = round(position * 255)
        selected_color = tuple(round(channel * 255) for channel in
                               colorsys.hsv_to_rgb(picker_hue, picker_saturation, picker_value))
        display()
        return
    if pan_anchor is None:
        return
    pan_x += screen_x - pan_anchor[0]
    pan_y += screen_y - pan_anchor[1]
    pan_anchor = (screen_x, screen_y)
    display()


def clear_canvas():
    """Clear all drawings and clipping state as one undoable action."""
    global clip_window, pending_points, status_message
    if drawing_objects or clip_window is not None:
        undo_stack.append(("clear", drawing_objects.copy()))
        redo_stack.clear()
    drawing_objects.clear()
    clip_window = None
    pending_points = []
    status_message = "Canvas cleared. Ctrl+Z restores the drawings."


def keyboard(key, _mouse_x, _mouse_y):
    """Handle clear, undo/redo, polyline finish, and clipping reset."""
    global pending_points, clip_window, status_message
    # Some GLUT/X11 setups provide Ctrl+Z/Y as control bytes; others provide
    # the letter plus a modifier flag. Bare Z/Y also work because the canvas
    # has no text-entry field.
    if key in (b"z", b"Z", b"\x1a"):
        if active_tool == "polyline" and remove_last_curve_point(pending_points):
            status_message = f"Last curve point undone. {len(pending_points)} point(s) remain."
        else:
            undo()
    elif key in (b"y", b"Y", b"\x19"):
        redo()
    elif key in (b"c", b"C"):
        clear_canvas()
    elif key in (b"\r", b"\n") and active_tool == "polyline":
        finish_polyline()
    elif key in (b"\x08", b"\x7f") and pending_points:
        pending_points.pop()
        status_message = "Removed the last unfinished point."
    elif key in (b"x", b"X"):
        clip_window = None
        status_message = "Clipping window removed."
    elif key == b"\x1b":
        glutLeaveMainLoop()
    display()


def main():
    """Open the KidsCanvas window and register its GLUT callbacks."""
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"KidsCanvas - CG Drawing and Coloring")
    glutSetWindowTitle(b"KidsCanvas | click tools and colors | C: clear | Ctrl+click: delete")
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutKeyboardFunc(keyboard)
    glutMainLoop()


if __name__ == "__main__":
    main()

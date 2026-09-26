"""Iterative 4-connected boundary fill algorithm.

The canvas is a 2D list: canvas[y][x].
Each pixel can be any hashable value, for example an RGB tuple such as (255, 0, 0).
"""


def boundary_fill(canvas, start_x, start_y, fill_color, boundary_color):
    """Fill pixels until boundary_color is reached.

    This implementation uses an explicit stack instead of recursion so that
    larger areas do not easily hit Python's recursion-depth limit.

    Returns the number of pixels changed.
    """
    # কী করছে: নির্দিষ্ট সীমানার রঙ না পাওয়া পর্যন্ত ভেতরের অঞ্চল ভরছে।
    # কখন লাগছে: BOUND টুল দিয়ে গাঢ় রেখায় ঘেরা কোনো অঞ্চল রঙ করলে।
    # real world-এ এটা কোথায় দেখা যায়: ড্রয়িং ও ইমেজ এডিটরের আবদ্ধ অঞ্চল ভরতে।
    height = len(canvas)
    if height == 0:
        return 0

    width = len(canvas[0])

    if not (0 <= start_x < width and 0 <= start_y < height):
        return 0

    if fill_color == boundary_color:
        return 0

    start_color = canvas[start_y][start_x]
    if start_color == boundary_color or start_color == fill_color:
        return 0

    stack = [(start_x, start_y)]
    changed = 0

    while stack:
        x, y = stack.pop()

        if not (0 <= x < width and 0 <= y < height):
            continue

        current = canvas[y][x]

        if current == boundary_color or current == fill_color:
            continue

        canvas[y][x] = fill_color
        changed += 1

        # 4-connected neighbours.
        stack.append((x + 1, y))
        stack.append((x - 1, y))
        stack.append((x, y + 1))
        stack.append((x, y - 1))

    return changed


if __name__ == "__main__":
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)

    canvas = [[WHITE for _ in range(10)] for _ in range(10)]

    # Simple black rectangular boundary.
    for x in range(2, 8):
        canvas[2][x] = BLACK
        canvas[7][x] = BLACK
    for y in range(2, 8):
        canvas[y][2] = BLACK
        canvas[y][7] = BLACK

    print("Pixels filled:", boundary_fill(canvas, 4, 4, RED, BLACK))

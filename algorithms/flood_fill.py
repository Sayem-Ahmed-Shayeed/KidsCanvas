"""Iterative 4-connected flood fill algorithm.

The canvas is a 2D list: canvas[y][x].
Each pixel can be an RGB tuple or another comparable value.
"""


def flood_fill(canvas, start_x, start_y, new_color):
    """Replace the connected region containing (start_x, start_y).

    The original color is read automatically from the starting pixel.
    Returns the number of pixels changed.
    """
    # কী করছে: শুরুর পিক্সেলের সঙ্গে যুক্ত একই রঙের অঞ্চল নতুন রঙে ভরছে।
    # কখন লাগছে: FILL টুল দিয়ে কোনো সংযুক্ত খালি অঞ্চল রঙ করতে ক্লিক করলে।
    # real world-এ এটা কোথায় দেখা যায়: পেইন্ট সফটওয়্যারের রঙের বালতি টুলে।
    height = len(canvas)
    if height == 0:
        return 0

    width = len(canvas[0])

    if not (0 <= start_x < width and 0 <= start_y < height):
        return 0

    old_color = canvas[start_y][start_x]

    if old_color == new_color:
        return 0

    stack = [(start_x, start_y)]
    changed = 0

    while stack:
        x, y = stack.pop()

        if not (0 <= x < width and 0 <= y < height):
            continue

        if canvas[y][x] != old_color:
            continue

        canvas[y][x] = new_color
        changed += 1

        # 4-connected neighbours.
        stack.append((x + 1, y))
        stack.append((x - 1, y))
        stack.append((x, y + 1))
        stack.append((x, y - 1))

    return changed


if __name__ == "__main__":
    WHITE = (255, 255, 255)
    BLUE = (0, 120, 255)

    canvas = [[WHITE for _ in range(8)] for _ in range(6)]
    print("Pixels filled:", flood_fill(canvas, 3, 2, BLUE))

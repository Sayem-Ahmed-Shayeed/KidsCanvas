"""Bresenham line drawing algorithm.

Returns the integer pixel coordinates that form a line between two points.
No OpenGL calls are used here so the algorithm can be tested independently.
"""


def bresenham_line(x0: int, y0: int, x1: int, y1: int):
    """Return a list of (x, y) pixels from (x0, y0) to (x1, y1)."""
    # কী করছে: Bresenham অ্যালগরিদম দিয়ে দুই বিন্দুর মাঝের পিক্সেল বেছে নিচ্ছে।
    # কখন লাগছে: রেখা, আকৃতি এবং কার্ভের অংশ আঁকার জন্য পিক্সেল দরকার হলে।
    # real world-এ এটা কোথায় দেখা যায়: পেইন্ট সফটওয়্যার ও কম্পিউটার গ্রাফিক্সে রেখা আঁকতে।
    points = []

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)

    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    err = dx - dy

    while True:
        points.append((x0, y0))

        if x0 == x1 and y0 == y1:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x0 += sx

        if e2 < dx:
            err += dx
            y0 += sy

    return points


if __name__ == "__main__":
    print(bresenham_line(2, 2, 10, 6))

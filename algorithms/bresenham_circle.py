"""Bresenham / midpoint-style integer circle drawing algorithm.

Returns the integer pixel coordinates of a circle using 8-way symmetry.
"""


def _symmetric_points(cx: int, cy: int, x: int, y: int):
    """Return the eight symmetric pixels for one circle point."""
    # কী করছে: বৃত্তের একটি বিন্দু থেকে আট দিকের সমমিত পিক্সেল বের করছে।
    # কখন লাগছে: Bresenham বৃত্ত অ্যালগরিদমের প্রতিটি ধাপে পিক্সেল বসাতে।
    # real world-এ এটা কোথায় দেখা যায়: কম ধাপে সমমিত বৃত্ত আঁকার গ্রাফিক্স অ্যালগরিদমে।
    return [
        (cx + x, cy + y),
        (cx - x, cy + y),
        (cx + x, cy - y),
        (cx - x, cy - y),
        (cx + y, cy + x),
        (cx - y, cy + x),
        (cx + y, cy - x),
        (cx - y, cy - x),
    ]


def bresenham_circle(cx: int, cy: int, radius: int):
    """Return a list of (x, y) pixels for a circle."""
    # কী করছে: Bresenham-এর বৃত্ত অ্যালগরিদম দিয়ে বৃত্তের পিক্সেল হিসাব করছে।
    # কখন লাগছে: কেন্দ্র ও ব্যাসার্ধ থেকে বৃত্ত আঁকার সময়।
    # real world-এ এটা কোথায় দেখা যায়: আইকন, চার্ট ও 2D গেমে বৃত্ত আঁকতে।
    if radius < 0:
        raise ValueError("radius must be non-negative")

    points = set()

    x = 0
    y = radius
    d = 3 - 2 * radius

    while x <= y:
        points.update(_symmetric_points(cx, cy, x, y))

        if d < 0:
            d = d + 4 * x + 6
        else:
            d = d + 4 * (x - y) + 10
            y -= 1

        x += 1

    return sorted(points)


if __name__ == "__main__":
    print(bresenham_circle(20, 20, 8))

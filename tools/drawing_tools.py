"""Build drawing-tool pixel lists from the standalone CG algorithms."""

from math import hypot

from algorithms.bresenham_circle import bresenham_circle
from algorithms.bresenham_line import bresenham_line


def make_line(start, end):
    """Return Bresenham pixels between two (x, y) points."""
    # কী করছে: Bresenham দিয়ে রেখার পিক্সেল তৈরি করছে।
    # কখন লাগছে: লাইন টুলে ব্যবহারকারী দুই প্রান্তে ক্লিক করলে।
    # real world-এ এটা কোথায় দেখা যায়: পেইন্ট অ্যাপ ও ভেক্টর গ্রাফিক্সে।
    return bresenham_line(start[0], start[1], end[0], end[1])


def make_circle(center, edge):
    """Return Bresenham circle pixels from center and edge points."""
    radius = round(hypot(edge[0] - center[0], edge[1] - center[1]))
    # কী করছে: কেন্দ্র ও ব্যাসার্ধ থেকে বৃত্তের পিক্সেল তৈরি করছে।
    # কখন লাগছে: বৃত্ত টুলে কেন্দ্র ও পরিধির একটি বিন্দু বাছলে।
    # real world-এ এটা কোথায় দেখা যায়: আইকন, চার্ট ও 2D গেমে।
    return bresenham_circle(center[0], center[1], radius)


def _join_edges(vertices, closed):
    """Connect vertices with Bresenham lines, keeping each pixel once."""
    # কী করছে: শীর্ষবিন্দুগুলো Bresenham রেখায় যুক্ত করে পুনরাবৃত্ত পিক্সেল বাদ দিচ্ছে।
    # কখন লাগছে: আয়তক্ষেত্র, ত্রিভুজ বা খোলা polyline-এর পিক্সেল তৈরি করতে।
    # real world-এ এটা কোথায় দেখা যায়: ভেক্টর আকৃতির সীমানা স্ক্রিনে rasterize করতে।
    pixels = []
    seen = set()
    edge_count = len(vertices) if closed else len(vertices) - 1

    for index in range(edge_count):
        start = vertices[index]
        end = vertices[(index + 1) % len(vertices)]
        for pixel in bresenham_line(start[0], start[1], end[0], end[1]):
            if pixel not in seen:
                pixels.append(pixel)
                seen.add(pixel)

    return pixels


def make_rectangle(first, second):
    """Return outline pixels for a rectangle given opposite corners."""
    # কী করছে: চারটি Bresenham রেখা জুড়ে আয়তক্ষেত্রের সীমানা তৈরি করছে।
    # কখন লাগছে: RECT টুলে বিপরীত দুই কোণে ক্লিক করলে।
    # real world-এ এটা কোথায় দেখা যায়: ড্রয়িং সফটওয়্যারে বক্স বা ফ্রেম আঁকতে।
    x1, y1 = first
    x2, y2 = second
    corners = [
        (min(x1, x2), min(y1, y2)),
        (max(x1, x2), min(y1, y2)),
        (max(x1, x2), max(y1, y2)),
        (min(x1, x2), max(y1, y2)),
    ]
    return _join_edges(corners, closed=True)


def make_triangle(vertices):
    """Return outline pixels for exactly three triangle vertices."""
    # কী করছে: তিনটি শীর্ষবিন্দু জুড়ে ত্রিভুজের রেখা তৈরি করছে।
    # কখন লাগছে: TRI টুলে তিনটি বিন্দু বাছাই সম্পন্ন হলে।
    # real world-এ এটা কোথায় দেখা যায়: ভেক্টর ড্রয়িং ও 2D গেমের আকৃতিতে।
    if len(vertices) != 3:
        raise ValueError("A triangle needs exactly three vertices")
    return _join_edges(vertices, closed=True)


def make_polyline(vertices):
    """Return pixels connecting each neighboring point without closing."""
    # কী করছে: পরপর বিন্দুগুলো Bresenham রেখা দিয়ে যুক্ত করছে।
    # কখন লাগছে: CURVE টুলে ক্লিক করা বিন্দুগুলোকে খোলা রেখা হিসেবে যুক্ত করতে।
    # real world-এ এটা কোথায় দেখা যায়: ড্রয়িং অ্যাপ ও মানচিত্রে পথ আঁকতে।
    if len(vertices) < 2:
        return []
    return _join_edges(vertices, closed=False)

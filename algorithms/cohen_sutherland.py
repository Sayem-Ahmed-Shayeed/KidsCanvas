"""Cohen-Sutherland line clipping algorithm."""

INSIDE = 0
LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8


def _region_code(x, y, xmin, ymin, xmax, ymax):
    # কী করছে: বিন্দুটি clipping window-এর কোন পাশে আছে তা bit code-এ রাখছে।
    # কখন লাগছে: রেখার দুই প্রান্ত ভেতরে, বাইরে, নাকি সীমা অতিক্রম করেছে তা যাচাই করতে।
    # real world-এ এটা কোথায় দেখা যায়: 2D গ্রাফিক্সে দৃশ্যমান অংশ নির্ধারণের clipping ধাপে।
    code = INSIDE

    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT

    if y < ymin:
        code |= BOTTOM
    elif y > ymax:
        code |= TOP

    return code


def cohen_sutherland_clip(x0, y0, x1, y1, xmin, ymin, xmax, ymax):
    """Clip a line to a rectangular window.

    Returns:
        (x0, y0, x1, y1) for the visible clipped segment,
        or None if the line is completely outside.
    """
    # কী করছে: রেখার দৃশ্যমান অংশটি আয়তাকার clipping window-এর মধ্যে রাখছে।
    # কখন লাগছে: CLIP টুল চালু রেখে নতুন রেখা আঁকলে।
    # real world-এ এটা কোথায় দেখা যায়: গ্রাফিক্স পাইপলাইনে পর্দার বাইরের রেখা বাদ দিতে।
    if xmin > xmax or ymin > ymax:
        raise ValueError("Invalid clipping rectangle")

    code0 = _region_code(x0, y0, xmin, ymin, xmax, ymax)
    code1 = _region_code(x1, y1, xmin, ymin, xmax, ymax)

    while True:
        # Both endpoints are inside.
        if code0 == 0 and code1 == 0:
            return x0, y0, x1, y1

        # Both endpoints share an outside region -> fully invisible.
        if code0 & code1:
            return None

        # Pick one endpoint that is outside.
        code_out = code0 if code0 != 0 else code1

        if code_out & TOP:
            if y1 == y0:
                return None
            x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0)
            y = ymax

        elif code_out & BOTTOM:
            if y1 == y0:
                return None
            x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0)
            y = ymin

        elif code_out & RIGHT:
            if x1 == x0:
                return None
            y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)
            x = xmax

        else:  # LEFT
            if x1 == x0:
                return None
            y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0)
            x = xmin

        if code_out == code0:
            x0, y0 = x, y
            code0 = _region_code(x0, y0, xmin, ymin, xmax, ymax)
        else:
            x1, y1 = x, y
            code1 = _region_code(x1, y1, xmin, ymin, xmax, ymax)


if __name__ == "__main__":
    result = cohen_sutherland_clip(
        -10, 20,
        120, 80,
        0, 0,
        100, 100,
    )
    print(result)

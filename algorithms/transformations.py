"""Convert between canvas coordinates and screen coordinates for zoom/pan."""


def screen_to_world(screen_x, screen_y, zoom, pan_x, pan_y):
    """Map a screen point back to the canvas coordinate system."""
    if zoom <= 0:
        raise ValueError("zoom must be greater than zero")
    # কী করছে: স্ক্রিনের অবস্থানকে ক্যানভাসের অবস্থানে রূপান্তর করছে।
    # কখন লাগছে: জুম বা প্যান করার পর মাউস ক্লিকের ক্যানভাস স্থান বের করতে।
    # real world-এ এটা কোথায় দেখা যায়: গ্রাফিক্স এডিটর ও ম্যাপ অ্যাপে।
    return (screen_x - pan_x) / zoom, (screen_y - pan_y) / zoom


def world_to_screen(world_x, world_y, zoom, pan_x, pan_y):
    """Map a canvas point to its visible screen position."""
    if zoom <= 0:
        raise ValueError("zoom must be greater than zero")
    # কী করছে: ক্যানভাসের অবস্থানকে জুম-প্যানসহ স্ক্রিনে বসাচ্ছে।
    # কখন লাগছে: ক্যানভাসের আঁকা জিনিস স্ক্রিনে দেখানোর সময়।
    # real world-এ এটা কোথায় দেখা যায়: 2D গেম, মানচিত্র ও ছবি সম্পাদকে।
    return world_x * zoom + pan_x, world_y * zoom + pan_y

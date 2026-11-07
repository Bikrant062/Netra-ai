LEFT_LIMIT = 1 / 3
RIGHT_LIMIT = 2 / 3
MIN_OVERLAP = 0.2  # a box counts as "in" a region if it covers 20% of the box's width there


def get_position(box, image_width):
    """Main position of a box, based on where its centre is."""
    x1, _, x2, _ = box
    centre = (x1 + x2) / 2 / image_width  # 0.0 = far left, 1.0 = far right
    if centre < LEFT_LIMIT:
        return "left"
    if centre < RIGHT_LIMIT:
        return "center"
    return "right"


def get_regions(box, image_width):
    """Every region (left/center/right) that the box meaningfully covers."""
    x1, _, x2, _ = box
    box_width = max(x2 - x1, 1)
    edges = {
        "left": (0, image_width * LEFT_LIMIT),
        "center": (image_width * LEFT_LIMIT, image_width * RIGHT_LIMIT),
        "right": (image_width * RIGHT_LIMIT, image_width),
    }
    regions = []
    for name, (start, end) in edges.items():
        overlap = max(0, min(x2, end) - max(x1, start))
        if overlap / box_width >= MIN_OVERLAP:
            regions.append(name)
    return regions


def add_positions(detections, image_width):
    """Add 'position' and 'regions' to every detection from detector.py."""
    for d in detections:
        d["position"] = get_position(d["box"], image_width)
        d["regions"] = get_regions(d["box"], image_width)
    return detections
SWAP = {"left": "right", "center": "center", "right": "left"}


def mirror_positions(detections):
    """For a camera that faces the user: swap left and right in every detection."""
    for d in detections:
        d["position"] = SWAP[d["position"]]
        d["regions"] = [SWAP[r] for r in d["regions"]]
    return detections
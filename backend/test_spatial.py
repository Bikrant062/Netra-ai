from spatial import get_position, get_regions

WIDTH = 1600  # the width of your test photo

# (name, box, expected position, expected regions)
cases = [
    ("clock (from your photo)", [7, 859, 289, 1125], "left", ["left"]),
    ("laptop (from your photo)", [152, 87, 1223, 1156], "center", ["left", "center"]),
    ("bottle (from your photo)", [1136, 24, 1590, 1128], "right", ["right"]),
    ("object across the whole view", [0, 0, 1600, 1200], "center", ["left", "center", "right"]),
]

all_ok = True
for name, box, want_pos, want_regions in cases:
    pos = get_position(box, WIDTH)
    regions = get_regions(box, WIDTH)
    ok = pos == want_pos and regions == want_regions
    all_ok = all_ok and ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}: position={pos}, regions={regions}")

print("\nAll tests passed." if all_ok else "\nSome tests FAILED.")
import sys
import time
from pathlib import Path

import cv2

from detector import Detector


def main():
    if len(sys.argv) < 2:
        print("Usage: python backend\\test_detector.py <image path>")
        return

    path = Path(sys.argv[1])
    image = cv2.imread(str(path))
    if image is None:
        print("Could not read the image:", path)
        return
    print(f"Image size: {image.shape[1]}x{image.shape[0]}")

    start = time.perf_counter()
    detector = Detector()
    print(f"Model loaded in {time.perf_counter() - start:.2f} s")

    detections = []
    for i in range(5):
        start = time.perf_counter()
        detections = detector.detect(image)
        print(f"Run {i + 1}: {(time.perf_counter() - start) * 1000:.0f} ms")

    print(f"\nFound {len(detections)} object(s):")
    for d in detections:
        print(f"  {d['name']}  {d['confidence']:.2f}  box={d['box']}")
        x1, y1, x2, y2 = d["box"]
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 255), 2)
        label = f"{d['name']} {d['confidence']:.2f}"
        cv2.putText(image, label, (x1, max(y1 - 6, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    out_path = path.with_name("result.jpg")
    cv2.imwrite(str(out_path), image)
    print("\nSaved the annotated image to:", out_path)


main()
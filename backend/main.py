import os
import time
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from assistant import answer_question
from detector import Detector
from spatial import add_positions, mirror_positions

app = FastAPI(title="Netra AI")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # skip any single image over 5 MB
MAX_FRAMES = 8                     # use at most this many frames per question
DEBUG_SAVE = os.environ.get("NETRA_DEBUG") == "1"  # off unless you turn it on

# Load the model once, when the server starts (not on every request).
detector = Detector()
# Warm-up: run once on a blank image so the first real question is fast.
detector.detect(np.zeros((480, 640, 3), dtype=np.uint8))


def sharpness_of(frame):
    """Higher = sharper. Only meaningful when comparing frames of the same scene."""
    return cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()


@app.get("/health")
def health():
    return {"status": "Netra AI backend is running"}


@app.post("/analyze")
def analyze(
    images: list[UploadFile] = File(...),
    question: str = Form(...),
    language: str = Form("en"),
    facing_me: bool = Form(False),
):
    # Decode every uploaded frame in memory. Nothing is written to disk.
    frames = []
    for upload in images[:MAX_FRAMES]:
        data = upload.file.read()
        if not data or len(data) > MAX_IMAGE_BYTES:
            continue
        decoded = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if decoded is not None:
            frames.append(decoded)
    if not frames:
        raise HTTPException(status_code=400, detail="No readable image was uploaded.")

    # Keep the sharpest of the recent frames.
    scores = [sharpness_of(f) for f in frames]
    best = max(range(len(frames)), key=lambda i: scores[i])
    frame = frames[best]

    if DEBUG_SAVE:
        debug_dir = Path(__file__).resolve().parent.parent / "debug"
        debug_dir.mkdir(exist_ok=True)
        cv2.imwrite(str(debug_dir / "last_frame.jpg"), frame)

    if language not in ("en", "ne"):
        language = "en"

    start = time.perf_counter()
    detections = detector.detect(frame)
    detect_ms = round((time.perf_counter() - start) * 1000)

    detections = add_positions(detections, frame.shape[1])
    if facing_me:
        detections = mirror_positions(detections)
    answer = answer_question(question, language, detections)

    names = [f"{d['name']}({d['position']}, {d['confidence']})" for d in detections]
    print(f"frames={[round(s) for s in scores]} used #{best + 1} | "
          f"{len(detections)} object(s) in {detect_ms} ms: {names}")

    return {
        "answer": answer,
        "language": language,
        "question": question,
        "objects": [
            {
                "name": d["name"],
                "confidence": d["confidence"],
                "position": d["position"],
                "regions": d["regions"],
            }
            for d in detections
        ],
    }


# This must stay LAST: it serves the frontend files at "/"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
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
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # reject uploads over 5 MB

# Load the model once, when the server starts (not on every request).
detector = Detector()


@app.get("/health")
def health():
    return {"status": "Netra AI backend is running"}


@app.post("/analyze")
def analyze(
    image: UploadFile = File(...),
    question: str = Form(...),
    language: str = Form("en"),
    facing_me: bool = Form(False),
):
    data = image.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="The image is too large.")

    # Decode the JPEG in memory. Nothing is written to disk.
    frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Could not read the image.")

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
    print(f"Detected {len(detections)} object(s) in {detect_ms} ms: {names}")

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
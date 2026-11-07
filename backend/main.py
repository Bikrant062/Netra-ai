from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Netra AI")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/health")
def health():
    return {"status": "Netra AI backend is running"}


@app.post("/analyze")
async def analyze(
    image: UploadFile = File(...),
    question: str = Form(...),
    language: str = Form("en"),
):
    image_bytes = await image.read()
    size_kb = round(len(image_bytes) / 1024, 1)
    print(f"Received {size_kb} KB image, language={language}, question={question!r}")

    # Placeholder answer. Real detection comes in Phase 4.
    if language == "ne":
        answer = f"मैले {size_kb} KB को तस्बिर पाएँ। वस्तु पहिचान चाँडै थपिनेछ।"
    else:
        answer = f"I received your {size_kb} KB image. Object detection is not added yet."

    return {
        "answer": answer,
        "language": language,
        "question": question,
        "objects": [],
    }


# This must stay LAST: it serves the frontend files at "/"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
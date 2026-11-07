from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Netra AI")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

@app.get("/health")
def health():
    return {"status": "Netra AI backend is running"}


# This must stay LAST: it serves the frontend files at "/"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
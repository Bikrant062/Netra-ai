from fastapi import FastAPI

app= FastAPI(title="Netra AI")

@app.get("/")
def home():
    return {"status": "Netra AI backend is running"}
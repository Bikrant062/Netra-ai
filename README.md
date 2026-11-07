# Netra AI 👁️

An AI-powered bilingual (English and Nepali) visual assistant for visually impaired people.

Users point their laptop camera at their surroundings, ask a question by voice or text, and hear a spoken answer describing the objects in view and where they are.

## Planned features

- Live camera-based visual question answering
- Object detection with a lightweight local ONNX model
- Left / center / right position awareness
- Voice input and spoken output in English and Nepali
- Text-input fallback when speech is unavailable
- No paid APIs and no extra hardware

## Tech stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python, FastAPI
- Computer vision: OpenCV, ONNX Runtime
- Voice: browser Web Speech API and SpeechSynthesis

## Status

In early development. The backend skeleton runs; features are being added step by step.

## Limitations

This is an informational assistant, not a navigation or collision-avoidance device. It cannot judge exact distances or confirm that a path is safe.

## Run locally

Requirements: Python 3.12 and, on Windows, the
[Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
(onnxruntime crashes on import without it).

```bash
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000
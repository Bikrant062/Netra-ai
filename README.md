# Netra AI 👁️

An AI-powered bilingual (English and Nepali) visual assistant for visually impaired people.

The user points the laptop camera at their surroundings and asks a question by voice or text, such as "What is on my left?". Netra AI analyzes the latest camera frame, finds the objects in it, works out where they are (left, front or right), and speaks the answer in English or Nepali.

Built for INNEX 2026 (Healthcare & Accessibility track). No paid APIs and no extra hardware.

## Features

- Live camera in the browser, with a recent-frame buffer: each question uses the sharpest of the last few frames
- Local object detection (YOLOX-Tiny, ONNX Runtime, CPU only) for the 80 everyday COCO classes
- Left / front / right position for each object, with objects that span regions noted
- Rule-based question understanding in English and Nepali ("What is on my left?", "मेरो अगाडि के छ?")
- Answers hedge when the detector is unsure ("something that looks like a bottle") and never claim an area is clear
- Spoken answers and voice input (browser speech services), with a typed-question fallback
- Keyboard shortcut: press **V** to ask by voice
- Option for a user-facing camera: swaps left and right in the answers and mirrors the preview

## How it works

1. The browser keeps the last few camera frames.
2. When a question is asked, the frames and the question are sent to the Python backend (FastAPI).
3. The backend picks the sharpest frame, runs the detector, and assigns each object a position.
4. A rule-based assistant builds the answer from the detections.
5. The browser speaks the answer.

## Requirements

- Windows, Python 3.12
- [Microsoft Visual C++ Redistributable (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe). ONNX Runtime crashes on import without it.
- Microsoft Edge with an internet connection (needed for speech, see Privacy)

## Setup

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Download the detection model (about 20 MB, not stored in this repository):

```powershell
Invoke-WebRequest -Uri "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_tiny.onnx" -OutFile "models\yolox_tiny.onnx"
```

Run:

```powershell
cd backend
uvicorn main:app --reload
```

Open http://127.0.0.1:8000, click **Start camera**, and ask a question.

## Using it

- Type a question and press **Ask**, or press **V** (or the voice button) and speak.
- Choose **English** or **नेपाली** before asking.
- If the laptop camera faces you, tick **The camera is facing me**. Without it, "left" and "right" are from the camera's point of view, which is correct when the camera points the way the user faces.

## Privacy

- Camera frames are processed in memory and are not saved to disk.
- Object detection runs locally on your computer.
- Voice input and spoken output use the browser's online speech services (Microsoft's in Edge), so they need an internet connection and the audio is processed by the browser vendor. Typed questions and on-screen answers work without them.

## Limitations

- **This is an informational assistant, not a navigation or safety device.** It cannot judge distance, and it must not be used to decide whether a path is safe.
- It only sees what is inside the camera's view, and it recognizes only 80 object types.
- A small model on a CPU makes mistakes. It can confuse similar objects (for example a bottle and a vase) and struggles with blur, dim light and backlight. Low-confidence guesses are reported as "looks like".
- "Left" and "right" are relative to the camera, so the camera must face the same way as the user for them to match the user's left and right.
- Tested only in Microsoft Edge on Windows. Nepali speech output needs a Nepali voice, and Edge provides one online. Other browsers are untested.

## Test results

(Add your scene test table here: scene, question, result.)

## Credits

- Object detection: [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) by Megvii (Apache License 2.0), YOLOX-Tiny weights exported to ONNX and trained on COCO.
- [ONNX Runtime](https://onnxruntime.ai/), [OpenCV](https://opencv.org/), [FastAPI](https://fastapi.tiangolo.com/), and the browser Web Speech API.
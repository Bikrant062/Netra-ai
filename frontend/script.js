const video = document.getElementById("camera");
const cameraBtn = document.getElementById("cameraBtn");
const statusEl = document.getElementById("status");
const answerEl = document.getElementById("answer");
const askForm = document.getElementById("askForm");
const askBtn = document.getElementById("askBtn");
const languageEl = document.getElementById("language");
const questionEl = document.getElementById("question");
const facingMeEl = document.getElementById("facingMe");

let stream = null;

function setStatus(message) {
  statusEl.textContent = message;
}

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false,
    });
    video.srcObject = stream;
    cameraBtn.textContent = "Stop camera";
    setStatus("Camera is on.");
  } catch (error) {
    stream = null;
    if (error.name === "NotAllowedError") {
      setStatus("Camera permission was denied. Please allow camera access in your browser.");
    } else if (error.name === "NotFoundError") {
      setStatus("No camera was found on this device.");
    } else if (error.name === "NotReadableError") {
      setStatus("The camera is being used by another application.");
    } else {
      setStatus("Could not start the camera: " + error.message);
    }
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
  stream = null;
  video.srcObject = null;
  cameraBtn.textContent = "Start camera";
  setStatus("Camera is off.");
}

cameraBtn.addEventListener("click", () => {
  if (stream) {
    stopCamera();
  } else {
    startCamera();
  }
});

// Grab the current video frame and return it as a JPEG file (Blob).
function captureFrame() {
  return new Promise((resolve, reject) => {
    if (!stream || video.videoWidth === 0) {
      reject(new Error("Camera is not ready."));
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("Could not capture the frame."))),
      "image/jpeg",
      0.8
    );
  });
}

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const question = questionEl.value.trim();
  if (!question) {
    setStatus("Please type a question first.");
    return;
  }
  if (!stream) {
    setStatus("Please start the camera first.");
    return;
  }

  askBtn.disabled = true;
  setStatus("Analyzing...");
  answerEl.textContent = "";

  try {
    const frame = await captureFrame();

    const formData = new FormData();
    formData.append("image", frame, "frame.jpg");
    formData.append("question", question);
    formData.append("language", languageEl.value);
    formData.append("facing_me", facingMeEl.checked ? "true" : "false");

    const response = await fetch("/analyze", { method: "POST", body: formData });
    if (!response.ok) {
      throw new Error("Server returned status " + response.status);
    }
    const data = await response.json();

    answerEl.textContent = data.answer;
    setStatus("Done.");
    console.log("Server response:", data);
  } catch (error) {
    setStatus("Something went wrong: " + error.message);
  } finally {
    askBtn.disabled = false;
  }
});
// Mirror the preview when the camera is facing the user.
function updateMirror() {
  video.classList.toggle("mirrored", facingMeEl.checked);
}
facingMeEl.addEventListener("change", updateMirror);
updateMirror();
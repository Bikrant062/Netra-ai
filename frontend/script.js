const video = document.getElementById("camera");
const cameraBtn = document.getElementById("cameraBtn");
const statusEl = document.getElementById("status");

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
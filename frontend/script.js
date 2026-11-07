const video = document.getElementById("camera");
const cameraBtn = document.getElementById("cameraBtn");
const statusEl = document.getElementById("status");
const answerEl = document.getElementById("answer");
const askForm = document.getElementById("askForm");
const askBtn = document.getElementById("askBtn");
const languageEl = document.getElementById("language");
const questionEl = document.getElementById("question");
const facingMeEl = document.getElementById("facingMe");
const repeatBtn = document.getElementById("repeatBtn");

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
    startFrameBuffer();
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
  stopFrameBuffer();
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
        // Send the most recent frames; the server keeps the sharpest one.
    let frames = recentFrames.slice();
    if (frames.length === 0) frames = [await captureFrame()];

    const formData = new FormData();
    frames.forEach((f, i) => formData.append("images", f, "frame" + i + ".jpg"));
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
    lastAnswer = data.answer;
    lastLanguage = data.language;
    repeatBtn.disabled = false;
    speak(lastAnswer, lastLanguage);

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
// ---------- Spoken answers ----------
let voices = [];
let lastAnswer = "";
let lastLanguage = "en";

function loadVoices() {
  voices = "speechSynthesis" in window ? speechSynthesis.getVoices() : [];
}
if ("speechSynthesis" in window) {
  loadVoices();
  speechSynthesis.addEventListener("voiceschanged", loadVoices);
}

function pickVoice(language) {
  const prefix = language === "ne" ? "ne" : "en";
  const matches = voices.filter((v) => v.lang.toLowerCase().startsWith(prefix));
  // Prefer the higher-quality "Natural"/"Online" voices when there are any.
  return matches.find((v) => /natural|online/i.test(v.name)) || matches[0] || null;
}

function speak(text, language) {
  if (!("speechSynthesis" in window)) {
    setStatus("Speech output is not supported in this browser. Please read the answer on screen.");
    return;
  }
  speechSynthesis.cancel(); // stop anything still being spoken
  const voice = pickVoice(language);
  if (language === "ne" && !voice) {
    setStatus("No Nepali voice was found on this device, so the answer is shown as text only.");
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = voice ? voice.lang : "en-US";
  if (voice) utterance.voice = voice;
  utterance.rate = 0.95;
  speechSynthesis.speak(utterance);
}

repeatBtn.addEventListener("click", () => {
  if (lastAnswer) speak(lastAnswer, lastLanguage);
});
// ---------- Recent-frame buffer ----------
const FRAME_BUFFER_SIZE = 5;   // keep the last 5 frames...
const FRAME_INTERVAL_MS = 100; // ...captured every 0.1 s (about the last half second)
let recentFrames = [];
let bufferTimer = null;
const bufferCanvas = document.createElement("canvas");

function startFrameBuffer() {
  stopFrameBuffer();
  bufferTimer = setInterval(() => {
    if (!stream || video.videoWidth === 0) return;
    bufferCanvas.width = video.videoWidth;
    bufferCanvas.height = video.videoHeight;
    bufferCanvas.getContext("2d").drawImage(video, 0, 0);
    bufferCanvas.toBlob(
      (blob) => {
        if (!blob) return;
        recentFrames.push(blob);
        if (recentFrames.length > FRAME_BUFFER_SIZE) recentFrames.shift();
      },
      "image/jpeg",
      0.8
    );
  }, FRAME_INTERVAL_MS);
}

function stopFrameBuffer() {
  if (bufferTimer) clearInterval(bufferTimer);
  bufferTimer = null;
  recentFrames = [];
}
// ---------- Voice input ----------
const voiceBtn = document.getElementById("voiceBtn");
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const RECOGNITION_LANG = { en: "en-IN", ne: "ne-NP" }; // en-US is the alternative for English
let recognition = null;
let listening = false;

function voiceErrorMessage(code) {
  switch (code) {
    case "not-allowed":
    case "service-not-allowed":
      return "Microphone permission was denied. Please allow the microphone, or type your question.";
    case "no-speech":
      return "I did not hear anything. Please try again, or type your question.";
    case "audio-capture":
      return "No microphone was found. Please type your question instead.";
    case "network":
      return "Voice recognition needs an internet connection and could not reach its service. Please type your question instead.";
    case "language-not-supported":
      return "Voice recognition is not available for this language in this browser. Please type your question instead.";
    default:
      return "Voice input failed (" + code + "). Please type your question instead.";
  }
}

function startListening() {
  if (!SpeechRecognition) {
    setStatus("Voice input is not supported in this browser. Please type your question.");
    return;
  }
  if (listening) {
    recognition.abort(); // second press cancels
    return;
  }
  // Stop any spoken answer first, so the microphone does not hear it.
  if ("speechSynthesis" in window) speechSynthesis.cancel();

  recognition = new SpeechRecognition();
  recognition.lang = RECOGNITION_LANG[languageEl.value] || "en-IN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    listening = true;
    voiceBtn.textContent = "Listening... (press V to cancel)";
    setStatus("Listening. Ask your question now.");
  };
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript.trim();
    if (transcript) {
      questionEl.value = transcript;
      askForm.requestSubmit(); // ask straight away, no extra click needed
    }
  };
  recognition.onerror = (event) => {
    if (event.error === "aborted") return; // the user cancelled on purpose
    setStatus(voiceErrorMessage(event.error));
  };
  recognition.onend = () => {
    listening = false;
    voiceBtn.textContent = "Ask by voice (press V)";
  };

  recognition.start();
}

if (!SpeechRecognition) {
  voiceBtn.disabled = true;
  voiceBtn.textContent = "Voice input is not supported in this browser";
}

voiceBtn.addEventListener("click", startListening);

// Keyboard shortcut: press V anywhere (except while typing) to ask by voice.
document.addEventListener("keydown", (event) => {
  const tag = event.target.tagName;
  if (
    event.key.toLowerCase() === "v" &&
    !event.ctrlKey && !event.altKey && !event.metaKey &&
    tag !== "INPUT" && tag !== "SELECT" && tag !== "TEXTAREA"
  ) {
    event.preventDefault();
    startListening();
  }
});
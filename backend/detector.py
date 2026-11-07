from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "yolox_tiny.onnx"
INPUT_SIZE = 416
CONF_THRESHOLD = 0.4   # ignore guesses below 40% confidence
NMS_THRESHOLD = 0.45   # remove boxes overlapping more than this

COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush",
]


def _nms(boxes, scores, iou_threshold):
    """Keep the best box for each object and drop heavily overlapping duplicates."""
    x1, y1, x2, y2 = boxes.T
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        rest = order[1:]
        xx1 = np.maximum(x1[i], x1[rest])
        yy1 = np.maximum(y1[i], y1[rest])
        xx2 = np.minimum(x2[i], x2[rest])
        yy2 = np.minimum(y2[i], y2[rest])
        inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        iou = inter / (areas[i] + areas[rest] - inter + 1e-9)
        order = rest[iou <= iou_threshold]
    return keep


class Detector:
    def __init__(self, model_path=MODEL_PATH):
        self.session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        self._grids, self._strides = self._build_grids()

    @staticmethod
    def _build_grids():
        """Position and step size of each of the 3549 candidate boxes."""
        grids, strides = [], []
        for stride in (8, 16, 32):
            size = INPUT_SIZE // stride
            xv, yv = np.meshgrid(np.arange(size), np.arange(size))
            grid = np.stack((xv, yv), axis=2).reshape(-1, 2)
            grids.append(grid)
            strides.append(np.full((grid.shape[0], 1), stride))
        return (
            np.concatenate(grids, 0).astype(np.float32),
            np.concatenate(strides, 0).astype(np.float32),
        )

    @staticmethod
    def _preprocess(image):
        """Shrink to fit 416x416 (keeping proportions), pad the rest with gray."""
        h, w = image.shape[:2]
        ratio = min(INPUT_SIZE / h, INPUT_SIZE / w)
        new_w, new_h = int(w * ratio), int(h * ratio)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((INPUT_SIZE, INPUT_SIZE, 3), 114, dtype=np.uint8)
        canvas[:new_h, :new_w] = resized
        blob = canvas.transpose(2, 0, 1).astype(np.float32)[None]
        return np.ascontiguousarray(blob), ratio

    def detect(self, image):
        """image: a BGR OpenCV image. Returns a list of detected objects."""
        h, w = image.shape[:2]
        blob, ratio = self._preprocess(image)
        pred = self.session.run(None, {self.input_name: blob})[0][0].copy()

        # Convert the model's raw numbers into pixel positions.
        pred[:, :2] = (pred[:, :2] + self._grids) * self._strides
        pred[:, 2:4] = np.exp(pred[:, 2:4]) * self._strides

        # Confidence = "is there an object" x "how sure about the class".
        scores = pred[:, 4:5] * pred[:, 5:]
        class_ids = scores.argmax(axis=1)
        confidences = scores[np.arange(len(scores)), class_ids]

        keep = confidences >= CONF_THRESHOLD
        if not keep.any():
            return []
        class_scores = scores[keep]
        pred, class_ids, confidences = pred[keep], class_ids[keep], confidences[keep]

        # Centre/width/height -> corners, mapped back to the original image size.
        cx, cy, bw, bh = pred[:, 0], pred[:, 1], pred[:, 2], pred[:, 3]
        boxes = np.stack(
            [cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], axis=1
        ) / ratio
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, w)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, h)

        # Remove duplicate boxes, separately for each object type.
        detections = []
        for class_id in np.unique(class_ids):
            idx = np.where(class_ids == class_id)[0]
            for k in _nms(boxes[idx], confidences[idx], NMS_THRESHOLD):
                j = idx[k]
                top = class_scores[j].argsort()[::-1][:3]
                detections.append(
                    {
                        "name": COCO_CLASSES[int(class_id)],
                        "confidence": round(float(confidences[j]), 2),
                        "box": [int(v) for v in boxes[j]],
                        "alternatives": [
                            (COCO_CLASSES[int(t)], round(float(class_scores[j][t]), 2))
                            for t in top
                        ],
                    }
                )
        # Second pass: if two boxes of different types cover almost the same
        # area, keep only the more confident one (e.g. "bottle" vs "vase").
        if detections:
            all_boxes = np.array([d["box"] for d in detections], dtype=np.float32)
            all_scores = np.array([d["confidence"] for d in detections], dtype=np.float32)
            kept = _nms(all_boxes, all_scores, 0.7)
            detections = [detections[i] for i in kept]

        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections
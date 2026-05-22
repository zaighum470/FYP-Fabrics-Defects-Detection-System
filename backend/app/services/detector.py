import os
import cv2
import numpy as np
from ultralytics import YOLO
from ..config import MEDIUM_MODEL, NANO_MODEL, CLASS_NAMES, CLASS_COLORS, CONF_THRESHOLD


class Detector:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self.load_model("medium")

    def load_model(self, model_name="medium"):
        """Load YOLO model"""
        model_path = MEDIUM_MODEL if model_name == "medium" else NANO_MODEL
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        self._model = YOLO(model_path)
        self._model_name = model_name

    def detect_from_array(self, img, conf_threshold=None):
        """Run detection on numpy array image"""
        if conf_threshold is None:
            conf_threshold = CONF_THRESHOLD
        results = self._model(img, conf=conf_threshold)
        detections = []

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls = int(box.cls[0])

                if cls >= len(CLASS_NAMES):
                    continue

                current_class = CLASS_NAMES[cls]
                color = CLASS_COLORS[current_class]

                label = f"{current_class} {conf:.2f}"

                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (255, 255, 255), 2)

                detections.append({
                    "class": current_class,
                    "confidence": round(conf, 2),
                    "bbox": [x1, y1, x2, y2]
                })

        return img, detections

    @property
    def class_names(self):
        return CLASS_NAMES

#!/usr/bin/env python3

import cv2
import numpy as np
import yaml
import time
import logging
from pathlib import Path
from typing import List, Tuple, Optional

try:
    from ultralytics import YOLO as UltralyticsYOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False


class Detection:
    """Reprezentarea unei detecții YOLO."""

    def __init__(self, class_id: int, class_name: str, confidence: float,
                 bbox: Tuple[int, int, int, int]):
        self.class_id = class_id
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox
        self.center = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
        self.area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "class": self.class_name,
            "confidence": float(self.confidence),
            "bbox": list(self.bbox),
        }


class YOLOInference:
    """Inferență YOLOv8n cu Ultralytics pe CPU."""

    def __init__(self, config_path: str = "config/robot_config.yaml"):
        self.config = self._load_config(config_path)
        self.yolo_config = self.config.get("yolo", {})

        logging.basicConfig(level=getattr(logging, self.config.get("logging", {}).get("level", "INFO")))
        self.logger = logging.getLogger("YOLOInference")

        self.confidence_threshold = self.yolo_config.get("confidence_threshold", 0.45)
        self.nms_threshold = self.yolo_config.get("nms_threshold", 0.50)
        self.model = None
        self.model_path = None
        self.inference_times: List[float] = []
        self.frame_count = 0

    def _load_config(self, config_path: str) -> dict:
        path = Path(config_path)
        if not path.is_absolute():
            root = Path(__file__).parent.parent.parent
            path = root / config_path
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _find_model(self) -> Optional[str]:
        candidates = self.yolo_config.get("model_paths", [
            "datasets/models/yolov8n.pt",
            "models/yolov8n.pt",
        ])
        root = Path(__file__).parent.parent.parent
        for rel in candidates:
            full = root / rel
            if full.exists():
                return str(full)
        return None

    def initialize(self) -> bool:
        if not ULTRALYTICS_AVAILABLE:
            self.logger.error("Ultralytics lipsește. Instalează: pip install ultralytics")
            return False

        self.model_path = self._find_model()
        if not self.model_path:
            self.logger.error(
                "Model YOLOv8n negăsit. Rulează: bash scripts/download_yolo_model.sh"
            )
            return False

        try:
            self.logger.info(f"Încărcare model: {Path(self.model_path).name}")
            self.model = UltralyticsYOLO(self.model_path)
            self.logger.info(f"Model încărcat — {len(self.model.names)} clase COCO")
            return True
        except Exception as e:
            self.logger.error(f"Eroare încărcare model: {e}")
            return False

    def infer(self, image: np.ndarray) -> Tuple[List[Detection], float]:
        """
        Rulează inferența YOLO pe imagine (BGR, preprocesată sau raw).

        Returns:
            (listă detecții, timp_inferență_ms)
        """
        if self.model is None:
            return [], 0.0

        start = time.perf_counter()
        try:
            results = self.model.predict(
                image,
                conf=self.confidence_threshold,
                iou=self.nms_threshold,
                verbose=False,
            )[0]

            detections = []
            for box in results.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                detections.append(Detection(
                    class_id=cls_id,
                    class_name=self.model.names[cls_id],
                    confidence=conf,
                    bbox=(int(x1), int(y1), int(x2), int(y2)),
                ))

            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self.inference_times.append(elapsed_ms)
            if len(self.inference_times) > 100:
                self.inference_times.pop(0)
            self.frame_count += 1
            return detections, elapsed_ms

        except Exception as e:
            self.logger.error(f"Eroare inferență: {e}")
            return [], 0.0

    def get_average_inference_time(self) -> float:
        if not self.inference_times:
            return 0.0
        return sum(self.inference_times) / len(self.inference_times)

    def visualize_detections(self, image: np.ndarray, detections: List[Detection]) -> np.ndarray:
        result = image.copy()
        for det in detections:
            color = (0, 255, 0)
            cv2.rectangle(result, (det.bbox[0], det.bbox[1]),
                          (det.bbox[2], det.bbox[3]), color, 2)
            label = f"{det.class_name}: {det.confidence:.2f}"
            cv2.putText(result, label, (det.bbox[0], det.bbox[1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return result

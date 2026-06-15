#!/usr/bin/env python3

import cv2
import numpy as np
import yaml
import time
import logging
from pathlib import Path
from typing import Tuple, Optional


class CPUPreprocessor:
    """Preprocesare YOLO pe CPU cu OpenCV + NumPy."""

    def __init__(self, config_path: str = "config/robot_config.yaml"):
        self.config = self._load_config(config_path)
        self.fpga_cfg = self.config.get("fpga", {})
        self.input_size = tuple(self.fpga_cfg.get("output_size", [640, 640]))
        self.send_size = tuple(self.fpga_cfg.get("send_size", [320, 240]))

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("CPUPreprocessor")
        self.last_process_time_ms = 0.0
        self.process_count = 0

    def _load_config(self, config_path: str) -> dict:
        path = Path(config_path)
        if not path.is_absolute():
            root = Path(__file__).parent.parent.parent
            path = root / config_path
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def initialize(self) -> bool:
        self.logger.info(
            f"Preprocesor CPU: {self.send_size[0]}x{self.send_size[1]} → "
            f"{self.input_size[0]}x{self.input_size[1]}"
        )
        return True

    def process(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Preprocesează un cadru BGR.

        Returns:
            (imagine preprocesată uint8 BGR 640x640, timp_ms)
        """
        start = time.perf_counter()

        # Pas 1: redimensionare intermediară (simulează captura la rezoluție redusă)
        small = cv2.resize(frame, self.send_size, interpolation=cv2.INTER_LINEAR)

        # Pas 2: redimensionare la dimensiunea input YOLO
        resized = cv2.resize(small, self.input_size, interpolation=cv2.INTER_LINEAR)

        # Pas 3: normalizare pixeli (0–255 → float → re-quantizare uint8)
        normalized = resized.astype(np.float32) / 255.0
        normalized = (normalized * 255.0).clip(0, 255).astype(np.uint8)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self.last_process_time_ms = elapsed_ms
        self.process_count += 1

        return normalized, elapsed_ms

    def get_average_time_ms(self) -> float:
        return self.last_process_time_ms

    def cleanup(self):
        pass

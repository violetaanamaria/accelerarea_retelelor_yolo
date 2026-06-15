
import time
from pathlib import Path
from typing import Optional

import yaml

ROOT = Path(__file__).parent.parent


def resolve_config(config_path: str) -> str:
    path = Path(config_path)
    if not path.is_absolute():
        path = ROOT / config_path
    return str(path)


def run_pipeline_frame(
    frame,
    preprocessor,
    yolo,
    detector,
    decision_maker,
    use_decision: bool = True,
) -> dict:
    """Procesează un cadru și returnează metrici + rezultate intermediare."""
    preprocessed, preprocess_ms = preprocessor.process(frame)
    detections, inference_ms = yolo.infer(preprocessed)

    frame_shape = (frame.shape[0], frame.shape[1])
    obstacles = detector.detect_obstacles(detections, frame_shape)
    traffic_signs = detector.detect_traffic_signs(obstacles)

    decision = None
    if use_decision:
        decision = decision_maker.make_decision(obstacles, traffic_signs)

    total_ms = preprocess_ms + inference_ms

    return {
        "preprocess_ms": preprocess_ms,
        "inference_ms": inference_ms,
        "total_ms": total_ms,
        "fps": 1000.0 / total_ms if total_ms > 0 else 0.0,
        "detections": detections,
        "obstacles": obstacles,
        "traffic_signs": traffic_signs,
        "decision": decision,
        "preprocessed": preprocessed,
    }

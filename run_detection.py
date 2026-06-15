#!/usr/bin/env python3

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import List

import cv2
import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from pipeline import resolve_config, run_pipeline_frame
from preprocessing import get_preprocessor
from inference.yolo_inference import YOLOInference
from detection.obstacle_detector import ObstacleDetector
from decision.decision_maker import DecisionMaker
from camera.video_capture import VideoCapture


def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def run_on_images(args, config_path: str):
    """Procesează imagini statice."""
    logger = logging.getLogger("run_detection")

    image_paths = []
    for p in args.images:
        path = Path(p)
        if path.is_dir():
            for ext in ("*.jpg", "*.jpeg", "*.png"):
                image_paths.extend(path.glob(ext))
        elif path.exists():
            image_paths.append(path)

    if not image_paths:
        logger.error("Nicio imagine găsită!")
        return 1

    preprocessor = get_preprocessor(use_fpga=args.use_fpga, config_path=config_path)
    if not preprocessor.initialize():
        return 1

    yolo = YOLOInference(config_path)
    if not yolo.initialize():
        return 1

    detector = ObstacleDetector(config_path)
    decision_maker = DecisionMaker(config_path)

    output_dir = ROOT / "datasets" / "demo_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    mode = "FPGA" if args.use_fpga else "CPU"
    logger.info(f"Mod: {mode} | Imagini: {len(image_paths)}")

    for img_path in image_paths:
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue

        result = run_pipeline_frame(
            frame, preprocessor, yolo, detector, decision_maker
        )

        vis = yolo.visualize_detections(frame, result["detections"])
        header = np.zeros((50, vis.shape[1], 3), dtype=np.uint8)
        info = (
            f"Mod: {mode} | Preproc: {result['preprocess_ms']:.1f}ms | "
            f"Infer: {result['inference_ms']:.1f}ms | "
            f"Total: {result['total_ms']:.1f}ms | "
            f"Det: {len(result['detections'])}"
        )
        cv2.putText(header, info, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        vis = np.vstack([header, vis])

        out_path = output_dir / f"{mode.lower()}_{img_path.name}"
        cv2.imwrite(str(out_path), vis)
        logger.info(
            f"{img_path.name}: preproc={result['preprocess_ms']:.1f}ms "
            f"infer={result['inference_ms']:.1f}ms total={result['total_ms']:.1f}ms "
            f"det={len(result['detections'])}"
        )

    preprocessor.cleanup()
    logger.info(f"Rezultate salvate în {output_dir}")
    return 0


def run_on_camera(args, config_path: str):
    """Procesare live de la cameră."""
    logger = logging.getLogger("run_detection")

    preprocessor = get_preprocessor(use_fpga=args.use_fpga, config_path=config_path)
    if not preprocessor.initialize():
        return 1

    yolo = YOLOInference(config_path)
    if not yolo.initialize():
        return 1

    detector = ObstacleDetector(config_path)
    decision_maker = DecisionMaker(config_path)

    camera = VideoCapture(config_path)
    if not camera.initialize() or not camera.start():
        logger.error("Cameră indisponibilă. Folosește --images pentru test offline.")
        return 1

    mode = "FPGA" if args.use_fpga else "CPU"
    if args.use_fpga and hasattr(preprocessor, "is_simulation") and preprocessor.is_simulation():
        mode = "FPGA (simulare)"

    logger.info(f"Pornire detectare — mod {mode}. Apasă 'q' pentru ieșire.")

    preprocess_times, inference_times, total_times = [], [], []

    try:
        while True:
            ret, frame = camera.read()
            if not ret or frame is None:
                continue

            result = run_pipeline_frame(
                frame, preprocessor, yolo, detector, decision_maker
            )

            preprocess_times.append(result["preprocess_ms"])
            inference_times.append(result["inference_ms"])
            total_times.append(result["total_ms"])

            vis = yolo.visualize_detections(frame, result["detections"])

            lines = [
                f"Mod: {mode}",
                f"Preproc: {result['preprocess_ms']:.1f} ms",
                f"Infer: {result['inference_ms']:.1f} ms",
                f"Total: {result['total_ms']:.1f} ms ({result['fps']:.1f} FPS)",
                f"Det: {len(result['detections'])}",
            ]
            if result["decision"]:
                lines.append(f"Actiune: {result['decision'].action.value}")

            for i, line in enumerate(lines):
                cv2.putText(vis, line, (10, 25 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("YOLO FPGA Detection", vis)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        pass
    finally:
        camera.stop()
        preprocessor.cleanup()
        cv2.destroyAllWindows()

    if total_times:
        logger.info(
            f"Medii — preproc: {np.mean(preprocess_times):.1f}ms | "
            f"infer: {np.mean(inference_times):.1f}ms | "
            f"total: {np.mean(total_times):.1f}ms | "
            f"FPS: {1000/np.mean(total_times):.1f}"
        )
    return 0


def run_benchmark(args, config_path: str):
    """Compară performanța CPU vs CPU+FPGA."""
    logger = logging.getLogger("benchmark")
    logger.info("=" * 60)
    logger.info("BENCHMARK: CPU vs CPU+FPGA (Nexys 4 DDR)")
    logger.info("=" * 60)

    # Colectează cadre de test
    frames: List[np.ndarray] = []
    if args.images:
        for p in args.images:
            path = Path(p)
            if path.is_file():
                img = cv2.imread(str(path))
                if img is not None:
                    frames.append(img)
            elif path.is_dir():
                for f in list(path.glob("*.jpg"))[:args.num_frames]:
                    img = cv2.imread(str(f))
                    if img is not None:
                        frames.append(img)

    if not frames:
        test_dir = ROOT / "datasets" / "test_images"
        if test_dir.exists():
            for f in list(test_dir.glob("*.jpg"))[:args.num_frames]:
                img = cv2.imread(str(f))
                if img is not None:
                    frames.append(img)

    if not frames:
        logger.info("Generare cadre sintetice pentru benchmark...")
        for _ in range(args.num_frames):
            frames.append(np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))

    yolo = YOLOInference(config_path)
    if not yolo.initialize():
        return 1

    detector = ObstacleDetector(config_path)
    decision_maker = DecisionMaker(config_path)

    results = {}

    for mode_name, use_fpga in [("CPU", False), ("CPU+FPGA", True)]:
        preprocessor = get_preprocessor(use_fpga=use_fpga, config_path=config_path)
        if not preprocessor.initialize():
            continue

        sim_note = ""
        if use_fpga and hasattr(preprocessor, "is_simulation") and preprocessor.is_simulation():
            sim_note = " (simulare — placa neconectată)"

        preproc_times, infer_times, total_times = [], [], []

        # Warm-up
        for frame in frames[:2]:
            run_pipeline_frame(frame, preprocessor, yolo, detector, decision_maker, use_decision=False)

        for frame in frames:
            r = run_pipeline_frame(
                frame, preprocessor, yolo, detector, decision_maker, use_decision=False
            )
            preproc_times.append(r["preprocess_ms"])
            infer_times.append(r["inference_ms"])
            total_times.append(r["total_ms"])

        preprocessor.cleanup()

        results[mode_name] = {
            "mode": mode_name + sim_note,
            "frames": len(frames),
            "preprocess_ms": round(float(np.mean(preproc_times)), 2),
            "inference_ms": round(float(np.mean(infer_times)), 2),
            "total_ms": round(float(np.mean(total_times)), 2),
            "fps": round(1000.0 / float(np.mean(total_times)), 2),
        }

        logger.info(f"\n--- {mode_name}{sim_note} ---")
        logger.info(f"  Preprocesare:  {results[mode_name]['preprocess_ms']:.1f} ms")
        logger.info(f"  Inferență:     {results[mode_name]['inference_ms']:.1f} ms")
        logger.info(f"  Total:         {results[mode_name]['total_ms']:.1f} ms")
        logger.info(f"  FPS:           {results[mode_name]['fps']:.1f}")

    if "CPU" in results and "CPU+FPGA" in results:
        cpu = results["CPU"]
        fpga = results["CPU+FPGA"]
        speedup = cpu["total_ms"] / fpga["total_ms"] if fpga["total_ms"] > 0 else 0
        preproc_gain = cpu["preprocess_ms"] - fpga["preprocess_ms"]

        logger.info("\n--- COMPARATIE ---")
        logger.info(f"  Câștig preprocesare: {preproc_gain:.1f} ms")
        logger.info(f"  Speedup total:        {speedup:.2f}x")
        logger.info(f"  FPS CPU:              {cpu['fps']:.1f}")
        logger.info(f"  FPS CPU+FPGA:         {fpga['fps']:.1f}")

        results["comparison"] = {
            "preprocess_gain_ms": round(preproc_gain, 2),
            "speedup": round(speedup, 2),
        }

    # Salvare rezultate JSON
    out_path = ROOT / "logs" / "benchmark_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"\nRezultate salvate: {out_path}")

    # Grafic comparativ (dacă matplotlib disponibil)
    try:
        import matplotlib.pyplot as plt

        labels = ["Preprocesare", "Inferență", "Total"]
        cpu_vals = [results["CPU"]["preprocess_ms"], results["CPU"]["inference_ms"], results["CPU"]["total_ms"]]
        fpga_vals = [results["CPU+FPGA"]["preprocess_ms"], results["CPU+FPGA"]["inference_ms"], results["CPU+FPGA"]["total_ms"]]

        x = np.arange(len(labels))
        width = 0.35
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(x - width / 2, cpu_vals, width, label="CPU", color="#4A90D9")
        ax.bar(x + width / 2, fpga_vals, width, label="CPU+FPGA", color="#50C878")
        ax.set_ylabel("Timp (ms)")
        ax.set_title("Comparație CPU vs CPU+FPGA — Pipeline YOLO")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        chart_path = ROOT / "logs" / "benchmark_chart.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150)
        logger.info(f"Grafic salvat: {chart_path}")
    except ImportError:
        logger.info("Instalează matplotlib pentru grafic automat: pip install matplotlib")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Detectare obiecte YOLO — arhitectură hibridă CPU/FPGA (Nexys 4 DDR)"
    )
    parser.add_argument(
        "--use-fpga", action="store_true",
        help="Folosește FPGA Nexys 4 DDR pentru preprocesare (UART)",
    )
    parser.add_argument(
        "--benchmark", action="store_true",
        help="Compară CPU vs CPU+FPGA și generează grafic",
    )
    parser.add_argument(
        "--images", "-i", nargs="+",
        help="Imagini sau director pentru test (implicit: cameră live)",
    )
    parser.add_argument(
        "--config", "-c", default="config/robot_config.yaml",
        help="Fișier configurare",
    )
    parser.add_argument(
        "--num-frames", type=int, default=20,
        help="Număr cadre pentru benchmark (default: 20)",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    args = parser.parse_args()
    setup_logging(args.log_level)
    config_path = resolve_config(args.config)

    if args.benchmark:
        return run_benchmark(args, config_path)
    if args.images:
        return run_on_images(args, config_path)
    return run_on_camera(args, config_path)


if __name__ == "__main__":
    sys.exit(main())

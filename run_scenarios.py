#!/usr/bin/env python3

import argparse
import csv
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from pipeline import resolve_config, run_pipeline_frame
from preprocessing import get_preprocessor
from inference.yolo_inference import YOLOInference
from detection.obstacle_detector import ObstacleDetector
from decision.decision_maker import DecisionMaker
from scenarios.categories import SCENARIOS, filter_detections_for_scenario, filter_obstacles_for_scenario

SCENARIOS_ROOT = ROOT / "datasets" / "test_scenarios"
OUTPUT_ROOT = ROOT / "datasets" / "demo_results" / "scenarios"
LOGS_ROOT = ROOT / "logs"


def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def list_images(folder: Path) -> List[Path]:
    images = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        images.extend(sorted(folder.glob(ext)))
    return images


def collect_image_paths(scenario_key: str) -> List[Path]:
    folder = SCENARIOS_ROOT / SCENARIOS[scenario_key]["folder"]
    if not folder.exists():
        return []
    return list_images(folder)


def visualize_scenario(
    frame: np.ndarray,
    scenario_key: str,
    result: dict,
    mode_label: str,
) -> np.ndarray:
    """Desenează detecțiile relevante scenariului + header cu metrici."""
    vis = frame.copy()
    scenario_dets = filter_detections_for_scenario(result["detections"], scenario_key)
    scenario_obs = filter_obstacles_for_scenario(result["obstacles"], scenario_key)

    colors = {
        "persoane": (255, 128, 0),
        "vehicule": (0, 128, 255),
        "animale": (0, 200, 100),
        "semne": (0, 0, 255),
    }
    color = colors.get(scenario_key, (0, 255, 0))

    for det in scenario_dets:
        cv2.rectangle(vis, (det.bbox[0], det.bbox[1]), (det.bbox[2], det.bbox[3]), color, 2)
        label = f"{det.class_name}: {det.confidence:.2f}"
        cv2.putText(vis, label, (det.bbox[0], max(det.bbox[1] - 8, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    header_h = 80
    header = np.zeros((header_h, vis.shape[1], 3), dtype=np.uint8)
    title = SCENARIOS[scenario_key]["title"]
    lines = [
        f"{SCENARIOS[scenario_key]['section']} {title} | Mod: {mode_label}",
        f"Preproc: {result['preprocess_ms']:.1f}ms | Infer: {result['inference_ms']:.1f}ms | "
        f"Total: {result['total_ms']:.1f}ms | Det scenariu: {len(scenario_dets)}",
    ]
    if result["decision"]:
        lines.append(f"Decizie: {result['decision'].action.value} — {result['decision'].reason[:60]}")
    elif scenario_obs:
        top = scenario_obs[0]
        lines.append(
            f"Pericol max: {top.detection.class_name} [{top.danger_level.name}] "
            f"conf={top.detection.confidence:.2f}"
        )

    for i, line in enumerate(lines):
        cv2.putText(header, line, (10, 22 + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)

    return np.vstack([header, vis])


def summarize_scenario_runs(runs: List[dict]) -> dict:
    if not runs:
        return {"images": 0}

    confidences = []
    category_det_counts = []
    preprocess = []
    inference = []
    total = []
    decisions = []
    danger_levels = []

    for r in runs:
        category_det_counts.append(r["category_detections"])
        preprocess.append(r["preprocess_ms"])
        inference.append(r["inference_ms"])
        total.append(r["total_ms"])
        confidences.extend(r["confidences"])
        if r.get("decision"):
            decisions.append(r["decision"])
        danger_levels.extend(r.get("danger_levels", []))

    danger_counter = Counter(danger_levels)
    decision_counter = Counter(decisions)

    images_with_detection = sum(
        1 for r in runs
        if isinstance(r.get("category_detections"), (int, float))
        and r["category_detections"] > 0
    )

    return {
        "images": len(runs),
        "images_with_detection": images_with_detection,
        "detection_hit_rate": round(images_with_detection / len(runs), 3) if runs else 0.0,
        "avg_category_detections": round(float(np.mean(category_det_counts)), 2),
        "avg_confidence": round(float(np.mean(confidences)), 3) if confidences else 0.0,
        "min_confidence": round(float(np.min(confidences)), 3) if confidences else 0.0,
        "max_confidence": round(float(np.max(confidences)), 3) if confidences else 0.0,
        "avg_preprocess_ms": round(float(np.mean(preprocess)), 2),
        "avg_inference_ms": round(float(np.mean(inference)), 2),
        "avg_total_ms": round(float(np.mean(total)), 2),
        "avg_fps": round(1000.0 / float(np.mean(total)), 2) if total else 0.0,
        "decisions": dict(decision_counter),
        "danger_levels": dict(danger_counter),
        "total_category_detections": int(sum(category_det_counts)),
    }


def process_scenario_mode(
    scenario_key: str,
    use_fpga: bool,
    config_path: str,
    yolo: YOLOInference,
    detector: ObstacleDetector,
    decision_maker: DecisionMaker,
) -> dict:
    logger = logging.getLogger("run_scenarios")
    images = collect_image_paths(scenario_key)

    if not images:
        logger.warning(f"  [{scenario_key}] Nicio imagine în {SCENARIOS_ROOT / SCENARIOS[scenario_key]['folder']}")
        return {"runs": [], "summary": {"images": 0}, "mode": "CPU+FPGA" if use_fpga else "CPU"}

    preprocessor = get_preprocessor(use_fpga=use_fpga, config_path=config_path)
    if not preprocessor.initialize():
        return {"runs": [], "summary": {"images": 0}, "mode": "CPU+FPGA" if use_fpga else "CPU"}

    mode_label = "CPU+FPGA" if use_fpga else "CPU"
    if use_fpga and hasattr(preprocessor, "is_simulation") and preprocessor.is_simulation():
        mode_label = "CPU+FPGA (simulare)"

    out_dir = OUTPUT_ROOT / scenario_key
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = []
    decision_maker.reset_state()

    for img_path in images:
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue

        result = run_pipeline_frame(
            frame, preprocessor, yolo, detector, decision_maker, use_decision=True
        )

        scenario_dets = filter_detections_for_scenario(result["detections"], scenario_key)
        scenario_obs = filter_obstacles_for_scenario(result["obstacles"], scenario_key)

        run_data = {
            "image": img_path.name,
            "preprocess_ms": round(result["preprocess_ms"], 2),
            "inference_ms": round(result["inference_ms"], 2),
            "total_ms": round(result["total_ms"], 2),
            "fps": round(result["fps"], 2),
            "total_detections": len(result["detections"]),
            "category_detections": len(scenario_dets),
            "classes_found": [d.class_name for d in scenario_dets],
            "confidences": [round(d.confidence, 3) for d in scenario_dets],
            "danger_levels": [o.danger_level.name for o in scenario_obs],
            "decision": result["decision"].action.value if result["decision"] else None,
            "decision_reason": result["decision"].reason if result["decision"] else None,
        }
        runs.append(run_data)

        vis = visualize_scenario(frame, scenario_key, result, mode_label)
        out_name = f"{mode_label.lower().replace(' ', '_').replace('+', '_')}_{img_path.stem}.jpg"
        cv2.imwrite(str(out_dir / out_name), vis)

        logger.info(
            f"  [{scenario_key}][{mode_label}] {img_path.name}: "
            f"det_scenariu={len(scenario_dets)} total={result['total_ms']:.1f}ms "
            f"decizie={run_data['decision']}"
        )

    preprocessor.cleanup()

    return {
        "mode": mode_label,
        "runs": runs,
        "summary": summarize_scenario_runs(runs),
    }


PENDING_VALUE = "—"
FPGA_MODE_LABEL = "CPU+FPGA (Nexys 4 DDR)"


def create_fpga_placeholder(cpu_block: dict) -> dict:
    """Șablon FPGA — aceleași imagini, metrici goale (de completat după teste hardware)."""
    runs = []
    for run in cpu_block.get("runs", []):
        runs.append({
            "image": run["image"],
            "preprocess_ms": PENDING_VALUE,
            "inference_ms": PENDING_VALUE,
            "total_ms": PENDING_VALUE,
            "fps": PENDING_VALUE,
            "total_detections": PENDING_VALUE,
            "category_detections": PENDING_VALUE,
            "classes_found": [],
            "confidences": [],
            "danger_levels": [],
            "decision": PENDING_VALUE,
            "decision_reason": "de completat după teste pe Nexys 4 DDR",
            "pending": True,
        })

    n = len(runs)
    pending_summary = {
        "images": n,
        "pending": True,
        "images_with_detection": PENDING_VALUE,
        "detection_hit_rate": PENDING_VALUE,
        "total_category_detections": PENDING_VALUE,
        "avg_category_detections": PENDING_VALUE,
        "avg_confidence": PENDING_VALUE,
        "avg_preprocess_ms": PENDING_VALUE,
        "avg_inference_ms": PENDING_VALUE,
        "avg_total_ms": PENDING_VALUE,
        "avg_fps": PENDING_VALUE,
        "decisions": PENDING_VALUE,
        "danger_levels": PENDING_VALUE,
    }

    return {
        "mode": FPGA_MODE_LABEL,
        "pending": True,
        "runs": runs,
        "summary": pending_summary,
    }


def _format_metric(value) -> str:
    if value is PENDING_VALUE or value == PENDING_VALUE:
        return PENDING_VALUE
    if isinstance(value, dict):
        return str(value)
    return str(value)


def generate_markdown_report(all_results: dict, output_path: Path):
    lines = [
        "# Raport scenarii experimentale — YOLO FPGA",
        "",
        "Rezultate generate automat de `run_scenarios.py`.",
        "",
        "> **Notă:** rândurile marcate cu `—` la modul FPGA sunt de completat după testele",
        "> pe placa Nexys 4 DDR conectată (rulează `python3 run_scenarios.py` cu placa USB).",
        "",
        "## Tabel comparativ rezumat — CPU vs FPGA",
        "",
        "| Scenariu | Mod | Imagini | Img. cu detecție | Rata (%) | Nr. cutii | Det./img | Conf. | Preproc. | Infer. | Total | FPS |",
        "|----------|-----|---------|------------------|----------|----------|----------|-------|----------|--------|-------|-----|",
    ]

    for key, scenario in SCENARIOS.items():
        data = all_results.get(key, {})
        for mode_key, mod_label in (("cpu", "CPU"), ("fpga", FPGA_MODE_LABEL)):
            block = data.get(mode_key, {})
            s = block.get("summary", {})
            if s.get("images", 0) == 0 and not s.get("pending"):
                continue
            imgs = s.get("images", 0)
            hits = s.get("images_with_detection", PENDING_VALUE)
            if hits not in (PENDING_VALUE, None) and imgs:
                hit_str = f"{hits}/{imgs}"
                rate_str = f"{float(hits) / float(imgs) * 100:.1f}"
            else:
                hit_str = _format_metric(PENDING_VALUE)
                rate_str = _format_metric(PENDING_VALUE)

            lines.append(
                f"| {scenario['title']} | {mod_label} | "
                f"{_format_metric(imgs)} | "
                f"{hit_str} | "
                f"{rate_str} | "
                f"{_format_metric(s.get('total_category_detections', PENDING_VALUE))} | "
                f"{_format_metric(s.get('avg_category_detections', PENDING_VALUE))} | "
                f"{_format_metric(s.get('avg_confidence', PENDING_VALUE))} | "
                f"{_format_metric(s.get('avg_preprocess_ms', PENDING_VALUE))} | "
                f"{_format_metric(s.get('avg_inference_ms', PENDING_VALUE))} | "
                f"{_format_metric(s.get('avg_total_ms', PENDING_VALUE))} | "
                f"{_format_metric(s.get('avg_fps', PENDING_VALUE))} |"
            )
    lines.append("")

    for key, scenario in SCENARIOS.items():
        data = all_results.get(key, {})
        lines.append(f"## {scenario['section']} {scenario['title']}")
        lines.append("")
        lines.append(f"*{scenario['description']}*")
        lines.append("")
        lines.append(f"Clase monitorizate: `{', '.join(scenario['classes'])}`")
        lines.append("")

        for mode_key in ("cpu", "fpga"):
            block = data.get(mode_key, {})
            summary = block.get("summary", {})
            is_pending = block.get("pending") or summary.get("pending")

            if summary.get("images", 0) == 0 and not is_pending:
                lines.append(f"### Mod {mode_key.upper()} — fără imagini")
                lines.append("")
                continue

            mode_title = block.get("mode", mode_key.upper())
            lines.append(f"### Mod {mode_title}")
            if is_pending:
                lines.append("")
                lines.append("*Rezultate de completat după testele pe Nexys 4 DDR.*")
            lines.append("")
            lines.append("| Metrică | Valoare |")
            lines.append("|---------|---------|")
            lines.append(f"| Imagini procesate | {_format_metric(summary.get('images', PENDING_VALUE))} |")
            lines.append(
                f"| Imagini cu ≥1 detecție | "
                f"{_format_metric(summary.get('images_with_detection', PENDING_VALUE))} |"
            )
            lines.append(
                f"| Detecții scenariu (total) | "
                f"{_format_metric(summary.get('total_category_detections', PENDING_VALUE))} |"
            )
            lines.append(
                f"| Detecții medii / imagine | "
                f"{_format_metric(summary.get('avg_category_detections', PENDING_VALUE))} |"
            )
            lines.append(
                f"| Confidence medie | {_format_metric(summary.get('avg_confidence', PENDING_VALUE))} |"
            )
            lines.append(
                f"| Preprocesare medie | {_format_metric(summary.get('avg_preprocess_ms', PENDING_VALUE))} ms |"
            )
            lines.append(
                f"| Inferență medie | {_format_metric(summary.get('avg_inference_ms', PENDING_VALUE))} ms |"
            )
            lines.append(
                f"| Total mediu | {_format_metric(summary.get('avg_total_ms', PENDING_VALUE))} ms |"
            )
            lines.append(
                f"| FPS mediu | {_format_metric(summary.get('avg_fps', PENDING_VALUE))} |"
            )
            if summary.get("decisions") and not is_pending:
                lines.append(f"| Decizii | {summary['decisions']} |")
            elif is_pending:
                lines.append(f"| Decizii | {PENDING_VALUE} |")
            if summary.get("danger_levels") and not is_pending:
                lines.append(f"| Niveluri pericol | {summary['danger_levels']} |")
            elif is_pending:
                lines.append(f"| Niveluri pericol | {PENDING_VALUE} |")
            lines.append("")

            lines.append("| Imagine | Det. scenariu | Confidence | Total (ms) | Decizie |")
            lines.append("|---------|---------------|------------|------------|---------|")
            for run in block.get("runs", []):
                if run.get("pending"):
                    lines.append(
                        f"| {run['image']} | {PENDING_VALUE} | {PENDING_VALUE} | "
                        f"{PENDING_VALUE} | {PENDING_VALUE} |"
                    )
                    continue
                conf = run["confidences"]
                conf_str = f"{np.mean(conf):.2f}" if conf else "-"
                lines.append(
                    f"| {run['image']} | {run['category_detections']} | {conf_str} | "
                    f"{run['total_ms']} | {run.get('decision') or '-'} |"
                )
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def generate_csv_report(all_results: dict, output_path: Path):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scenariu", "sectiune", "mod", "imagine", "det_scenariu",
            "clase_gasite", "confidence_medie", "preprocess_ms", "inferenta_ms",
            "total_ms", "fps", "decizie", "motiv_decizie",
        ])
        for key, scenario in SCENARIOS.items():
            data = all_results.get(key, {})
            for mode_key in ("cpu", "fpga"):
                block = data.get(mode_key, {})
                for run in block.get("runs", []):
                    if run.get("pending"):
                        writer.writerow([
                            key,
                            scenario["section"],
                            block.get("mode", mode_key),
                            run["image"],
                            PENDING_VALUE,
                            "",
                            PENDING_VALUE,
                            PENDING_VALUE,
                            PENDING_VALUE,
                            PENDING_VALUE,
                            PENDING_VALUE,
                            PENDING_VALUE,
                            run.get("decision_reason", ""),
                        ])
                        continue
                    confs = run.get("confidences", [])
                    writer.writerow([
                        key,
                        scenario["section"],
                        block.get("mode", mode_key),
                        run["image"],
                        run["category_detections"],
                        ";".join(run.get("classes_found", [])),
                        round(float(np.mean(confs)), 3) if confs else "",
                        run["preprocess_ms"],
                        run["inference_ms"],
                        run["total_ms"],
                        run["fps"],
                        run.get("decision") or "",
                        run.get("decision_reason") or "",
                    ])


def generate_summary_csv(all_results: dict, output_path: Path):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scenariu", "sectiune", "mod", "imagini", "imagini_cu_detectie",
            "det_scenariu_total", "det_medii", "confidence_medie", "preprocess_ms",
            "inferenta_ms", "total_ms", "fps_mediu",
        ])
        for key, scenario in SCENARIOS.items():
            data = all_results.get(key, {})
            for mode_key in ("cpu", "fpga"):
                block = data.get(mode_key, {})
                s = block.get("summary", {})
                is_pending = block.get("pending") or s.get("pending")
                if s.get("images", 0) == 0 and not is_pending:
                    continue
                if is_pending:
                    writer.writerow([
                        key,
                        scenario["section"],
                        block.get("mode", mode_key),
                        s.get("images", 0),
                        PENDING_VALUE,
                        PENDING_VALUE,
                        PENDING_VALUE,
                        PENDING_VALUE,
                        PENDING_VALUE,
                        PENDING_VALUE,
                        PENDING_VALUE,
                        PENDING_VALUE,
                    ])
                    continue
                writer.writerow([
                    key,
                    scenario["section"],
                    data.get(mode_key, {}).get("mode", mode_key),
                    s["images"],
                    s.get("images_with_detection", 0),
                    s["total_category_detections"],
                    s["avg_category_detections"],
                    s["avg_confidence"],
                    s["avg_preprocess_ms"],
                    s["avg_inference_ms"],
                    s["avg_total_ms"],
                    s["avg_fps"],
                ])


def refresh_summaries(all_results: dict) -> dict:
    """Recalculează summary din runs (util la regenerare rapoarte)."""
    for data in all_results.values():
        for mode_key in ("cpu", "fpga"):
            block = data.get(mode_key)
            if not block or block.get("pending"):
                continue
            runs = block.get("runs", [])
            if runs and not any(r.get("pending") for r in runs):
                block["summary"] = summarize_scenario_runs(runs)
    return all_results


def attach_fpga_placeholders(all_results: dict) -> dict:
    """Adaugă secțiuni FPGA goale dacă testele hardware nu au rulat."""
    for key in SCENARIOS:
        data = all_results.setdefault(key, {})
        if "fpga" in data and not data["fpga"].get("pending"):
            continue
        cpu_block = data.get("cpu", {})
        if cpu_block.get("runs"):
            data["fpga"] = create_fpga_placeholder(cpu_block)
    return all_results


def write_all_reports(all_results: dict):
    all_results = refresh_summaries(all_results)
    all_results = attach_fpga_placeholders(all_results)
    LOGS_ROOT.mkdir(parents=True, exist_ok=True)
    json_path = LOGS_ROOT / "scenarios_results.json"
    csv_path = LOGS_ROOT / "scenarios_results.csv"
    summary_csv_path = LOGS_ROOT / "scenarios_summary.csv"
    md_path = LOGS_ROOT / "scenarios_report.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    generate_csv_report(all_results, csv_path)
    generate_summary_csv(all_results, summary_csv_path)
    generate_markdown_report(all_results, md_path)

    logger = logging.getLogger("run_scenarios")
    logger.info("\n" + "=" * 60)
    logger.info("RAPOARTE GENERATE:")
    logger.info(f"  JSON:    {json_path}")
    logger.info(f"  CSV:     {csv_path}")
    logger.info(f"  Rezumat: {summary_csv_path}")
    logger.info(f"  Markdown:{md_path}")
    logger.info(f"  Imagini: {OUTPUT_ROOT}")
    logger.info("=" * 60)


def regenerate_reports_from_json(json_path: Path) -> int:
    if not json_path.exists():
        logging.error(f"Fișier inexistent: {json_path}")
        return 1
    with open(json_path, "r", encoding="utf-8") as f:
        all_results = json.load(f)
    all_results = attach_fpga_placeholders(all_results)
    write_all_reports(all_results)
    return 0


def fpga_hardware_available(config_path: str) -> bool:
    """True doar dacă placa răspunde pe UART (nu simulare)."""
    preprocessor = get_preprocessor(use_fpga=True, config_path=config_path)
    try:
        if not preprocessor.initialize():
            return False
        if hasattr(preprocessor, "is_simulation") and preprocessor.is_simulation():
            return False
        return True
    finally:
        preprocessor.cleanup()


def run_all(args):
    logger = logging.getLogger("run_scenarios")
    config_path = resolve_config(args.config)

    logger.info("=" * 60)
    logger.info("TESTARE PE 4 SCENARII — YOLO FPGA")
    logger.info("=" * 60)

    yolo = YOLOInference(config_path)
    if not yolo.initialize():
        return 1

    detector = ObstacleDetector(config_path)
    decision_maker = DecisionMaker(config_path)

    scenario_keys = list(SCENARIOS.keys())
    if args.scenario:
        if args.scenario not in SCENARIOS:
            logger.error(f"Scenariu invalid: {args.scenario}. Opțiuni: {', '.join(SCENARIOS)}")
            return 1
        scenario_keys = [args.scenario]

    all_results = {}
    run_fpga = not args.cpu_only

    if run_fpga and not args.allow_fpga_simulation:
        if not fpga_hardware_available(config_path):
            logger.warning(
                "[ATENTIE] Nexys 4 DDR neconectată — rulez DOAR modul CPU.\n"
                "    Conectează placa (USB) și rulează din nou pentru comparație CPU vs FPGA.\n"
                "    Pentru test local fără hardware: --allow-fpga-simulation"
            )
            run_fpga = False

    for key in scenario_keys:
        meta = SCENARIOS[key]
        logger.info(f"\n>>> {meta['section']} {meta['title']}")

        all_results[key] = {}

        cpu_result = process_scenario_mode(
            key, False, config_path, yolo, detector, decision_maker
        )
        all_results[key]["cpu"] = cpu_result

        if run_fpga:
            fpga_result = process_scenario_mode(
                key, True, config_path, yolo, detector, decision_maker
            )
            all_results[key]["fpga"] = fpga_result
        elif cpu_result.get("runs"):
            all_results[key]["fpga"] = create_fpga_placeholder(cpu_result)

    all_results = attach_fpga_placeholders(all_results)
    write_all_reports(all_results)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Testare pe 4 scenarii experimentale")
    parser.add_argument("--scenario", choices=list(SCENARIOS.keys()),
                        help="Rulează un singur scenariu")
    parser.add_argument("--cpu-only", action="store_true",
                        help="Rulează doar modul CPU (fără FPGA)")
    parser.add_argument(
        "--allow-fpga-simulation", action="store_true",
        help="Permite modul FPGA simulat când placa nu e conectată (doar dev/test)",
    )
    parser.add_argument(
        "--reports-only",
        action="store_true",
        help="Regenerează rapoartele din logs/scenarios_results.json (fără inferență)",
    )
    parser.add_argument("--config", "-c", default="config/robot_config.yaml")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()
    setup_logging(args.log_level)
    if args.reports_only:
        return regenerate_reports_from_json(LOGS_ROOT / "scenarios_results.json")
    return run_all(args)


if __name__ == "__main__":
    sys.exit(main())

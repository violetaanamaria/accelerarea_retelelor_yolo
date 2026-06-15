#!/usr/bin/env python3

import argparse
import struct
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from preprocessing.fpga_preprocessor import (
    MAGIC_RX,
    MAGIC_TX,
    CMD_PREPROCESS,
    RESP_OK,
    FPGAPreprocessor,
)

try:
    import serial.tools.list_ports
except ImportError:
    serial = None


def find_port(hint: str | None) -> str | None:
    if hint and hint != "auto":
        return hint
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").lower()
        dev = p.device
        if any(k in desc for k in ("ftdi", "digilent", "uart", "usb serial")):
            return dev
        if "usbserial" in dev or "ttyUSB" in dev or "ttyACM" in dev:
            return dev
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Test UART preprocess pe Nexys 4 DDR")
    parser.add_argument("--port", default="auto", help="Port serial sau auto")
    parser.add_argument("--config", default="config/robot_config.yaml")
    parser.add_argument("--image", default=None, help="Imagine test (optional)")
    args = parser.parse_args()

    port = find_port(args.port)
    if port is None:
        print("[EROARE] Nu s-a găsit port serial. Conectează Nexys via USB.")
        print("   macOS: ls /dev/cu.usb*")
        return 1

    print(f"Port: {port}")

    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"[EROARE] Nu pot citi {args.image}")
            return 1
    else:
        test_dir = ROOT / "datasets" / "test_images"
        candidates = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
        if not candidates:
            print("[EROARE] Nicio imagine în datasets/test_images/")
            return 1
        frame = cv2.imread(str(candidates[0]))
        print(f"Imagine: {candidates[0].name}")

    prep = FPGAPreprocessor(config_path=str(ROOT / args.config))
    prep.port = port
    prep.simulate_on_fail = False

    if not prep.initialize():
        print("[EROARE] Conectare FPGA eșuată")
        return 1
    if prep.is_simulation():
        print("[EROARE] Intrat în mod simulare — verifică bitstream și cablu USB")
        return 1

    print("[OK] FPGA conectat (mod hardware)")
    t0 = time.perf_counter()
    try:
        out, ms = prep.process(frame)
    except Exception as exc:
        print(f"[EROARE] Eroare UART: {exc}")
        prep.cleanup()
        return 1
    elapsed = (time.perf_counter() - t0) * 1000.0

    if out.shape[:2] != (640, 640):
        print(f"[EROARE] Dimensiune greșită: {out.shape}")
        prep.cleanup()
        return 1

    out_path = ROOT / "datasets" / "demo_results" / "fpga_uart_test.jpg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), out)

    print(f"[OK] Răspuns OK: 640x640 BGR, {ms:.1f} ms preprocess, {elapsed:.1f} ms total")
    print(f"   Salvat: {out_path}")
    print("   LED-uri pe placă: idle=1, RX=2, payload=4, TX=8")
    prep.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

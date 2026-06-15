# Arhitectura Sistemului — Nexys 4 DDR + CPU

## Prezentare generală

Sistem hibrid **CPU–FPGA** pentru detectarea obiectelor cu YOLOv8n (pre-antrenat, COCO).

- **FPGA**: Digilent Nexys 4 DDR (Artix-7 XC7A100T) — recepție UART, stocare BRAM, **RGB pass-through**
- **Host**: MacBook / laptop — redimensionare finală, inferență YOLO, detecție, decizie
- **Comunicație**: UART/USB (921600 baud)

> Inferența YOLO, NMS și postprocesarea rulează **exclusiv pe CPU** (Ultralytics/PyTorch).
> FPGA **nu** face resize la 640×640, normalizare sau NMS.

## Diagrama bloc

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEM HOST (Python)                      │
│  Cameră → downscale 160×120 → UART → [FPGA BRAM] → UART     │
│         → resize 640×640 (OpenCV) → YOLOv8n → Detecție     │
└─────────────────────────────────────────────────────────────┘
                          │ UART
                          ▼
              ┌───────────────────────┐
              │  Nexys 4 DDR (FPGA)   │
              │  • Recepție UART      │
              │  • Stocare BRAM       │
              │  • RGB pass-through   │
              │  • Transmitere UART   │
              └───────────────────────┘
```

## Module software

| Modul | Fișier | Funcție |
|-------|--------|---------|
| Preprocesare CPU | `src/preprocessing/cpu_preprocessor.py` | Baseline: resize 160×120 → 640×640 |
| Preprocesare FPGA | `src/preprocessing/fpga_preprocessor.py` | UART ↔ Nexys; resize final pe host |
| Inferență | `src/inference/yolo_inference.py` | YOLOv8n Ultralytics (CPU) |
| Detecție | `src/detection/obstacle_detector.py` | ROI, nivel pericol, distanță |
| Decizie | `src/decision/decision_maker.py` | Acțiuni robot |
| Pipeline | `src/pipeline.py` | Legătură module |
| Main | `run_detection.py`, `run_scenarios.py` | Rulare + benchmark |

## Moduri de funcționare

### Baseline CPU
```
Cameră → Preprocesare CPU (OpenCV) → YOLO → Detecție → Decizie
```
`python3 run_detection.py` sau `python3 run_scenarios.py --cpu-only`

### Hibrid CPU + FPGA
```
Cameră → downscale → UART → FPGA (BRAM, pass-through) → UART → resize 640 → YOLO → …
```
`python3 run_detection.py --use-fpga` sau `python3 run_scenarios.py`

## Protocol UART (activ: `nexys_grayscale` în config)

```
Host → FPGA:  [AA 55] [CMD=0x01] [LEN:4B BE] [RGB 160×120×3] [XOR checksum]
FPGA → Host:  [AA 55] [CMD=0x81] [LEN:4B BE] [RGB 160×120×3] [XOR checksum]
```

Implementare Verilog: `fpga/rtl/nexys4ddr_yolo_preprocessor_top_v2.v` + `frame_engine.v`.

## Performanță măsurată (scenarii, logs/scenarios_summary.csv)

| Mod | Preprocesare | Total | FPS |
|-----|--------------|-------|-----|
| CPU | ~0,3 ms | ~31 ms | ~32 |
| CPU+FPGA | ~2200 ms | ~2230 ms | ~0,45 |

Goul de comunicare UART domină timpul end-to-end; nucleul FPGA e rapid, dar transferul serial limitează throughput-ul.

## Fișiere FPGA recomandate (Vivado)

- Top: `nexys4ddr_yolo_preprocessor_top_v2.v`
- `frame_engine.v`, `uart_rx.v`, `uart_tx.v`, `grayscale_rgb.v` (RGB pass-through)
- Constraints: `fpga/constraints/Nexys4DDR_UART.xdc`

Nu folosiți top-ul v1 streaming (`nexys4ddr_yolo_preprocessor_top.v`) — pierde bytes UART.

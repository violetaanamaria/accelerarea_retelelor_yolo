# Accelerarea Rețelelor YOLO pe FPGA pentru Detectarea Obiectelor

Proiect de diplomă — **Arhitecturi Avansate de Calculatoare**  
Autor: Draica Violeta Ana-Maria | Îndrumător: Conf.dr.Ing. Ciobanu Vlad

## Descriere

Sistem hibrid **CPU–FPGA** cu **YOLOv8n** (pre-antrenat, Ultralytics):

- **FPGA** (Nexys 4 DDR): recepție UART, stocare BRAM, **RGB pass-through** (160×120)
- **CPU** (MacBook): resize la 640×640, inferență YOLO, NMS, detecție obstacole, decizie
- **Comunicație**: UART 921600 baud (`/dev/cu.usbserial-*`, port UART = al doilea FTDI)

Fără ROS, fără Vitis AI, fără fine-tuning — model `yolov8n.pt` descărcat cu `scripts/download_yolo_model.sh`.

## Pipeline

```
Cameră → [downscale 160×120] → UART → FPGA (BRAM) → UART → [resize 640×640] → YOLOv8n (CPU) → Decizie
```

Mod CPU: resize complet pe OpenCV (`cpu_preprocessor.py`).

## Structura proiectului

```
yolo_fpga_robot/
├── run_detection.py          # Pipeline + benchmark
├── run_scenarios.py          # 4 scenarii × 100 imagini (cap. 5.7)
├── config/robot_config.yaml
├── src/
│   ├── camera/video_capture.py
│   ├── preprocessing/        # cpu_preprocessor.py, fpga_preprocessor.py
│   ├── inference/yolo_inference.py
│   ├── detection/obstacle_detector.py
│   ├── decision/decision_maker.py
│   ├── scenarios/categories.py
│   └── pipeline.py
├── scripts/                  # download_yolo_model.sh, test_fpga_uart.py etc.
├── docs/architecture.md
├── fpga/
│   ├── grayscale/            # preprocesare grayscale
│   ├── rgb/                  # preprocesare RGB
│   ├── rgb_upgraded/         # preprocesare RGB (varianta mai rapida)
│   └── README.md             # instructiuni Vivado + programare placa
└── logs/scenarios_summary.csv
```

## Programarea plăcii FPGA

> **Placa Nexys 4 DDR trebuie programată separat înainte de a putea folosi modul FPGA.**

Fișierele de proiect Vivado (sursele Verilog/SystemVerilog, constrângerile XDC și bitstream-ul generat) se găsesc în directorul `fpga/`. Urmează instrucțiunile din `fpga/README.md` pentru a sintetiza și a încărca bitstream-ul pe placă via Vivado sau `openFPGALoader`.

## Instalare

```bash
pip3 install -r requirements.txt
bash scripts/download_yolo_model.sh
```

## Utilizare

```bash
# CPU baseline
python3 run_detection.py --images datasets/test_images/

# Cu Nexys (bitstream v2 încărcat, port UART)
python3 scripts/test_fpga_uart.py --port /dev/cu.usbserial-XXXX
python3 run_detection.py --use-fpga --images datasets/test_images/

# Scenarii experimentale
python3 run_scenarios.py --cpu-only
python3 run_scenarios.py   # CPU + FPGA dacă placa e conectată
```

## Performanță măsurată

| Mod | Preproc. | Total | FPS |
|-----|----------|-------|-----|
| CPU | ~0,3 ms | ~31 ms | ~32 |
| CPU+FPGA | ~2200 ms | ~2230 ms | ~0,45 |

Detectarea (cutii, rate) este **identică** între moduri; diferența e doar la timp (UART).

## Licență

MIT License

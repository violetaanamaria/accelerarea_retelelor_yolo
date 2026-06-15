#!/bin/bash

##############################################################################
# Script descărcare model YOLO optimizat pentru robotul tău
# Autor: Draica Violeta Ana-Maria
##############################################################################

set -e

echo "----------------------------------------------------------------"
echo "  DESCĂRCARE MODEL YOLO OPTIMIZAT"
echo "  Sistem YOLO FPGA Robot"
echo "----------------------------------------------------------------"
echo ""

# Creare директория
mkdir -p datasets/models
cd datasets/models

# Meniu selecție model
echo "Selectează modelul YOLO:"
echo ""
echo "  1) YOLOv5n - Ultra rapid (45 FPS, 1.9 MB) "
echo "  2) YOLOv5s - Echilibrat (35 FPS, 7.2 MB) RECOMANDAT"
echo "  3) YOLOv5m - Acurat (25 FPS, 21 MB) "
echo "  4) YOLOv8n - Nou & rapid (40 FPS, 3.2 MB)"
echo "  5) YOLOv8s - Nou & acurat (30 FPS, 11.2 MB)"
echo ""
read -p "Alege opțiunea (1-5) [default: 2]: " choice
choice=${choice:-2}

case $choice in
    1)
        MODEL_NAME="yolov5n"
        MODEL_URL="https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5n.pt"
        echo "OK: Selectat: YOLOv5n (ultra rapid)"
        ;;
    2)
        MODEL_NAME="yolov5s"
        MODEL_URL="https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt"
        echo "OK: Selectat: YOLOv5s (echilibrat) "
        ;;
    3)
        MODEL_NAME="yolov5m"
        MODEL_URL="https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5m.pt"
        echo "OK: Selectat: YOLOv5m (acurat)"
        ;;
    4)
        MODEL_NAME="yolov8n"
        echo "OK: Selectat: YOLOv8n (nou & rapid)"
        echo "Instalare ultralytics..."
        pip3 install -q ultralytics
        python3 << EOF
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
model.export(format='onnx')
print("OK: Model descărcat și exportat")
EOF
        echo "OK: YOLOv8n gata!"
        exit 0
        ;;
    5)
        MODEL_NAME="yolov8s"
        echo "OK: Selectat: YOLOv8s (nou & acurat)"
        echo "Instalare ultralytics..."
        pip3 install -q ultralytics
        python3 << EOF
from ultralytics import YOLO
model = YOLO('yolov8s.pt')
model.export(format='onnx')
print("OK: Model descărcat și exportat")
EOF
        echo "OK: YOLOv8s gata!"
        exit 0
        ;;
    *)
        echo "[EROARE] Opțiune invalidă! Folosesc YOLOv5s (default)"
        MODEL_NAME="yolov5s"
        MODEL_URL="https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt"
        ;;
esac

echo ""
echo "Descărcare $MODEL_NAME..."

# Verifică dacă există deja
if [ -f "${MODEL_NAME}.pt" ]; then
    echo "[ATENTIE] Modelul ${MODEL_NAME}.pt există deja!"
    read -p "Vrei să-l descarci din nou? (y/N): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "OK: Folosim modelul existent"
        exit 0
    fi
    rm -f "${MODEL_NAME}.pt"
fi

# Descarcă model
wget -q --show-progress "$MODEL_URL" -O "${MODEL_NAME}.pt"

if [ $? -eq 0 ]; then
    echo "OK: Model descărcat cu succes!"
    echo ""
    
    # Informații model
    echo "Informații model:"
    ls -lh "${MODEL_NAME}.pt"
    
    # Exportă în ONNX (pentru FPGA)
    echo ""
    echo "Exportare în format ONNX pentru FPGA..."
    
    python3 << EOF
import torch
from pathlib import Path

try:
    # Încarcă model
    model = torch.hub.load('ultralytics/yolov5', 'custom', 
                           path='${MODEL_NAME}.pt', force_reload=False)
    
    # Exportă ONNX
    model.export(format='onnx', dynamic=False, simplify=True)
    
    print("OK: Export ONNX reușit!")
    
    # Info model
    print(f"\nDetalii model ${MODEL_NAME}:")
    print(f"  - Clase: {len(model.names)} (COCO dataset)")
    print(f"  - Clase obstacole relevante:")
    relevant = ['person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck']
    for cls in relevant:
        if cls in model.names:
            print(f"    • {cls}")
    
except Exception as e:
    print(f"[ATENTIE] Eroare la export: {e}")
    print("  Poți exporta manual mai târziu cu:")
    print(f"    python3 -m torch.hub load ultralytics/yolov5 custom path=${MODEL_NAME}.pt")
EOF
    
    echo ""
    echo "----------------------------------------------------------------"
    echo "[OK] MODEL GATA DE UTILIZARE!"
    echo "----------------------------------------------------------------"
    echo ""
    echo "Fișiere generate:"
    ls -lh ${MODEL_NAME}*
    echo ""
    echo "PAȘI URMĂTORI:"
    echo ""
    echo "  1. Pentru calibrare INT8 (IMPORTANT pentru FPGA):"
    echo "     bash scripts/calibrate_and_compile.sh"
    echo ""
    echo "  2. Pentru testare model pe imagini:"
    echo "     python3 test_model.py --model datasets/models/${MODEL_NAME}.pt"
    echo ""
    echo "  3. Pentru antrenament custom pe propriile date:"
    echo "     python3 train_custom_yolo.py"
    echo ""
    echo "  4. Pentru rulare sistem complet:"
    echo "     bash scripts/start_robot.sh"
    echo ""
    echo "----------------------------------------------------------------"
    
else
    echo "[EROARE] Eroare la descărcare!"
    echo "Încearcă manual:"
    echo "  wget $MODEL_URL -O datasets/models/${MODEL_NAME}.pt"
    exit 1
fi


#!/bin/bash
###############################################################################
# Pornire sistem YOLO FPGA — Python pur (fără ROS)
# Placă: Digilent Nexys 4 DDR | Host: MacBook / laptop
###############################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================="
echo " YOLO FPGA — Detectare Obiecte"
echo " Nexys 4 DDR + Python"
echo "========================================="

cd "$(dirname "$0")/.."

# Verifică model
if [ ! -f "./datasets/models/yolov8n.pt" ] && [ ! -f "./models/yolov8n.pt" ]; then
    echo -e "${YELLOW}Model YOLOv8n lipsă. Descărcare...${NC}"
    bash scripts/download_yolo_model.sh
fi
echo -e "${GREEN}OK: Model YOLO disponibil${NC}"

echo ""
echo "Selectați modul:"
echo "  1) CPU only (baseline)"
echo "  2) CPU + FPGA (Nexys 4 DDR via UART)"
echo "  3) Benchmark comparativ CPU vs FPGA"
echo "  4) Demo imagini statice (CPU)"
echo "  5) Test 4 scenarii (persoane, vehicule, animale, semne)"
read -p "Opțiune (1-5): " choice

case $choice in
    1)
        python3 run_detection.py
        ;;
    2)
        echo -e "${YELLOW}Verificare port serial...${NC}"
        ls /dev/tty.usb* /dev/cu.usb* 2>/dev/null || echo "(niciun port detectat — va rula simulare)"
        python3 run_detection.py --use-fpga
        ;;
    3)
        python3 run_detection.py --benchmark --images datasets/test_images/
        ;;
    4)
        python3 run_detection.py --images datasets/test_images/
        ;;
    5)
        bash scripts/setup_scenario_images.sh 2>/dev/null || true
        python3 run_scenarios.py
        ;;
    *)
        echo -e "${RED}Opțiune invalidă${NC}"
        exit 1
        ;;
esac

#!/bin/bash
# Pregătește folderele și imaginile pentru cele 4 scenarii de test

set -e
cd "$(dirname "$0")/.."

BASE="datasets/test_scenarios"
mkdir -p "$BASE"/{persoane,vehicule,animale,semne}

echo "Structură scenarii creată în $BASE"

copy_if_exists() {
    local src="$1" dest="$2"
    if [ -f "$src" ]; then
        cp "$src" "$dest"
        echo "  OK: Copiat $(basename "$src") → $dest"
    fi
}

download_if_missing() {
    local url="$1" dest="$2"
    if [ ! -f "$dest" ]; then
        echo "  Descarcare Descărcare $(basename "$dest")..."
        curl -fsSL "$url" -o "$dest" || wget -q "$url" -O "$dest" || echo "  EROARE: Eșec descărcare $url"
    else
        echo "  OK: Există deja $(basename "$dest")"
    fi
}

echo ""
echo "1/4 Persoane"
download_if_missing "https://ultralytics.com/images/zidane.jpg" "$BASE/persoane/person_01.jpg"
copy_if_exists "datasets/test_images/traffic.jpg" "$BASE/persoane/person_02_traffic.jpg"

echo ""
echo "2/4 Vehicule"
download_if_missing "https://ultralytics.com/images/bus.jpg" "$BASE/vehicule/bus_01.jpg"
copy_if_exists "datasets/test_images/street.jpg" "$BASE/vehicule/street_01.jpg"

echo ""
echo "3/4 Animale"
# Imagini COCO publice (câine, pisică) — adaugă manual dacă descărcarea eșuează
download_if_missing "https://images.unsplash.com/photo-1548191265-cc70d3d45c0c?w=640" "$BASE/animale/dog_01.jpg" 2>/dev/null || true
download_if_missing "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=640" "$BASE/animale/cat_01.jpg" 2>/dev/null || true
echo "  Info: Dacă lipsesc imagini, adaugă manual poze cu câini/pisici în $BASE/animale/"

echo ""
echo "4/4 Semne"
download_if_missing "https://ultralytics.com/images/bus.jpg" "$BASE/semne/traffic_scene_01.jpg"
echo "  Info: Pentru semne STOP/semafoare clare, adaugă poze dedicate în $BASE/semne/"

echo ""
echo "[OK] Setup complet. Rulează:"
echo "   python3 run_scenarios.py"

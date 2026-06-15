#!/bin/bash
# Wrapper — descarcă imagini COCO per scenariu
set -e
cd "$(dirname "$0")/.."

PER_SCENARIO=15
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --per-scenario) PER_SCENARIO="$2"; shift 2 ;;
        --clear) EXTRA_ARGS+=("--clear"); shift ;;
        --dry-run) EXTRA_ARGS+=("--dry-run"); shift ;;
        *) EXTRA_ARGS+=("$1"); shift ;;
    esac
done

echo "Descărcare COCO val2017 → datasets/test_scenarios/"
echo "Imagini per scenariu: $PER_SCENARIO"
echo ""

python3 scripts/download_coco_scenarios.py \
    --per-scenario "$PER_SCENARIO" \
    "${EXTRA_ARGS[@]}"

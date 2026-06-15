# Raport scenarii experimentale — YOLO FPGA

Rezultate generate automat de `run_scenarios.py`.

> **Notă:** rândurile marcate cu `—` la modul FPGA sunt de completat după testele
> pe placa Nexys 4 DDR conectată (rulează `python3 run_scenarios.py` cu placa USB).

## Tabel comparativ rezumat — CPU vs FPGA

| Scenariu | Mod | Imagini | Img. cu detecție | Rata (%) | Nr. cutii | Det./img | Conf. | Preproc. | Infer. | Total | FPS |
|----------|-----|---------|------------------|----------|----------|----------|-------|----------|--------|-------|-----|
| Detectarea persoanelor | CPU | 100 | 64/100 | 64.0 | 109 | 1.09 | 0.683 | 0.34 | 33.27 | 33.61 | 29.75 |
| Detectarea persoanelor | CPU+FPGA (Nexys 4 DDR) | 100 | 64/100 | 64.0 | 109 | 1.09 | 0.683 | 61.1 | 31.41 | 92.5 | 10.81 |
| Detectarea vehiculelor | CPU | 100 | 49/100 | 49.0 | 64 | 0.64 | 0.612 | 0.33 | 31.34 | 31.66 | 31.58 |
| Detectarea vehiculelor | CPU+FPGA (Nexys 4 DDR) | 100 | 49/100 | 49.0 | 64 | 0.64 | 0.612 | 61.13 | 31.64 | 92.77 | 10.78 |
| Detectarea animalelor | CPU | 100 | 18/100 | 18.0 | 20 | 0.2 | 0.686 | 0.33 | 30.94 | 31.27 | 31.98 |
| Detectarea animalelor | CPU+FPGA (Nexys 4 DDR) | 100 | 18/100 | 18.0 | 20 | 0.2 | 0.686 | 61.13 | 30.47 | 91.6 | 10.92 |
| Detectarea semnelor de circulație | CPU | 100 | 42/100 | 42.0 | 56 | 0.56 | 0.747 | 0.31 | 29.78 | 30.1 | 33.23 |
| Detectarea semnelor de circulație | CPU+FPGA (Nexys 4 DDR) | 100 | 42/100 | 42.0 | 56 | 0.56 | 0.747 | 61.11 | 30.71 | 91.82 | 10.89 |

## 5.7.1 Detectarea persoanelor

*Pietoni și persoane în mediul urban / interior*

Clase monitorizate: `person`

### Mod CPU

| Metrică | Valoare |
|---------|---------|
| Imagini procesate | 100 |
| Imagini cu ≥1 detecție | 64 |
| Detecții scenariu (total) | 109 |
| Detecții medii / imagine | 1.09 |
| Confidence medie | 0.683 |
| Preprocesare medie | 0.34 ms |
| Inferență medie | 33.27 ms |
| Total mediu | 33.61 ms |
| FPS mediu | 29.75 |
| Decizii | {'emergency_stop': 48, 'continue': 40, 'stop': 9, 'slow_down': 3} |
| Niveluri pericol | {'CRITICAL': 54, 'LOW': 14, 'HIGH': 13} |

| Imagine | Det. scenariu | Confidence | Total (ms) | Decizie |
|---------|---------------|------------|------------|---------|
| coco_000000000872_person.jpg | 1 | 0.58 | 55.91 | emergency_stop |
| coco_000000002261_person.jpg | 1 | 0.64 | 34.05 | emergency_stop |
| coco_000000002431_person.jpg | 0 | - | 33.28 | emergency_stop |
| coco_000000017899_person.jpg | 0 | - | 31.2 | continue |
| coco_000000019109_person.jpg | 0 | - | 31.74 | continue |
| coco_000000025057_person.jpg | 1 | 0.81 | 29.61 | continue |
| coco_000000037689_person.jpg | 2 | 0.48 | 30.78 | continue |
| coco_000000054931_person.jpg | 1 | 0.83 | 29.87 | continue |
| coco_000000055022_person.jpg | 0 | - | 29.92 | continue |
| coco_000000060102_person.jpg | 1 | 0.72 | 31.51 | emergency_stop |
| coco_000000060932_person.jpg | 2 | 0.58 | 31.24 | emergency_stop |
| coco_000000072281_person.jpg | 1 | 0.77 | 30.36 | emergency_stop |
| coco_000000080022_person.jpg | 1 | 0.88 | 31.55 | emergency_stop |
| coco_000000084241_person.jpg | 2 | 0.74 | 32.45 | emergency_stop |
| coco_000000085329_person.jpg | 1 | 0.56 | 35.33 | emergency_stop |
| coco_000000085682_person.jpg | 0 | - | 33.16 | continue |
| coco_000000103723_person.jpg | 1 | 0.71 | 34.64 | continue |
| coco_000000114884_person.jpg | 2 | 0.70 | 46.61 | continue |
| coco_000000118405_person.jpg | 0 | - | 36.25 | continue |
| coco_000000119516_person.jpg | 0 | - | 34.13 | continue |
| coco_000000122606_person.jpg | 0 | - | 31.63 | continue |
| coco_000000128675_person.jpg | 3 | 0.60 | 34.83 | continue |
| coco_000000132587_person.jpg | 0 | - | 33.34 | continue |
| coco_000000135890_person.jpg | 0 | - | 42.43 | continue |
| coco_000000137294_person.jpg | 1 | 0.84 | 42.25 | continue |
| coco_000000140270_person.jpg | 1 | 0.68 | 34.5 | continue |
| coco_000000143068_person.jpg | 1 | 0.81 | 33.76 | continue |
| coco_000000143556_person.jpg | 1 | 0.69 | 33.95 | emergency_stop |
| coco_000000148739_person.jpg | 1 | 0.80 | 33.48 | emergency_stop |
| coco_000000154358_person.jpg | 0 | - | 34.37 | emergency_stop |
| coco_000000157601_person.jpg | 1 | 0.73 | 34.92 | emergency_stop |
| coco_000000176037_person.jpg | 0 | - | 36.55 | emergency_stop |
| coco_000000179174_person.jpg | 2 | 0.57 | 35.38 | emergency_stop |
| coco_000000185950_person.jpg | 1 | 0.50 | 36.29 | continue |
| coco_000000206411_person.jpg | 0 | - | 38.36 | continue |
| coco_000000207306_person.jpg | 0 | - | 33.22 | continue |
| coco_000000209757_person.jpg | 0 | - | 33.93 | continue |
| coco_000000212453_person.jpg | 0 | - | 34.48 | continue |
| coco_000000214869_person.jpg | 0 | - | 34.1 | continue |
| coco_000000215072_person.jpg | 1 | 0.60 | 31.38 | emergency_stop |
| coco_000000216277_person.jpg | 1 | 0.56 | 32.34 | emergency_stop |
| coco_000000224807_person.jpg | 7 | 0.65 | 31.62 | emergency_stop |
| coco_000000227482_person.jpg | 1 | 0.88 | 32.94 | emergency_stop |
| coco_000000248616_person.jpg | 3 | 0.64 | 40.04 | emergency_stop |
| coco_000000250127_person.jpg | 1 | 0.85 | 32.12 | emergency_stop |
| coco_000000256775_person.jpg | 4 | 0.65 | 32.13 | continue |
| coco_000000272136_person.jpg | 0 | - | 30.7 | continue |
| coco_000000279541_person.jpg | 0 | - | 32.65 | continue |
| coco_000000289343_person.jpg | 1 | 0.48 | 36.13 | stop |
| coco_000000289415_person.jpg | 1 | 0.80 | 36.5 | stop |
| coco_000000292456_person.jpg | 0 | - | 34.88 | stop |
| coco_000000295478_person.jpg | 1 | 0.91 | 33.24 | emergency_stop |
| coco_000000303566_person.jpg | 4 | 0.63 | 33.39 | emergency_stop |
| coco_000000312192_person.jpg | 0 | - | 32.91 | emergency_stop |
| coco_000000313034_person.jpg | 2 | 0.68 | 32.69 | emergency_stop |
| coco_000000315187_person.jpg | 0 | - | 33.78 | emergency_stop |
| coco_000000317999_person.jpg | 0 | - | 35.7 | emergency_stop |
| coco_000000323355_person.jpg | 1 | 0.77 | 35.83 | emergency_stop |
| coco_000000327701_person.jpg | 3 | 0.78 | 31.15 | emergency_stop |
| coco_000000332351_person.jpg | 5 | 0.54 | 31.23 | emergency_stop |
| coco_000000336053_person.jpg | 2 | 0.63 | 33.62 | emergency_stop |
| coco_000000345361_person.jpg | 3 | 0.82 | 33.32 | emergency_stop |
| coco_000000347254_person.jpg | 3 | 0.79 | 40.34 | emergency_stop |
| coco_000000354307_person.jpg | 0 | - | 43.09 | continue |
| coco_000000354547_person.jpg | 1 | 0.84 | 33.84 | continue |
| coco_000000368212_person.jpg | 1 | 0.62 | 33.79 | continue |
| coco_000000372819_person.jpg | 2 | 0.74 | 31.51 | stop |
| coco_000000383337_person.jpg | 1 | 0.55 | 33.41 | stop |
| coco_000000385190_person.jpg | 0 | - | 33.66 | stop |
| coco_000000390246_person.jpg | 1 | 0.73 | 35.72 | stop |
| coco_000000391722_person.jpg | 2 | 0.68 | 36.93 | stop |
| coco_000000394275_person.jpg | 0 | - | 34.84 | stop |
| coco_000000398377_person.jpg | 3 | 0.75 | 34.84 | emergency_stop |
| coco_000000406129_person.jpg | 1 | 0.47 | 32.04 | emergency_stop |
| coco_000000414170_person.jpg | 3 | 0.76 | 33.48 | emergency_stop |
| coco_000000417632_person.jpg | 1 | 0.54 | 32.45 | emergency_stop |
| coco_000000427997_person.jpg | 1 | 0.69 | 32.73 | emergency_stop |
| coco_000000428111_person.jpg | 0 | - | 31.01 | emergency_stop |
| coco_000000434230_person.jpg | 0 | - | 29.19 | continue |
| coco_000000437351_person.jpg | 1 | 0.65 | 31.76 | continue |
| coco_000000441491_person.jpg | 0 | - | 30.5 | continue |
| coco_000000447465_person.jpg | 0 | - | 32.49 | continue |
| coco_000000459195_person.jpg | 3 | 0.71 | 30.56 | continue |
| coco_000000481480_person.jpg | 0 | - | 30.7 | continue |
| coco_000000490936_person.jpg | 1 | 0.76 | 31.23 | continue |
| coco_000000492758_person.jpg | 0 | - | 30.75 | continue |
| coco_000000497568_person.jpg | 0 | - | 31.73 | continue |
| coco_000000504389_person.jpg | 1 | 0.66 | 30.95 | emergency_stop |
| coco_000000512836_person.jpg | 0 | - | 31.55 | emergency_stop |
| coco_000000516173_person.jpg | 1 | 0.88 | 31.15 | emergency_stop |
| coco_000000527528_person.jpg | 0 | - | 29.74 | slow_down |
| coco_000000529939_person.jpg | 1 | 0.80 | 30.29 | slow_down |
| coco_000000548780_person.jpg | 3 | 0.63 | 31.84 | slow_down |
| coco_000000551215_person.jpg | 1 | 0.90 | 32.07 | emergency_stop |
| coco_000000553788_person.jpg | 1 | 0.64 | 30.22 | emergency_stop |
| coco_000000559543_person.jpg | 1 | 0.84 | 31.29 | emergency_stop |
| coco_000000561223_person.jpg | 1 | 0.91 | 30.9 | emergency_stop |
| coco_000000563604_person.jpg | 3 | 0.56 | 31.37 | emergency_stop |
| coco_000000563648_person.jpg | 0 | - | 30.26 | emergency_stop |
| coco_000000576955_person.jpg | 1 | 0.49 | 31.19 | continue |

### Mod CPU+FPGA

| Metrică | Valoare |
|---------|---------|
| Imagini procesate | 100 |
| Imagini cu ≥1 detecție | 64 |
| Detecții scenariu (total) | 109 |
| Detecții medii / imagine | 1.09 |
| Confidence medie | 0.683 |
| Preprocesare medie | 61.1 ms |
| Inferență medie | 31.41 ms |
| Total mediu | 92.5 ms |
| FPS mediu | 10.81 |
| Decizii | {'emergency_stop': 55, 'continue': 33, 'stop': 12} |
| Niveluri pericol | {'CRITICAL': 54, 'LOW': 14, 'HIGH': 13} |

| Imagine | Det. scenariu | Confidence | Total (ms) | Decizie |
|---------|---------------|------------|------------|---------|
| coco_000000000872_person.jpg | 1 | 0.58 | 6127.29 | emergency_stop |
| coco_000000002261_person.jpg | 1 | 0.64 | 31.47 | emergency_stop |
| coco_000000002431_person.jpg | 0 | - | 34.38 | emergency_stop |
| coco_000000017899_person.jpg | 0 | - | 33.65 | continue |
| coco_000000019109_person.jpg | 0 | - | 31.03 | continue |
| coco_000000025057_person.jpg | 1 | 0.81 | 33.01 | continue |
| coco_000000037689_person.jpg | 2 | 0.48 | 30.83 | continue |
| coco_000000054931_person.jpg | 1 | 0.83 | 30.16 | continue |
| coco_000000055022_person.jpg | 0 | - | 30.12 | continue |
| coco_000000060102_person.jpg | 1 | 0.72 | 31.67 | emergency_stop |
| coco_000000060932_person.jpg | 2 | 0.58 | 30.66 | emergency_stop |
| coco_000000072281_person.jpg | 1 | 0.77 | 30.65 | emergency_stop |
| coco_000000080022_person.jpg | 1 | 0.88 | 32.25 | emergency_stop |
| coco_000000084241_person.jpg | 2 | 0.74 | 34.43 | emergency_stop |
| coco_000000085329_person.jpg | 1 | 0.56 | 32.16 | emergency_stop |
| coco_000000085682_person.jpg | 0 | - | 30.36 | continue |
| coco_000000103723_person.jpg | 1 | 0.71 | 29.68 | continue |
| coco_000000114884_person.jpg | 2 | 0.70 | 31.45 | continue |
| coco_000000118405_person.jpg | 0 | - | 30.87 | continue |
| coco_000000119516_person.jpg | 0 | - | 31.19 | continue |
| coco_000000122606_person.jpg | 0 | - | 32.27 | continue |
| coco_000000128675_person.jpg | 3 | 0.60 | 32.04 | continue |
| coco_000000132587_person.jpg | 0 | - | 30.54 | continue |
| coco_000000135890_person.jpg | 0 | - | 31.31 | continue |
| coco_000000137294_person.jpg | 1 | 0.84 | 31.5 | continue |
| coco_000000140270_person.jpg | 1 | 0.68 | 32.57 | continue |
| coco_000000143068_person.jpg | 1 | 0.81 | 30.81 | continue |
| coco_000000143556_person.jpg | 1 | 0.69 | 30.13 | emergency_stop |
| coco_000000148739_person.jpg | 1 | 0.80 | 30.14 | emergency_stop |
| coco_000000154358_person.jpg | 0 | - | 31.94 | emergency_stop |
| coco_000000157601_person.jpg | 1 | 0.73 | 29.95 | emergency_stop |
| coco_000000176037_person.jpg | 0 | - | 29.82 | emergency_stop |
| coco_000000179174_person.jpg | 2 | 0.57 | 31.0 | emergency_stop |
| coco_000000185950_person.jpg | 1 | 0.50 | 30.82 | continue |
| coco_000000206411_person.jpg | 0 | - | 30.42 | continue |
| coco_000000207306_person.jpg | 0 | - | 30.59 | continue |
| coco_000000209757_person.jpg | 0 | - | 33.92 | continue |
| coco_000000212453_person.jpg | 0 | - | 32.34 | continue |
| coco_000000214869_person.jpg | 0 | - | 31.21 | continue |
| coco_000000215072_person.jpg | 1 | 0.60 | 29.7 | emergency_stop |
| coco_000000216277_person.jpg | 1 | 0.56 | 33.25 | emergency_stop |
| coco_000000224807_person.jpg | 7 | 0.65 | 33.84 | emergency_stop |
| coco_000000227482_person.jpg | 1 | 0.88 | 30.43 | emergency_stop |
| coco_000000248616_person.jpg | 3 | 0.64 | 30.97 | emergency_stop |
| coco_000000250127_person.jpg | 1 | 0.85 | 29.95 | emergency_stop |
| coco_000000256775_person.jpg | 4 | 0.65 | 33.27 | continue |
| coco_000000272136_person.jpg | 0 | - | 30.3 | continue |
| coco_000000279541_person.jpg | 0 | - | 30.15 | continue |
| coco_000000289343_person.jpg | 1 | 0.48 | 31.7 | stop |
| coco_000000289415_person.jpg | 1 | 0.80 | 30.94 | stop |
| coco_000000292456_person.jpg | 0 | - | 30.12 | stop |
| coco_000000295478_person.jpg | 1 | 0.91 | 30.12 | emergency_stop |
| coco_000000303566_person.jpg | 4 | 0.63 | 41.75 | emergency_stop |
| coco_000000312192_person.jpg | 0 | - | 31.81 | emergency_stop |
| coco_000000313034_person.jpg | 2 | 0.68 | 32.41 | emergency_stop |
| coco_000000315187_person.jpg | 0 | - | 35.48 | emergency_stop |
| coco_000000317999_person.jpg | 0 | - | 31.17 | emergency_stop |
| coco_000000323355_person.jpg | 1 | 0.77 | 33.76 | emergency_stop |
| coco_000000327701_person.jpg | 3 | 0.78 | 31.6 | emergency_stop |
| coco_000000332351_person.jpg | 5 | 0.54 | 33.61 | emergency_stop |
| coco_000000336053_person.jpg | 2 | 0.63 | 31.12 | emergency_stop |
| coco_000000345361_person.jpg | 3 | 0.82 | 30.84 | emergency_stop |
| coco_000000347254_person.jpg | 3 | 0.79 | 31.33 | emergency_stop |
| coco_000000354307_person.jpg | 0 | - | 29.91 | continue |
| coco_000000354547_person.jpg | 1 | 0.84 | 30.31 | continue |
| coco_000000368212_person.jpg | 1 | 0.62 | 29.7 | continue |
| coco_000000372819_person.jpg | 2 | 0.74 | 31.33 | stop |
| coco_000000383337_person.jpg | 1 | 0.55 | 31.16 | stop |
| coco_000000385190_person.jpg | 0 | - | 33.44 | stop |
| coco_000000390246_person.jpg | 1 | 0.73 | 31.7 | stop |
| coco_000000391722_person.jpg | 2 | 0.68 | 33.43 | stop |
| coco_000000394275_person.jpg | 0 | - | 33.07 | stop |
| coco_000000398377_person.jpg | 3 | 0.75 | 30.67 | emergency_stop |
| coco_000000406129_person.jpg | 1 | 0.47 | 32.91 | emergency_stop |
| coco_000000414170_person.jpg | 3 | 0.76 | 29.89 | emergency_stop |
| coco_000000417632_person.jpg | 1 | 0.54 | 32.59 | emergency_stop |
| coco_000000427997_person.jpg | 1 | 0.69 | 30.11 | emergency_stop |
| coco_000000428111_person.jpg | 0 | - | 29.24 | emergency_stop |
| coco_000000434230_person.jpg | 0 | - | 30.08 | emergency_stop |
| coco_000000437351_person.jpg | 1 | 0.65 | 31.79 | emergency_stop |
| coco_000000441491_person.jpg | 0 | - | 29.52 | emergency_stop |
| coco_000000447465_person.jpg | 0 | - | 29.97 | emergency_stop |
| coco_000000459195_person.jpg | 3 | 0.71 | 32.18 | emergency_stop |
| coco_000000481480_person.jpg | 0 | - | 31.81 | emergency_stop |
| coco_000000490936_person.jpg | 1 | 0.76 | 32.19 | emergency_stop |
| coco_000000492758_person.jpg | 0 | - | 31.65 | emergency_stop |
| coco_000000497568_person.jpg | 0 | - | 32.47 | emergency_stop |
| coco_000000504389_person.jpg | 1 | 0.66 | 30.58 | emergency_stop |
| coco_000000512836_person.jpg | 0 | - | 33.4 | stop |
| coco_000000516173_person.jpg | 1 | 0.88 | 30.93 | stop |
| coco_000000527528_person.jpg | 0 | - | 29.84 | stop |
| coco_000000529939_person.jpg | 1 | 0.80 | 30.44 | emergency_stop |
| coco_000000548780_person.jpg | 3 | 0.63 | 30.04 | emergency_stop |
| coco_000000551215_person.jpg | 1 | 0.90 | 31.59 | emergency_stop |
| coco_000000553788_person.jpg | 1 | 0.64 | 31.11 | emergency_stop |
| coco_000000559543_person.jpg | 1 | 0.84 | 33.19 | emergency_stop |
| coco_000000561223_person.jpg | 1 | 0.91 | 32.86 | emergency_stop |
| coco_000000563604_person.jpg | 3 | 0.56 | 32.35 | continue |
| coco_000000563648_person.jpg | 0 | - | 31.35 | continue |
| coco_000000576955_person.jpg | 1 | 0.49 | 31.3 | continue |

## 5.7.2 Detectarea vehiculelor

*Autoturisme, autobuze, camioane, motociclete, biciclete*

Clase monitorizate: `bicycle, car, motorcycle, bus, truck`

### Mod CPU

| Metrică | Valoare |
|---------|---------|
| Imagini procesate | 100 |
| Imagini cu ≥1 detecție | 49 |
| Detecții scenariu (total) | 64 |
| Detecții medii / imagine | 0.64 |
| Confidence medie | 0.612 |
| Preprocesare medie | 0.33 ms |
| Inferență medie | 31.34 ms |
| Total mediu | 31.66 ms |
| FPS mediu | 31.58 |
| Decizii | {'continue': 24, 'stop': 57, 'emergency_stop': 16, 'slow_down': 3} |
| Niveluri pericol | {'HIGH': 10, 'LOW': 7, 'CRITICAL': 18, 'MEDIUM': 3} |

| Imagine | Det. scenariu | Confidence | Total (ms) | Decizie |
|---------|---------------|------------|------------|---------|
| coco_000000008899_bicycle.jpg | 0 | - | 31.03 | continue |
| coco_000000009891_car.jpg | 1 | 0.50 | 29.87 | continue |
| coco_000000013348_truck.jpg | 0 | - | 30.95 | continue |
| coco_000000026204_bus_car.jpg | 4 | 0.64 | 29.52 | stop |
| coco_000000026926_car.jpg | 0 | - | 33.49 | stop |
| coco_000000030828_car.jpg | 0 | - | 34.27 | stop |
| coco_000000032941_bus_car.jpg | 2 | 0.61 | 31.01 | emergency_stop |
| coco_000000033759_car_truck.jpg | 0 | - | 29.53 | emergency_stop |
| coco_000000033854_bus_car.jpg | 1 | 0.73 | 30.64 | emergency_stop |
| coco_000000069213_motorcycle.jpg | 0 | - | 30.62 | emergency_stop |
| coco_000000072852_bicycle.jpg | 0 | - | 31.11 | emergency_stop |
| coco_000000074256_bus.jpg | 0 | - | 33.45 | emergency_stop |
| coco_000000076417_car_truck.jpg | 0 | - | 31.01 | emergency_stop |
| coco_000000076547_bicycle.jpg | 1 | 0.62 | 30.91 | emergency_stop |
| coco_000000081394_car_motorcycle.jpg | 1 | 0.69 | 30.2 | emergency_stop |
| coco_000000085376_car_motorcycle.jpg | 2 | 0.56 | 30.21 | slow_down |
| coco_000000086483_car.jpg | 0 | - | 33.31 | slow_down |
| coco_000000095843_bus.jpg | 1 | 0.61 | 30.11 | slow_down |
| coco_000000100274_car_truck.jpg | 1 | 0.51 | 31.6 | continue |
| coco_000000102411_car_motorcycle.jpg | 1 | 0.55 | 33.76 | continue |
| coco_000000102805_car_truck.jpg | 1 | 0.49 | 30.37 | continue |
| coco_000000105923_car.jpg | 1 | 0.46 | 32.37 | continue |
| coco_000000111086_car.jpg | 0 | - | 30.28 | continue |
| coco_000000122166_bicycle_car.jpg | 1 | 0.53 | 31.42 | continue |
| coco_000000130386_bicycle_car.jpg | 0 | - | 31.51 | continue |
| coco_000000132375_bicycle.jpg | 0 | - | 30.97 | continue |
| coco_000000133819_bus.jpg | 1 | 0.63 | 30.07 | continue |
| coco_000000136715_car_motorcycle.jpg | 1 | 0.45 | 29.76 | continue |
| coco_000000143931_bus.jpg | 1 | 0.50 | 30.49 | continue |
| coco_000000146498_car.jpg | 0 | - | 31.45 | continue |
| coco_000000153011_bus_car.jpg | 1 | 0.50 | 30.68 | emergency_stop |
| coco_000000155341_car_truck.jpg | 2 | 0.62 | 29.91 | emergency_stop |
| coco_000000157928_car.jpg | 0 | - | 31.94 | emergency_stop |
| coco_000000158744_car.jpg | 1 | 0.71 | 32.18 | continue |
| coco_000000180878_car.jpg | 0 | - | 30.93 | continue |
| coco_000000190753_bicycle.jpg | 0 | - | 29.71 | continue |
| coco_000000192716_car.jpg | 1 | 0.50 | 31.03 | stop |
| coco_000000198489_car.jpg | 1 | 0.64 | 30.34 | stop |
| coco_000000204186_motorcycle.jpg | 1 | 0.61 | 34.29 | stop |
| coco_000000204871_bus_car.jpg | 1 | 0.64 | 32.93 | stop |
| coco_000000205647_truck.jpg | 1 | 0.91 | 30.36 | stop |
| coco_000000213605_bus_car.jpg | 2 | 0.75 | 32.99 | stop |
| coco_000000231508_car.jpg | 0 | - | 31.91 | stop |
| coco_000000235399_truck.jpg | 0 | - | 30.77 | stop |
| coco_000000245320_car.jpg | 0 | - | 29.9 | stop |
| coco_000000249219_bus.jpg | 1 | 0.73 | 30.5 | stop |
| coco_000000256941_bicycle.jpg | 0 | - | 32.3 | stop |
| coco_000000261888_bicycle.jpg | 0 | - | 29.99 | stop |
| coco_000000279714_car.jpg | 1 | 0.89 | 29.93 | stop |
| coco_000000297022_truck.jpg | 0 | - | 30.29 | stop |
| coco_000000297562_car.jpg | 0 | - | 30.68 | stop |
| coco_000000303305_bus_car.jpg | 2 | 0.70 | 33.1 | stop |
| coco_000000308531_car.jpg | 0 | - | 34.38 | stop |
| coco_000000312421_motorcycle.jpg | 0 | - | 30.92 | stop |
| coco_000000319534_bus.jpg | 0 | - | 31.38 | stop |
| coco_000000322864_car.jpg | 1 | 0.56 | 35.87 | stop |
| coco_000000326627_car.jpg | 2 | 0.59 | 31.25 | stop |
| coco_000000335177_car_truck.jpg | 1 | 0.65 | 37.17 | stop |
| coco_000000338219_motorcycle.jpg | 1 | 0.56 | 35.35 | stop |
| coco_000000338624_car.jpg | 0 | - | 31.42 | stop |
| coco_000000343561_bicycle.jpg | 1 | 0.58 | 30.97 | stop |
| coco_000000344888_car_truck.jpg | 0 | - | 32.34 | stop |
| coco_000000350003_bicycle_car.jpg | 2 | 0.62 | 32.16 | stop |
| coco_000000357737_bicycle_car.jpg | 2 | 0.60 | 32.75 | stop |
| coco_000000363188_car.jpg | 0 | - | 30.36 | stop |
| coco_000000365642_car.jpg | 3 | 0.52 | 39.18 | stop |
| coco_000000372317_bus.jpg | 1 | 0.79 | 33.16 | stop |
| coco_000000374545_bicycle.jpg | 0 | - | 31.35 | stop |
| coco_000000383289_car.jpg | 1 | 0.48 | 29.59 | stop |
| coco_000000408120_car.jpg | 0 | - | 31.07 | stop |
| coco_000000414133_car.jpg | 0 | - | 30.22 | stop |
| coco_000000417779_car.jpg | 0 | - | 31.85 | stop |
| coco_000000421455_car_truck.jpg | 0 | - | 32.71 | stop |
| coco_000000426166_bicycle.jpg | 1 | 0.49 | 32.27 | stop |
| coco_000000430073_motorcycle.jpg | 0 | - | 31.16 | stop |
| coco_000000439180_truck.jpg | 0 | - | 30.1 | stop |
| coco_000000439854_bicycle.jpg | 0 | - | 30.77 | stop |
| coco_000000446206_bus.jpg | 1 | 0.91 | 32.68 | stop |
| coco_000000449312_car.jpg | 0 | - | 33.15 | stop |
| coco_000000452321_bus.jpg | 2 | 0.73 | 33.07 | stop |
| coco_000000454798_bus_truck.jpg | 0 | - | 32.19 | stop |
| coco_000000454978_motorcycle.jpg | 1 | 0.60 | 30.47 | stop |
| coco_000000458702_car.jpg | 0 | - | 31.43 | stop |
| coco_000000462756_car_motorcycle.jpg | 1 | 0.58 | 31.71 | stop |
| coco_000000464824_car.jpg | 0 | - | 31.78 | stop |
| coco_000000465675_truck.jpg | 0 | - | 31.17 | stop |
| coco_000000468124_bus_car.jpg | 1 | 0.49 | 31.21 | stop |
| coco_000000468332_car.jpg | 0 | - | 32.62 | stop |
| coco_000000476119_car_truck.jpg | 1 | 0.48 | 31.21 | stop |
| coco_000000485237_car_truck.jpg | 0 | - | 29.85 | stop |
| coco_000000490936_bicycle_car.jpg | 0 | - | 38.99 | continue |
| coco_000000499622_motorcycle.jpg | 0 | - | 32.59 | continue |
| coco_000000523782_truck.jpg | 1 | 0.49 | 31.9 | continue |
| coco_000000555050_car.jpg | 1 | 0.90 | 30.69 | continue |
| coco_000000563702_truck.jpg | 1 | 0.53 | 31.74 | continue |
| coco_000000564336_car_truck.jpg | 0 | - | 30.24 | continue |
| coco_000000567640_car_truck.jpg | 0 | - | 29.79 | emergency_stop |
| coco_000000569030_car_truck.jpg | 0 | - | 32.24 | emergency_stop |
| coco_000000572956_motorcycle.jpg | 2 | 0.50 | 32.37 | emergency_stop |
| coco_000000574425_bus.jpg | 0 | - | 31.47 | emergency_stop |

### Mod CPU+FPGA

| Metrică | Valoare |
|---------|---------|
| Imagini procesate | 100 |
| Imagini cu ≥1 detecție | 49 |
| Detecții scenariu (total) | 64 |
| Detecții medii / imagine | 0.64 |
| Confidence medie | 0.612 |
| Preprocesare medie | 61.13 ms |
| Inferență medie | 31.64 ms |
| Total mediu | 92.77 ms |
| FPS mediu | 10.78 |
| Decizii | {'continue': 21, 'stop': 60, 'emergency_stop': 16, 'slow_down': 3} |
| Niveluri pericol | {'HIGH': 10, 'LOW': 7, 'CRITICAL': 18, 'MEDIUM': 3} |

| Imagine | Det. scenariu | Confidence | Total (ms) | Decizie |
|---------|---------------|------------|------------|---------|
| coco_000000008899_bicycle.jpg | 0 | - | 6148.11 | continue |
| coco_000000009891_car.jpg | 1 | 0.50 | 33.23 | continue |
| coco_000000013348_truck.jpg | 0 | - | 32.04 | continue |
| coco_000000026204_bus_car.jpg | 4 | 0.64 | 32.91 | stop |
| coco_000000026926_car.jpg | 0 | - | 32.71 | stop |
| coco_000000030828_car.jpg | 0 | - | 30.32 | stop |
| coco_000000032941_bus_car.jpg | 2 | 0.61 | 32.42 | emergency_stop |
| coco_000000033759_car_truck.jpg | 0 | - | 32.32 | emergency_stop |
| coco_000000033854_bus_car.jpg | 1 | 0.73 | 31.72 | emergency_stop |
| coco_000000069213_motorcycle.jpg | 0 | - | 31.28 | emergency_stop |
| coco_000000072852_bicycle.jpg | 0 | - | 31.43 | emergency_stop |
| coco_000000074256_bus.jpg | 0 | - | 33.56 | emergency_stop |
| coco_000000076417_car_truck.jpg | 0 | - | 31.13 | emergency_stop |
| coco_000000076547_bicycle.jpg | 1 | 0.62 | 33.6 | emergency_stop |
| coco_000000081394_car_motorcycle.jpg | 1 | 0.69 | 31.54 | emergency_stop |
| coco_000000085376_car_motorcycle.jpg | 2 | 0.56 | 32.84 | slow_down |
| coco_000000086483_car.jpg | 0 | - | 30.08 | slow_down |
| coco_000000095843_bus.jpg | 1 | 0.61 | 34.06 | slow_down |
| coco_000000100274_car_truck.jpg | 1 | 0.51 | 34.82 | continue |
| coco_000000102411_car_motorcycle.jpg | 1 | 0.55 | 33.93 | continue |
| coco_000000102805_car_truck.jpg | 1 | 0.49 | 31.25 | continue |
| coco_000000105923_car.jpg | 1 | 0.46 | 31.02 | continue |
| coco_000000111086_car.jpg | 0 | - | 32.63 | continue |
| coco_000000122166_bicycle_car.jpg | 1 | 0.53 | 32.46 | continue |
| coco_000000130386_bicycle_car.jpg | 0 | - | 31.06 | continue |
| coco_000000132375_bicycle.jpg | 0 | - | 34.81 | continue |
| coco_000000133819_bus.jpg | 1 | 0.63 | 32.64 | continue |
| coco_000000136715_car_motorcycle.jpg | 1 | 0.45 | 30.34 | continue |
| coco_000000143931_bus.jpg | 1 | 0.50 | 30.06 | continue |
| coco_000000146498_car.jpg | 0 | - | 32.97 | continue |
| coco_000000153011_bus_car.jpg | 1 | 0.50 | 31.12 | emergency_stop |
| coco_000000155341_car_truck.jpg | 2 | 0.62 | 31.51 | emergency_stop |
| coco_000000157928_car.jpg | 0 | - | 30.73 | emergency_stop |
| coco_000000158744_car.jpg | 1 | 0.71 | 32.21 | continue |
| coco_000000180878_car.jpg | 0 | - | 33.02 | continue |
| coco_000000190753_bicycle.jpg | 0 | - | 32.33 | continue |
| coco_000000192716_car.jpg | 1 | 0.50 | 30.85 | stop |
| coco_000000198489_car.jpg | 1 | 0.64 | 30.95 | stop |
| coco_000000204186_motorcycle.jpg | 1 | 0.61 | 31.94 | stop |
| coco_000000204871_bus_car.jpg | 1 | 0.64 | 29.98 | stop |
| coco_000000205647_truck.jpg | 1 | 0.91 | 31.05 | stop |
| coco_000000213605_bus_car.jpg | 2 | 0.75 | 32.12 | stop |
| coco_000000231508_car.jpg | 0 | - | 32.22 | stop |
| coco_000000235399_truck.jpg | 0 | - | 30.1 | stop |
| coco_000000245320_car.jpg | 0 | - | 30.58 | stop |
| coco_000000249219_bus.jpg | 1 | 0.73 | 31.05 | stop |
| coco_000000256941_bicycle.jpg | 0 | - | 30.6 | stop |
| coco_000000261888_bicycle.jpg | 0 | - | 31.01 | stop |
| coco_000000279714_car.jpg | 1 | 0.89 | 30.62 | stop |
| coco_000000297022_truck.jpg | 0 | - | 32.6 | stop |
| coco_000000297562_car.jpg | 0 | - | 30.59 | stop |
| coco_000000303305_bus_car.jpg | 2 | 0.70 | 30.35 | stop |
| coco_000000308531_car.jpg | 0 | - | 30.28 | stop |
| coco_000000312421_motorcycle.jpg | 0 | - | 32.03 | stop |
| coco_000000319534_bus.jpg | 0 | - | 33.12 | stop |
| coco_000000322864_car.jpg | 1 | 0.56 | 31.5 | stop |
| coco_000000326627_car.jpg | 2 | 0.59 | 30.18 | stop |
| coco_000000335177_car_truck.jpg | 1 | 0.65 | 29.5 | stop |
| coco_000000338219_motorcycle.jpg | 1 | 0.56 | 30.12 | stop |
| coco_000000338624_car.jpg | 0 | - | 31.64 | stop |
| coco_000000343561_bicycle.jpg | 1 | 0.58 | 32.24 | stop |
| coco_000000344888_car_truck.jpg | 0 | - | 32.58 | stop |
| coco_000000350003_bicycle_car.jpg | 2 | 0.62 | 30.13 | stop |
| coco_000000357737_bicycle_car.jpg | 2 | 0.60 | 30.47 | stop |
| coco_000000363188_car.jpg | 0 | - | 33.1 | stop |
| coco_000000365642_car.jpg | 3 | 0.52 | 31.93 | stop |
| coco_000000372317_bus.jpg | 1 | 0.79 | 31.6 | stop |
| coco_000000374545_bicycle.jpg | 0 | - | 33.91 | stop |
| coco_000000383289_car.jpg | 1 | 0.48 | 30.68 | stop |
| coco_000000408120_car.jpg | 0 | - | 32.57 | stop |
| coco_000000414133_car.jpg | 0 | - | 30.45 | stop |
| coco_000000417779_car.jpg | 0 | - | 31.05 | stop |
| coco_000000421455_car_truck.jpg | 0 | - | 33.77 | stop |
| coco_000000426166_bicycle.jpg | 1 | 0.49 | 30.34 | stop |
| coco_000000430073_motorcycle.jpg | 0 | - | 30.39 | stop |
| coco_000000439180_truck.jpg | 0 | - | 29.76 | stop |
| coco_000000439854_bicycle.jpg | 0 | - | 29.66 | stop |
| coco_000000446206_bus.jpg | 1 | 0.91 | 30.79 | stop |
| coco_000000449312_car.jpg | 0 | - | 29.93 | stop |
| coco_000000452321_bus.jpg | 2 | 0.73 | 31.19 | stop |
| coco_000000454798_bus_truck.jpg | 0 | - | 31.63 | stop |
| coco_000000454978_motorcycle.jpg | 1 | 0.60 | 31.02 | stop |
| coco_000000458702_car.jpg | 0 | - | 31.73 | stop |
| coco_000000462756_car_motorcycle.jpg | 1 | 0.58 | 32.81 | stop |
| coco_000000464824_car.jpg | 0 | - | 31.74 | stop |
| coco_000000465675_truck.jpg | 0 | - | 31.21 | stop |
| coco_000000468124_bus_car.jpg | 1 | 0.49 | 32.81 | stop |
| coco_000000468332_car.jpg | 0 | - | 33.39 | stop |
| coco_000000476119_car_truck.jpg | 1 | 0.48 | 33.61 | stop |
| coco_000000485237_car_truck.jpg | 0 | - | 30.87 | stop |
| coco_000000490936_bicycle_car.jpg | 0 | - | 31.6 | stop |
| coco_000000499622_motorcycle.jpg | 0 | - | 31.22 | stop |
| coco_000000523782_truck.jpg | 1 | 0.49 | 30.75 | stop |
| coco_000000555050_car.jpg | 1 | 0.90 | 30.55 | continue |
| coco_000000563702_truck.jpg | 1 | 0.53 | 33.21 | continue |
| coco_000000564336_car_truck.jpg | 0 | - | 30.85 | continue |
| coco_000000567640_car_truck.jpg | 0 | - | 30.3 | emergency_stop |
| coco_000000569030_car_truck.jpg | 0 | - | 29.87 | emergency_stop |
| coco_000000572956_motorcycle.jpg | 2 | 0.50 | 31.07 | emergency_stop |
| coco_000000574425_bus.jpg | 0 | - | 31.34 | emergency_stop |

## 5.7.3 Detectarea animalelor

*Câini și pisici ca obstacole mobile*

Clase monitorizate: `dog, cat`

### Mod CPU

| Metrică | Valoare |
|---------|---------|
| Imagini procesate | 100 |
| Imagini cu ≥1 detecție | 18 |
| Detecții scenariu (total) | 20 |
| Detecții medii / imagine | 0.2 |
| Confidence medie | 0.686 |
| Preprocesare medie | 0.33 ms |
| Inferență medie | 30.94 ms |
| Total mediu | 31.27 ms |
| FPS mediu | 31.98 |
| Decizii | {'continue': 67, 'emergency_stop': 27, 'stop': 6} |
| Niveluri pericol | {'CRITICAL': 16} |

| Imagine | Det. scenariu | Confidence | Total (ms) | Decizie |
|---------|---------------|------------|------------|---------|
| coco_000000001675_cat.jpg | 0 | - | 38.68 | continue |
| coco_000000007386_dog.jpg | 0 | - | 34.44 | continue |
| coco_000000010363_cat.jpg | 0 | - | 32.09 | continue |
| coco_000000018833_cat.jpg | 0 | - | 33.97 | continue |
| coco_000000022192_dog.jpg | 0 | - | 31.35 | continue |
| coco_000000022892_cat_dog.jpg | 0 | - | 30.81 | continue |
| coco_000000047121_cat.jpg | 1 | 0.73 | 31.84 | emergency_stop |
| coco_000000049269_dog.jpg | 0 | - | 31.29 | emergency_stop |
| coco_000000049810_cat.jpg | 0 | - | 29.82 | emergency_stop |
| coco_000000052891_dog.jpg | 0 | - | 31.61 | continue |
| coco_000000058111_cat.jpg | 0 | - | 32.57 | continue |
| coco_000000060835_dog.jpg | 0 | - | 30.71 | continue |
| coco_000000063552_cat.jpg | 0 | - | 33.08 | emergency_stop |
| coco_000000076417_dog.jpg | 0 | - | 33.37 | emergency_stop |
| coco_000000077595_cat.jpg | 0 | - | 31.39 | emergency_stop |
| coco_000000078565_dog.jpg | 0 | - | 31.57 | continue |
| coco_000000084362_cat.jpg | 0 | - | 29.8 | continue |
| coco_000000084650_cat.jpg | 0 | - | 31.35 | continue |
| coco_000000088951_dog.jpg | 0 | - | 34.47 | continue |
| coco_000000089880_dog.jpg | 0 | - | 31.58 | continue |
| coco_000000115885_cat.jpg | 0 | - | 31.64 | continue |
| coco_000000117908_cat.jpg | 1 | 0.49 | 31.44 | continue |
| coco_000000119233_cat.jpg | 2 | 0.65 | 31.29 | continue |
| coco_000000119828_cat.jpg | 1 | 0.55 | 30.45 | continue |
| coco_000000129756_dog.jpg | 0 | - | 30.87 | emergency_stop |
| coco_000000139684_cat.jpg | 0 | - | 30.8 | emergency_stop |
| coco_000000139872_dog.jpg | 1 | 0.80 | 31.91 | emergency_stop |
| coco_000000140203_dog.jpg | 0 | - | 31.07 | emergency_stop |
| coco_000000149568_dog.jpg | 0 | - | 31.5 | emergency_stop |
| coco_000000155291_cat.jpg | 0 | - | 31.64 | emergency_stop |
| coco_000000159458_dog.jpg | 0 | - | 31.01 | continue |
| coco_000000166277_cat.jpg | 0 | - | 30.35 | continue |
| coco_000000169076_cat_dog.jpg | 0 | - | 30.45 | continue |
| coco_000000172330_cat.jpg | 0 | - | 32.04 | stop |
| coco_000000177015_cat.jpg | 0 | - | 30.08 | stop |
| coco_000000185250_dog.jpg | 1 | 0.93 | 29.94 | stop |
| coco_000000189806_cat_dog.jpg | 1 | 0.59 | 30.08 | emergency_stop |
| coco_000000190140_dog.jpg | 0 | - | 34.82 | emergency_stop |
| coco_000000193162_dog.jpg | 0 | - | 31.0 | emergency_stop |
| coco_000000193674_dog.jpg | 0 | - | 31.36 | emergency_stop |
| coco_000000198641_cat.jpg | 1 | 0.53 | 30.4 | emergency_stop |
| coco_000000205834_dog.jpg | 0 | - | 32.76 | emergency_stop |
| coco_000000206831_dog.jpg | 0 | - | 29.26 | continue |
| coco_000000211042_cat.jpg | 0 | - | 32.68 | continue |
| coco_000000222235_cat.jpg | 0 | - | 30.25 | continue |
| coco_000000225670_dog.jpg | 0 | - | 31.17 | continue |
| coco_000000236166_dog.jpg | 0 | - | 34.83 | continue |
| coco_000000240940_cat.jpg | 0 | - | 31.26 | continue |
| coco_000000241326_cat_dog.jpg | 2 | 0.71 | 32.68 | emergency_stop |
| coco_000000243344_cat.jpg | 0 | - | 31.57 | emergency_stop |
| coco_000000245576_cat.jpg | 0 | - | 31.32 | emergency_stop |
| coco_000000253386_dog.jpg | 0 | - | 30.92 | continue |
| coco_000000255965_cat.jpg | 0 | - | 32.79 | continue |
| coco_000000260925_cat.jpg | 0 | - | 30.12 | continue |
| coco_000000267300_dog.jpg | 0 | - | 31.65 | continue |
| coco_000000273642_dog.jpg | 0 | - | 30.36 | continue |
| coco_000000277584_cat.jpg | 0 | - | 35.52 | continue |
| coco_000000279145_cat.jpg | 0 | - | 33.27 | continue |
| coco_000000279278_dog.jpg | 1 | 0.82 | 30.67 | continue |
| coco_000000291664_dog.jpg | 0 | - | 33.03 | continue |
| coco_000000297085_cat.jpg | 0 | - | 31.24 | continue |
| coco_000000309484_dog.jpg | 0 | - | 29.69 | continue |
| coco_000000309938_dog.jpg | 0 | - | 32.45 | continue |
| coco_000000327769_cat.jpg | 0 | - | 29.7 | continue |
| coco_000000329447_dog.jpg | 0 | - | 34.33 | continue |
| coco_000000347930_dog.jpg | 1 | 0.72 | 35.77 | continue |
| coco_000000361621_cat.jpg | 0 | - | 29.53 | continue |
| coco_000000364636_dog.jpg | 0 | - | 30.69 | continue |
| coco_000000366611_dog.jpg | 1 | 0.59 | 29.48 | continue |
| coco_000000367195_dog.jpg | 0 | - | 29.9 | continue |
| coco_000000375278_cat_dog.jpg | 0 | - | 31.3 | continue |
| coco_000000387383_cat.jpg | 0 | - | 30.25 | continue |
| coco_000000399560_cat.jpg | 0 | - | 29.46 | continue |
| coco_000000399655_dog.jpg | 1 | 0.49 | 31.28 | continue |
| coco_000000401991_cat_dog.jpg | 0 | - | 29.94 | continue |
| coco_000000415990_dog.jpg | 0 | - | 30.5 | emergency_stop |
| coco_000000416256_cat.jpg | 0 | - | 30.23 | emergency_stop |
| coco_000000433134_cat.jpg | 1 | 0.52 | 30.43 | emergency_stop |
| coco_000000434996_cat.jpg | 0 | - | 28.62 | continue |
| coco_000000435299_cat.jpg | 0 | - | 30.24 | continue |
| coco_000000452891_dog.jpg | 0 | - | 29.55 | continue |
| coco_000000462728_dog.jpg | 0 | - | 29.23 | continue |
| coco_000000472375_dog.jpg | 0 | - | 29.93 | continue |
| coco_000000475732_cat.jpg | 1 | 0.73 | 29.57 | continue |
| coco_000000476810_cat.jpg | 1 | 0.79 | 30.29 | emergency_stop |
| coco_000000479155_dog.jpg | 0 | - | 29.69 | emergency_stop |
| coco_000000486479_dog.jpg | 1 | 0.81 | 28.97 | emergency_stop |
| coco_000000489014_dog.jpg | 0 | - | 29.44 | stop |
| coco_000000490171_dog.jpg | 0 | - | 28.77 | stop |
| coco_000000491216_cat.jpg | 0 | - | 29.4 | stop |
| coco_000000498286_dog.jpg | 0 | - | 30.48 | continue |
| coco_000000520531_cat.jpg | 0 | - | 30.29 | continue |
| coco_000000524280_cat.jpg | 0 | - | 30.08 | continue |
| coco_000000530099_cat.jpg | 0 | - | 31.91 | continue |
| coco_000000532530_dog.jpg | 0 | - | 31.16 | continue |
| coco_000000554579_dog.jpg | 1 | 0.88 | 32.86 | continue |
| coco_000000555005_dog.jpg | 0 | - | 32.57 | continue |
| coco_000000562561_dog.jpg | 0 | - | 32.21 | continue |
| coco_000000574315_cat.jpg | 0 | - | 29.62 | continue |
| coco_000000579321_dog.jpg | 0 | - | 29.84 | continue |

### Mod CPU+FPGA

| Metrică | Valoare |
|---------|---------|
| Imagini procesate | 100 |
| Imagini cu ≥1 detecție | 18 |
| Detecții scenariu (total) | 20 |
| Detecții medii / imagine | 0.2 |
| Confidence medie | 0.686 |
| Preprocesare medie | 61.13 ms |
| Inferență medie | 30.47 ms |
| Total mediu | 91.6 ms |
| FPS mediu | 10.92 |
| Decizii | {'continue': 52, 'emergency_stop': 42, 'slow_down': 3, 'stop': 3} |
| Niveluri pericol | {'CRITICAL': 16} |

| Imagine | Det. scenariu | Confidence | Total (ms) | Decizie |
|---------|---------------|------------|------------|---------|
| coco_000000001675_cat.jpg | 0 | - | 6125.45 | continue |
| coco_000000007386_dog.jpg | 0 | - | 36.15 | continue |
| coco_000000010363_cat.jpg | 0 | - | 33.37 | continue |
| coco_000000018833_cat.jpg | 0 | - | 32.58 | continue |
| coco_000000022192_dog.jpg | 0 | - | 31.52 | continue |
| coco_000000022892_cat_dog.jpg | 0 | - | 31.62 | continue |
| coco_000000047121_cat.jpg | 1 | 0.73 | 31.42 | emergency_stop |
| coco_000000049269_dog.jpg | 0 | - | 30.8 | emergency_stop |
| coco_000000049810_cat.jpg | 0 | - | 30.02 | emergency_stop |
| coco_000000052891_dog.jpg | 0 | - | 30.73 | continue |
| coco_000000058111_cat.jpg | 0 | - | 30.24 | continue |
| coco_000000060835_dog.jpg | 0 | - | 38.36 | continue |
| coco_000000063552_cat.jpg | 0 | - | 31.79 | emergency_stop |
| coco_000000076417_dog.jpg | 0 | - | 31.72 | emergency_stop |
| coco_000000077595_cat.jpg | 0 | - | 31.93 | emergency_stop |
| coco_000000078565_dog.jpg | 0 | - | 30.42 | continue |
| coco_000000084362_cat.jpg | 0 | - | 30.82 | continue |
| coco_000000084650_cat.jpg | 0 | - | 30.2 | continue |
| coco_000000088951_dog.jpg | 0 | - | 30.64 | continue |
| coco_000000089880_dog.jpg | 0 | - | 30.33 | continue |
| coco_000000115885_cat.jpg | 0 | - | 30.4 | continue |
| coco_000000117908_cat.jpg | 1 | 0.49 | 30.0 | continue |
| coco_000000119233_cat.jpg | 2 | 0.65 | 29.5 | emergency_stop |
| coco_000000119828_cat.jpg | 1 | 0.55 | 29.63 | emergency_stop |
| coco_000000129756_dog.jpg | 0 | - | 30.67 | emergency_stop |
| coco_000000139684_cat.jpg | 0 | - | 30.08 | slow_down |
| coco_000000139872_dog.jpg | 1 | 0.80 | 35.96 | slow_down |
| coco_000000140203_dog.jpg | 0 | - | 30.36 | slow_down |
| coco_000000149568_dog.jpg | 0 | - | 29.73 | emergency_stop |
| coco_000000155291_cat.jpg | 0 | - | 30.44 | emergency_stop |
| coco_000000159458_dog.jpg | 0 | - | 30.12 | emergency_stop |
| coco_000000166277_cat.jpg | 0 | - | 29.94 | continue |
| coco_000000169076_cat_dog.jpg | 0 | - | 30.04 | continue |
| coco_000000172330_cat.jpg | 0 | - | 32.98 | continue |
| coco_000000177015_cat.jpg | 0 | - | 30.17 | emergency_stop |
| coco_000000185250_dog.jpg | 1 | 0.93 | 30.39 | emergency_stop |
| coco_000000189806_cat_dog.jpg | 1 | 0.59 | 30.34 | emergency_stop |
| coco_000000190140_dog.jpg | 0 | - | 30.56 | emergency_stop |
| coco_000000193162_dog.jpg | 0 | - | 29.5 | emergency_stop |
| coco_000000193674_dog.jpg | 0 | - | 29.95 | emergency_stop |
| coco_000000198641_cat.jpg | 1 | 0.53 | 33.17 | emergency_stop |
| coco_000000205834_dog.jpg | 0 | - | 30.5 | emergency_stop |
| coco_000000206831_dog.jpg | 0 | - | 34.34 | emergency_stop |
| coco_000000211042_cat.jpg | 0 | - | 30.41 | continue |
| coco_000000222235_cat.jpg | 0 | - | 31.97 | continue |
| coco_000000225670_dog.jpg | 0 | - | 30.07 | continue |
| coco_000000236166_dog.jpg | 0 | - | 28.73 | continue |
| coco_000000240940_cat.jpg | 0 | - | 29.68 | continue |
| coco_000000241326_cat_dog.jpg | 2 | 0.71 | 29.65 | continue |
| coco_000000243344_cat.jpg | 0 | - | 29.94 | stop |
| coco_000000245576_cat.jpg | 0 | - | 28.74 | stop |
| coco_000000253386_dog.jpg | 0 | - | 29.54 | stop |
| coco_000000255965_cat.jpg | 0 | - | 30.24 | continue |
| coco_000000260925_cat.jpg | 0 | - | 30.23 | continue |
| coco_000000267300_dog.jpg | 0 | - | 30.35 | continue |
| coco_000000273642_dog.jpg | 0 | - | 30.37 | emergency_stop |
| coco_000000277584_cat.jpg | 0 | - | 30.01 | emergency_stop |
| coco_000000279145_cat.jpg | 0 | - | 30.48 | emergency_stop |
| coco_000000279278_dog.jpg | 1 | 0.82 | 31.08 | emergency_stop |
| coco_000000291664_dog.jpg | 0 | - | 30.62 | emergency_stop |
| coco_000000297085_cat.jpg | 0 | - | 30.26 | emergency_stop |
| coco_000000309484_dog.jpg | 0 | - | 29.89 | continue |
| coco_000000309938_dog.jpg | 0 | - | 29.65 | continue |
| coco_000000327769_cat.jpg | 0 | - | 29.95 | continue |
| coco_000000329447_dog.jpg | 0 | - | 30.14 | emergency_stop |
| coco_000000347930_dog.jpg | 1 | 0.72 | 29.91 | emergency_stop |
| coco_000000361621_cat.jpg | 0 | - | 29.98 | emergency_stop |
| coco_000000364636_dog.jpg | 0 | - | 29.72 | continue |
| coco_000000366611_dog.jpg | 1 | 0.59 | 30.02 | continue |
| coco_000000367195_dog.jpg | 0 | - | 30.0 | continue |
| coco_000000375278_cat_dog.jpg | 0 | - | 29.68 | continue |
| coco_000000387383_cat.jpg | 0 | - | 30.24 | continue |
| coco_000000399560_cat.jpg | 0 | - | 29.66 | continue |
| coco_000000399655_dog.jpg | 1 | 0.49 | 30.78 | emergency_stop |
| coco_000000401991_cat_dog.jpg | 0 | - | 29.77 | emergency_stop |
| coco_000000415990_dog.jpg | 0 | - | 30.48 | emergency_stop |
| coco_000000416256_cat.jpg | 0 | - | 30.11 | continue |
| coco_000000433134_cat.jpg | 1 | 0.52 | 30.89 | continue |
| coco_000000434996_cat.jpg | 0 | - | 30.55 | continue |
| coco_000000435299_cat.jpg | 0 | - | 30.53 | emergency_stop |
| coco_000000452891_dog.jpg | 0 | - | 29.38 | emergency_stop |
| coco_000000462728_dog.jpg | 0 | - | 31.06 | emergency_stop |
| coco_000000472375_dog.jpg | 0 | - | 30.36 | continue |
| coco_000000475732_cat.jpg | 1 | 0.73 | 30.66 | continue |
| coco_000000476810_cat.jpg | 1 | 0.79 | 30.2 | continue |
| coco_000000479155_dog.jpg | 0 | - | 30.61 | emergency_stop |
| coco_000000486479_dog.jpg | 1 | 0.81 | 30.03 | emergency_stop |
| coco_000000489014_dog.jpg | 0 | - | 31.28 | emergency_stop |
| coco_000000490171_dog.jpg | 0 | - | 29.94 | continue |
| coco_000000491216_cat.jpg | 0 | - | 30.35 | continue |
| coco_000000498286_dog.jpg | 0 | - | 30.48 | continue |
| coco_000000520531_cat.jpg | 0 | - | 30.48 | continue |
| coco_000000524280_cat.jpg | 0 | - | 29.93 | continue |
| coco_000000530099_cat.jpg | 0 | - | 29.58 | continue |
| coco_000000532530_dog.jpg | 0 | - | 29.71 | continue |
| coco_000000554579_dog.jpg | 1 | 0.88 | 31.28 | continue |
| coco_000000555005_dog.jpg | 0 | - | 30.38 | continue |
| coco_000000562561_dog.jpg | 0 | - | 30.41 | emergency_stop |
| coco_000000574315_cat.jpg | 0 | - | 30.57 | emergency_stop |
| coco_000000579321_dog.jpg | 0 | - | 30.38 | emergency_stop |

## 5.7.4 Detectarea semnelor de circulație

*Semne STOP și semafoare*

Clase monitorizate: `stop sign, traffic light`

### Mod CPU

| Metrică | Valoare |
|---------|---------|
| Imagini procesate | 100 |
| Imagini cu ≥1 detecție | 42 |
| Detecții scenariu (total) | 56 |
| Detecții medii / imagine | 0.56 |
| Confidence medie | 0.747 |
| Preprocesare medie | 0.31 ms |
| Inferență medie | 29.78 ms |
| Total mediu | 30.1 ms |
| FPS mediu | 33.23 |
| Decizii | {'stop': 88, 'continue': 6, 'emergency_stop': 6} |
| Niveluri pericol | {'MEDIUM': 8, 'LOW': 11, 'CRITICAL': 9, 'HIGH': 5} |

| Imagine | Det. scenariu | Confidence | Total (ms) | Decizie |
|---------|---------------|------------|------------|---------|
| coco_000000000724_stop-sign.jpg | 1 | 0.95 | 31.45 | stop |
| coco_000000011122_stop-sign.jpg | 1 | 0.97 | 29.49 | stop |
| coco_000000015440_stop-sign.jpg | 1 | 0.75 | 30.0 | stop |
| coco_000000021839_traffic-light.jpg | 1 | 0.66 | 29.68 | stop |
| coco_000000071877_traffic-light.jpg | 0 | - | 29.0 | stop |
| coco_000000076547_traffic-light.jpg | 0 | - | 29.83 | stop |
| coco_000000079408_stop-sign.jpg | 1 | 0.96 | 29.67 | stop |
| coco_000000088462_stop-sign.jpg | 0 | - | 30.51 | stop |
| coco_000000095899_stop-sign.jpg | 1 | 0.95 | 29.75 | stop |
| coco_000000100283_stop-sign.jpg | 1 | 0.92 | 29.66 | stop |
| coco_000000100723_stop-sign.jpg | 0 | - | 29.94 | stop |
| coco_000000104782_stop-sign.jpg | 0 | - | 29.9 | stop |
| coco_000000119516_traffic-light.jpg | 0 | - | 30.36 | stop |
| coco_000000122166_traffic-light.jpg | 0 | - | 29.92 | stop |
| coco_000000122745_stop-sign.jpg | 1 | 0.85 | 30.71 | stop |
| coco_000000126592_stop-sign.jpg | 1 | 0.95 | 29.51 | stop |
| coco_000000127092_stop-sign.jpg | 0 | - | 30.22 | stop |
| coco_000000144706_traffic-light.jpg | 0 | - | 29.03 | stop |
| coco_000000153568_stop-sign.jpg | 0 | - | 28.91 | stop |
| coco_000000165039_traffic-light.jpg | 0 | - | 28.86 | stop |
| coco_000000169996_traffic-light.jpg | 1 | 0.49 | 29.85 | stop |
| coco_000000172856_stop-sign.jpg | 1 | 0.92 | 29.72 | stop |
| coco_000000174482_traffic-light.jpg | 0 | - | 30.13 | stop |
| coco_000000176037_traffic-light.jpg | 0 | - | 30.32 | stop |
| coco_000000183246_traffic-light.jpg | 0 | - | 30.2 | stop |
| coco_000000184324_stop-sign.jpg | 0 | - | 30.47 | stop |
| coco_000000190923_traffic-light.jpg | 1 | 0.45 | 28.92 | stop |
| coco_000000191471_stop-sign.jpg | 1 | 0.90 | 29.85 | stop |
| coco_000000192716_stop-sign.jpg | 1 | 0.94 | 29.23 | stop |
| coco_000000193717_traffic-light.jpg | 1 | 0.53 | 29.11 | stop |
| coco_000000201148_traffic-light.jpg | 0 | - | 29.49 | stop |
| coco_000000212072_stop-sign.jpg | 1 | 0.95 | 30.17 | stop |
| coco_000000213255_traffic-light.jpg | 0 | - | 30.89 | stop |
| coco_000000214200_stop-sign.jpg | 1 | 0.95 | 29.76 | stop |
| coco_000000221754_traffic-light.jpg | 2 | 0.54 | 29.87 | stop |
| coco_000000226417_traffic-light.jpg | 2 | 0.62 | 29.75 | stop |
| coco_000000228942_traffic-light.jpg | 1 | 0.48 | 28.85 | stop |
| coco_000000230450_traffic-light.jpg | 0 | - | 31.09 | stop |
| coco_000000232646_stop-sign.jpg | 1 | 0.93 | 30.94 | stop |
| coco_000000244379_traffic-light.jpg | 2 | 0.82 | 30.06 | stop |
| coco_000000252332_stop-sign.jpg | 1 | 0.94 | 29.59 | stop |
| coco_000000255917_traffic-light.jpg | 0 | - | 29.23 | stop |
| coco_000000260266_traffic-light.jpg | 2 | 0.67 | 30.16 | stop |
| coco_000000261888_stop-sign.jpg | 0 | - | 30.3 | stop |
| coco_000000273617_stop-sign.jpg | 1 | 0.68 | 30.35 | stop |
| coco_000000274272_traffic-light.jpg | 0 | - | 30.58 | stop |
| coco_000000281179_traffic-light.jpg | 0 | - | 31.23 | stop |
| coco_000000283037_traffic-light.jpg | 0 | - | 29.97 | stop |
| coco_000000283038_stop-sign_traffic-light.jpg | 1 | 0.91 | 29.93 | stop |
| coco_000000284762_traffic-light.jpg | 0 | - | 28.79 | stop |
| coco_000000289222_traffic-light.jpg | 2 | 0.83 | 29.96 | stop |
| coco_000000297343_stop-sign.jpg | 1 | 0.79 | 30.48 | stop |
| coco_000000309173_stop-sign.jpg | 1 | 0.91 | 30.6 | stop |
| coco_000000311883_traffic-light.jpg | 2 | 0.54 | 30.54 | stop |
| coco_000000315187_traffic-light.jpg | 0 | - | 30.35 | stop |
| coco_000000323751_traffic-light.jpg | 0 | - | 30.29 | stop |
| coco_000000326627_traffic-light.jpg | 0 | - | 36.95 | stop |
| coco_000000333697_stop-sign.jpg | 0 | - | 29.98 | stop |
| coco_000000336587_stop-sign.jpg | 2 | 0.84 | 30.51 | continue |
| coco_000000343496_stop-sign.jpg | 1 | 0.84 | 30.05 | continue |
| coco_000000347163_stop-sign.jpg | 2 | 0.71 | 29.91 | continue |
| coco_000000361506_stop-sign.jpg | 0 | - | 29.11 | continue |
| coco_000000369442_stop-sign.jpg | 0 | - | 30.25 | continue |
| coco_000000369751_stop-sign.jpg | 1 | 0.63 | 31.15 | continue |
| coco_000000375493_stop-sign.jpg | 0 | - | 30.33 | emergency_stop |
| coco_000000377946_traffic-light.jpg | 2 | 0.58 | 29.39 | emergency_stop |
| coco_000000379800_stop-sign.jpg | 0 | - | 32.4 | emergency_stop |
| coco_000000380706_traffic-light.jpg | 0 | - | 29.34 | emergency_stop |
| coco_000000381971_stop-sign.jpg | 0 | - | 29.29 | emergency_stop |
| coco_000000413689_stop-sign_traffic-light.jpg | 0 | - | 30.28 | emergency_stop |
| coco_000000414133_stop-sign.jpg | 1 | 0.80 | 30.48 | stop |
| coco_000000417779_stop-sign.jpg | 0 | - | 30.22 | stop |
| coco_000000418696_traffic-light.jpg | 0 | - | 30.35 | stop |
| coco_000000423229_traffic-light.jpg | 0 | - | 29.52 | stop |
| coco_000000424975_stop-sign.jpg | 0 | - | 30.09 | stop |
| coco_000000427055_stop-sign.jpg | 0 | - | 29.91 | stop |
| coco_000000438017_traffic-light.jpg | 0 | - | 29.83 | stop |
| coco_000000441553_traffic-light.jpg | 0 | - | 28.99 | stop |
| coco_000000449198_stop-sign_traffic-light.jpg | 0 | - | 28.81 | stop |
| coco_000000454661_traffic-light.jpg | 3 | 0.51 | 30.18 | stop |
| coco_000000475484_traffic-light.jpg | 0 | - | 30.34 | stop |
| coco_000000479030_traffic-light.jpg | 0 | - | 30.23 | stop |
| coco_000000480944_stop-sign_traffic-light.jpg | 2 | 0.67 | 31.31 | stop |
| coco_000000484029_stop-sign.jpg | 1 | 0.96 | 30.73 | stop |
| coco_000000491213_traffic-light.jpg | 0 | - | 30.06 | stop |
| coco_000000491470_traffic-light.jpg | 0 | - | 30.35 | stop |
| coco_000000496854_traffic-light.jpg | 0 | - | 30.06 | stop |
| coco_000000499181_stop-sign_traffic-light.jpg | 0 | - | 29.79 | stop |
| coco_000000501023_stop-sign_traffic-light.jpg | 3 | 0.66 | 30.53 | stop |
| coco_000000522940_stop-sign.jpg | 1 | 0.91 | 29.21 | stop |
| coco_000000523194_stop-sign.jpg | 0 | - | 30.43 | stop |
| coco_000000528980_stop-sign.jpg | 0 | - | 30.53 | stop |
| coco_000000538458_traffic-light.jpg | 0 | - | 29.88 | stop |
| coco_000000558558_traffic-light.jpg | 0 | - | 30.07 | stop |
| coco_000000565778_traffic-light.jpg | 0 | - | 30.1 | stop |
| coco_000000569030_traffic-light.jpg | 0 | - | 29.87 | stop |
| coco_000000571008_stop-sign.jpg | 1 | 0.85 | 31.22 | stop |
| coco_000000571943_traffic-light.jpg | 0 | - | 30.41 | stop |
| coco_000000572555_traffic-light.jpg | 0 | - | 30.19 | stop |
| coco_000000580418_stop-sign.jpg | 0 | - | 29.69 | stop |

### Mod CPU+FPGA

| Metrică | Valoare |
|---------|---------|
| Imagini procesate | 100 |
| Imagini cu ≥1 detecție | 42 |
| Detecții scenariu (total) | 56 |
| Detecții medii / imagine | 0.56 |
| Confidence medie | 0.747 |
| Preprocesare medie | 61.11 ms |
| Inferență medie | 30.71 ms |
| Total mediu | 91.82 ms |
| FPS mediu | 10.89 |
| Decizii | {'stop': 88, 'continue': 6, 'emergency_stop': 6} |
| Niveluri pericol | {'MEDIUM': 8, 'LOW': 11, 'CRITICAL': 9, 'HIGH': 5} |

| Imagine | Det. scenariu | Confidence | Total (ms) | Decizie |
|---------|---------------|------------|------------|---------|
| coco_000000000724_stop-sign.jpg | 1 | 0.95 | 6117.16 | stop |
| coco_000000011122_stop-sign.jpg | 1 | 0.97 | 33.49 | stop |
| coco_000000015440_stop-sign.jpg | 1 | 0.75 | 34.47 | stop |
| coco_000000021839_traffic-light.jpg | 1 | 0.66 | 36.15 | stop |
| coco_000000071877_traffic-light.jpg | 0 | - | 35.36 | stop |
| coco_000000076547_traffic-light.jpg | 0 | - | 32.83 | stop |
| coco_000000079408_stop-sign.jpg | 1 | 0.96 | 31.77 | stop |
| coco_000000088462_stop-sign.jpg | 0 | - | 32.81 | stop |
| coco_000000095899_stop-sign.jpg | 1 | 0.95 | 34.33 | stop |
| coco_000000100283_stop-sign.jpg | 1 | 0.92 | 33.69 | stop |
| coco_000000100723_stop-sign.jpg | 0 | - | 32.29 | stop |
| coco_000000104782_stop-sign.jpg | 0 | - | 31.8 | stop |
| coco_000000119516_traffic-light.jpg | 0 | - | 30.95 | stop |
| coco_000000122166_traffic-light.jpg | 0 | - | 31.34 | stop |
| coco_000000122745_stop-sign.jpg | 1 | 0.85 | 31.45 | stop |
| coco_000000126592_stop-sign.jpg | 1 | 0.95 | 30.5 | stop |
| coco_000000127092_stop-sign.jpg | 0 | - | 30.76 | stop |
| coco_000000144706_traffic-light.jpg | 0 | - | 30.34 | stop |
| coco_000000153568_stop-sign.jpg | 0 | - | 31.47 | stop |
| coco_000000165039_traffic-light.jpg | 0 | - | 29.92 | stop |
| coco_000000169996_traffic-light.jpg | 1 | 0.49 | 30.63 | stop |
| coco_000000172856_stop-sign.jpg | 1 | 0.92 | 30.1 | stop |
| coco_000000174482_traffic-light.jpg | 0 | - | 30.1 | stop |
| coco_000000176037_traffic-light.jpg | 0 | - | 30.41 | stop |
| coco_000000183246_traffic-light.jpg | 0 | - | 30.48 | stop |
| coco_000000184324_stop-sign.jpg | 0 | - | 30.09 | stop |
| coco_000000190923_traffic-light.jpg | 1 | 0.45 | 29.78 | stop |
| coco_000000191471_stop-sign.jpg | 1 | 0.90 | 32.11 | stop |
| coco_000000192716_stop-sign.jpg | 1 | 0.94 | 30.22 | stop |
| coco_000000193717_traffic-light.jpg | 1 | 0.53 | 29.61 | stop |
| coco_000000201148_traffic-light.jpg | 0 | - | 30.58 | stop |
| coco_000000212072_stop-sign.jpg | 1 | 0.95 | 31.46 | stop |
| coco_000000213255_traffic-light.jpg | 0 | - | 30.89 | stop |
| coco_000000214200_stop-sign.jpg | 1 | 0.95 | 30.52 | stop |
| coco_000000221754_traffic-light.jpg | 2 | 0.54 | 30.61 | stop |
| coco_000000226417_traffic-light.jpg | 2 | 0.62 | 30.4 | stop |
| coco_000000228942_traffic-light.jpg | 1 | 0.48 | 30.46 | stop |
| coco_000000230450_traffic-light.jpg | 0 | - | 30.9 | stop |
| coco_000000232646_stop-sign.jpg | 1 | 0.93 | 31.24 | stop |
| coco_000000244379_traffic-light.jpg | 2 | 0.82 | 30.68 | stop |
| coco_000000252332_stop-sign.jpg | 1 | 0.94 | 31.46 | stop |
| coco_000000255917_traffic-light.jpg | 0 | - | 30.46 | stop |
| coco_000000260266_traffic-light.jpg | 2 | 0.67 | 31.01 | stop |
| coco_000000261888_stop-sign.jpg | 0 | - | 29.88 | stop |
| coco_000000273617_stop-sign.jpg | 1 | 0.68 | 31.77 | stop |
| coco_000000274272_traffic-light.jpg | 0 | - | 30.89 | stop |
| coco_000000281179_traffic-light.jpg | 0 | - | 30.56 | stop |
| coco_000000283037_traffic-light.jpg | 0 | - | 30.93 | stop |
| coco_000000283038_stop-sign_traffic-light.jpg | 1 | 0.91 | 30.8 | stop |
| coco_000000284762_traffic-light.jpg | 0 | - | 29.69 | stop |
| coco_000000289222_traffic-light.jpg | 2 | 0.83 | 29.75 | stop |
| coco_000000297343_stop-sign.jpg | 1 | 0.79 | 30.21 | stop |
| coco_000000309173_stop-sign.jpg | 1 | 0.91 | 29.61 | stop |
| coco_000000311883_traffic-light.jpg | 2 | 0.54 | 29.95 | stop |
| coco_000000315187_traffic-light.jpg | 0 | - | 29.95 | stop |
| coco_000000323751_traffic-light.jpg | 0 | - | 32.73 | stop |
| coco_000000326627_traffic-light.jpg | 0 | - | 32.77 | stop |
| coco_000000333697_stop-sign.jpg | 0 | - | 30.67 | stop |
| coco_000000336587_stop-sign.jpg | 2 | 0.84 | 29.47 | continue |
| coco_000000343496_stop-sign.jpg | 1 | 0.84 | 29.79 | continue |
| coco_000000347163_stop-sign.jpg | 2 | 0.71 | 31.45 | continue |
| coco_000000361506_stop-sign.jpg | 0 | - | 29.61 | continue |
| coco_000000369442_stop-sign.jpg | 0 | - | 30.19 | continue |
| coco_000000369751_stop-sign.jpg | 1 | 0.63 | 29.95 | continue |
| coco_000000375493_stop-sign.jpg | 0 | - | 29.63 | emergency_stop |
| coco_000000377946_traffic-light.jpg | 2 | 0.58 | 30.05 | emergency_stop |
| coco_000000379800_stop-sign.jpg | 0 | - | 29.39 | emergency_stop |
| coco_000000380706_traffic-light.jpg | 0 | - | 30.56 | emergency_stop |
| coco_000000381971_stop-sign.jpg | 0 | - | 29.68 | emergency_stop |
| coco_000000413689_stop-sign_traffic-light.jpg | 0 | - | 29.27 | emergency_stop |
| coco_000000414133_stop-sign.jpg | 1 | 0.80 | 37.44 | stop |
| coco_000000417779_stop-sign.jpg | 0 | - | 30.5 | stop |
| coco_000000418696_traffic-light.jpg | 0 | - | 30.11 | stop |
| coco_000000423229_traffic-light.jpg | 0 | - | 29.76 | stop |
| coco_000000424975_stop-sign.jpg | 0 | - | 30.43 | stop |
| coco_000000427055_stop-sign.jpg | 0 | - | 30.02 | stop |
| coco_000000438017_traffic-light.jpg | 0 | - | 30.43 | stop |
| coco_000000441553_traffic-light.jpg | 0 | - | 30.47 | stop |
| coco_000000449198_stop-sign_traffic-light.jpg | 0 | - | 29.51 | stop |
| coco_000000454661_traffic-light.jpg | 3 | 0.51 | 31.31 | stop |
| coco_000000475484_traffic-light.jpg | 0 | - | 30.29 | stop |
| coco_000000479030_traffic-light.jpg | 0 | - | 30.58 | stop |
| coco_000000480944_stop-sign_traffic-light.jpg | 2 | 0.67 | 31.43 | stop |
| coco_000000484029_stop-sign.jpg | 1 | 0.96 | 30.78 | stop |
| coco_000000491213_traffic-light.jpg | 0 | - | 30.47 | stop |
| coco_000000491470_traffic-light.jpg | 0 | - | 33.5 | stop |
| coco_000000496854_traffic-light.jpg | 0 | - | 31.59 | stop |
| coco_000000499181_stop-sign_traffic-light.jpg | 0 | - | 30.01 | stop |
| coco_000000501023_stop-sign_traffic-light.jpg | 3 | 0.66 | 30.37 | stop |
| coco_000000522940_stop-sign.jpg | 1 | 0.91 | 31.12 | stop |
| coco_000000523194_stop-sign.jpg | 0 | - | 30.86 | stop |
| coco_000000528980_stop-sign.jpg | 0 | - | 31.55 | stop |
| coco_000000538458_traffic-light.jpg | 0 | - | 31.41 | stop |
| coco_000000558558_traffic-light.jpg | 0 | - | 30.22 | stop |
| coco_000000565778_traffic-light.jpg | 0 | - | 29.89 | stop |
| coco_000000569030_traffic-light.jpg | 0 | - | 30.21 | stop |
| coco_000000571008_stop-sign.jpg | 1 | 0.85 | 29.65 | stop |
| coco_000000571943_traffic-light.jpg | 0 | - | 31.43 | stop |
| coco_000000572555_traffic-light.jpg | 0 | - | 30.09 | stop |
| coco_000000580418_stop-sign.jpg | 0 | - | 29.8 | stop |

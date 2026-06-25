# FPGA — Nexys 4 DDR

> **Notă:** Acest director conține **doar codurile sursă** (fișiere `.v` și constrângeri `.xdc`), **nu** proiectele Vivado complete. Lipsesc fișierele `.xpr`, directoarele `runs/`, bitstream-urile (`.bit`/`.bin`) și alte artefacte generate de Vivado. Pentru sinteză și programarea plăcii trebuie creat sau importat manual un proiect Vivado și adăugate aceste surse.

## Placa utilizată

- Placa: Digilent Nexys 4 DDR
- FPGA: Xilinx Artix-7 XC7A100T-CSG324
- Clock principal: 100 MHz
- Interfață de comunicație: USB-UART
- Mediul de dezvoltare: Xilinx Vivado

## Structura directorului

Directorul `FPGA/` conține **trei seturi de surse**, câte unul pentru fiecare variantă de preprocesare testată:

```
FPGA/
├── grayscale/    # surse — preprocesare grayscale (Etapa 1)
├── rgb/          # surse — preprocesare RGB pass-through (Etapa 2)
└── rgb_upgraded/ # surse — preprocesare RGB pass-through, 3 Mbaud (Etapa 3, recomandat)
```

Fiecare variantă are doar fișierele din `*.srcs/sources_1/new/` și `*.srcs/constrs_1/new/`.

## Surse per variantă

### `grayscale/` — preprocesare grayscale

Surse Verilog:
- `uart_rx.v`
- `uart_tx.v`
- `image_preprocess_rgb.v`
- `frame_engine.v`
- `grayscale_rgb.v`
- `nexys4ddr_yolo_preprocessor_top.v` — **Top Module**

Constrângeri: `Nexys4DDR_UART.xdc`

### `rgb/` — preprocesare RGB pass-through

Surse Verilog:
- `uart_rx.v`
- `uart_tx.v`
- `frame_engine.v`
- `grayscale_rgb.v`
- `nexys4ddr_yolo_preprocessor_top_v2.v` — **Top Module**

Constrângeri: `Nexys4DDR_UART.xdc`

### `rgb_upgraded/` — preprocesare RGB (3 Mbaud, recomandat)

Varianta cu performanță superioară conform testelor experimentale (cap. 5.7 din lucrare).

Surse Verilog:
- `uart_rx.v`
- `uart_tx.v`
- `frame_engine.v`
- `grayscale_rgb.v`
- `nexys4ddr_yolo_preprocessor_top_v2.v` — **Top Module**

Constrângeri: `Nexys4DDR_UART.xdc`

## Crearea unui proiect Vivado din aceste surse

1. Deschide Vivado → **Create Project** → selectează placa **Nexys 4 DDR** (xc7a100tcsg324-1).
2. Adaugă toate fișierele `.v` din subdirectorul variantei alese (`sources_1/new/`).
3. Adaugă fișierul `Nexys4DDR_UART.xdc` din `constrs_1/new/`.
4. Setează **Top Module** corespunzător variantei:
   - `grayscale/`: `nexys4ddr_yolo_preprocessor_top`
   - `rgb/` sau `rgb_upgraded/`: `nexys4ddr_yolo_preprocessor_top_v2`
5. **Run Synthesis** → **Run Implementation** → **Generate Bitstream**.
6. Programează placa (vezi mai jos).

## Programarea plăcii

**Testare rapidă** — încarcă bitstream-ul (`.bit`) direct pe FPGA prin Hardware Manager. Designul se pierde la repornirea plăcii.

**Persistent** — generează fișierul `.bin` și scrie-l în memoria Flash a plăcii. După programare, deconectează și reconectează placa; designul pornește automat la fiecare pornire.

## Atenție la mixarea fișierelor

Fișierele sursă diferă între variante. Nu copia fișiere `.v` dintr-un director în altul fără să verifici top module-ul și parametrii UART. Folosește **un singur set de surse** per proiect Vivado.

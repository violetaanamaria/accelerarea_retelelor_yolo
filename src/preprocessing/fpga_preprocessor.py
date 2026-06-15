#!/usr/bin/env python3
"""
Preprocesare imagini pe FPGA Digilent Nexys 4 DDR via UART/USB.

Pipeline activ (config fpga.protocol = nexys_grayscale, bitstream v2):
  Host downscale 160x120 -> UART -> FPGA (BRAM + RGB pass-through) -> UART
  -> host resize 640x640 (OpenCV) -> YOLO pe CPU.

Protocol nexys_grayscale / v2 (nexys4ddr_yolo_preprocessor_top_v2.v):
  Host -> FPGA: [AA 55] [CMD=0x01] [LEN:4B BE] [RGB 160x120x3] [XOR checksum]
  FPGA -> Host: [AA 55] [CMD=0x81] [LEN:4B BE] [RGB 160x120x3] [XOR checksum]

Protocol legacy „resize” (neimplementat in RTL curent):
  Host -> FPGA: [AA 55] [CMD=0x01] [W:2B] [H:2B] [RGB ...]
  FPGA -> Host: [BB 66] [STATUS] [W:2B] [H:2B] [RGB 640x640]
"""

import cv2
import numpy as np
import yaml
import time
import logging
import struct
from pathlib import Path
from typing import Tuple, Optional, List

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

from .cpu_preprocessor import CPUPreprocessor

MAGIC_TX = bytes([0xAA, 0x55])
MAGIC_RX = bytes([0xBB, 0x66])
CMD_PREPROCESS = 0x01
CMD_RESP_GRAY = 0x81
RESP_OK = 0x00
RESP_ERROR = 0xFF


def xor_checksum(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


class FPGAPreprocessor:
    """Preprocesare accelerată pe Nexys 4 DDR prin UART."""

    def __init__(self, config_path: str = "config/robot_config.yaml"):
        self.config = self._load_config(config_path)
        self.fpga_cfg = self.config.get("fpga", {})
        self.uart_cfg = self.fpga_cfg.get("uart", {})

        self.port = self.uart_cfg.get("port", "auto")
        self.baudrate = self.uart_cfg.get("baudrate", 921600)
        self.timeout = self.uart_cfg.get("timeout", 30.0)
        self.input_size = tuple(self.fpga_cfg.get("output_size", [640, 640]))
        self.send_size = tuple(self.fpga_cfg.get("send_size", [320, 240]))
        self.simulate_on_fail = self.fpga_cfg.get("simulate_on_fail", True)
        self.protocol = self.fpga_cfg.get("protocol", "nexys_grayscale")
        self.uart_paced = self.fpga_cfg.get("uart_paced", True)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("FPGAPreprocessor")

        self.serial: Optional["serial.Serial"] = None
        self.simulation_mode = False
        self._cpu_fallback = CPUPreprocessor(config_path)
        self.last_process_time_ms = 0.0
        self.last_uart_time_ms = 0.0
        self.process_count = 0
        self._process_times: List[float] = []

    def _load_config(self, config_path: str) -> dict:
        path = Path(config_path)
        if not path.is_absolute():
            root = Path(__file__).parent.parent.parent
            path = root / config_path
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _list_serial_candidates(self) -> List[str]:
        if not SERIAL_AVAILABLE:
            return []

        if self.port and self.port != "auto":
            return [self.port]

        candidates = []
        for p in serial.tools.list_ports.comports():
            desc = (p.description or "").lower()
            device = p.device
            if any(k in desc for k in ("ftdi", "digilent", "uart", "usb serial")):
                candidates.append(device)
            elif "usbserial" in device or "ttyUSB" in device or "ttyACM" in device:
                candidates.append(device)

        cu_ports = [c for c in candidates if "/cu." in c]
        other = [c for c in candidates if c not in cu_ports]
        ordered = cu_ports + other
        # Nexys 4 DDR: al doilea port FTDI e de obicei UART (primul = JTAG)
        if len(ordered) >= 2:
            ordered = [ordered[1], ordered[0]] + ordered[2:]
        return ordered

    def _open_serial(self, port: str) -> bool:
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
            self.logger.info(f"FPGA conectat: {port} @ {self.baudrate} baud ({self.protocol})")
            return True
        except Exception as exc:
            self.logger.debug(f"Port {port} indisponibil: {exc}")
            return False

    def initialize(self) -> bool:
        if not SERIAL_AVAILABLE:
            self.logger.warning("pyserial indisponibil — mod simulare FPGA")
            self.simulation_mode = True
            return self._cpu_fallback.initialize()

        ports = self._list_serial_candidates()
        if not ports:
            if self.simulate_on_fail:
                self.logger.warning(
                    "Placa Nexys 4 DDR negăsită — mod SIMULARE FPGA "
                    "(conectează placa via USB și verifică ls /dev/tty.usb*)"
                )
                self.simulation_mode = True
                return self._cpu_fallback.initialize()
            self.logger.error("Nu s-a găsit port serial FPGA!")
            return False

        for port in ports:
            if self._open_serial(port):
                self.simulation_mode = False
                return True

        if self.simulate_on_fail:
            self.logger.warning("Conectare FPGA eșuată pe toate porturile — mod simulare")
            self.simulation_mode = True
            return self._cpu_fallback.initialize()
        self.logger.error("Nu s-a putut deschide niciun port serial FPGA!")
        return False

    def _prepare_send_frame(self, frame: np.ndarray) -> np.ndarray:
        return cv2.resize(frame, self.send_size, interpolation=cv2.INTER_LINEAR)

    def _read_exact(self, size: int) -> bytes:
        chunks: List[bytes] = []
        received = 0
        while received < size:
            block = self.serial.read(size - received)
            if not block:
                raise TimeoutError(
                    f"Timeout UART: primite {received}/{size} bytes "
                    f"(mărește fpga.uart.timeout în config)"
                )
            chunks.append(block)
            received += len(block)
        return b"".join(chunks)

    def _build_tx_packet_resize(self, rgb_frame: np.ndarray) -> bytes:
        h, w = rgb_frame.shape[:2]
        header = MAGIC_TX + struct.pack(">BHH", CMD_PREPROCESS, w, h)
        return header + rgb_frame.tobytes()

    def _build_tx_packet_nexys(self, rgb_frame: np.ndarray) -> bytes:
        payload = rgb_frame.tobytes()
        length = len(payload)
        body = bytes([CMD_PREPROCESS]) + struct.pack(">I", length) + payload
        checksum = xor_checksum(body)
        return MAGIC_TX + body + bytes([checksum])

    def _parse_rx_packet_resize(self, data: bytes) -> np.ndarray:
        if len(data) < 7:
            raise ValueError(f"Răspuns prea scurt: {len(data)} bytes")
        if data[:2] != MAGIC_RX:
            raise ValueError(f"Magic RX invalid: {data[:2].hex()}")

        status = data[2]
        w, h = struct.unpack(">HH", data[3:7])
        if status == RESP_ERROR:
            raise RuntimeError("FPGA a returnat eroare")

        expected = 7 + w * h * 3
        if len(data) < expected:
            raise ValueError(f"Payload incomplet: {len(data)}/{expected}")

        rgb = np.frombuffer(data[7:expected], dtype=np.uint8).reshape(h, w, 3)
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    def _parse_rx_packet_nexys(self, payload: bytes, resp_len: int) -> np.ndarray:
        if len(payload) != resp_len:
            raise ValueError(f"Payload FPGA {len(payload)} != {resp_len}")

        sw, sh = self.send_size
        expected = sw * sh * 3
        if resp_len != expected:
            self.logger.warning(
                f"Lungime răspuns FPGA {resp_len} != așteptat {expected} ({sw}x{sh})"
            )

        pixels = resp_len // 3
        side = int(np.sqrt(pixels))
        if side * side * 3 == resp_len:
            h = w = side
        else:
            w, h = sw, sh

        rgb = np.frombuffer(payload, dtype=np.uint8).reshape(h, w, 3)
        gray = rgb[:, :, 0]
        bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return cv2.resize(bgr, self.input_size, interpolation=cv2.INTER_LINEAR)

    def _process_via_uart_resize(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        uart_start = time.perf_counter()
        small = self._prepare_send_frame(frame)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        tx = self._build_tx_packet_resize(rgb)

        self.serial.reset_input_buffer()
        chunk = 4096
        for i in range(0, len(tx), chunk):
            self.serial.write(tx[i:i + chunk])
            self.serial.flush()
            time.sleep(0.002)

        out_w, out_h = self.input_size
        expected_len = 7 + out_w * out_h * 3
        rx = self._read_exact(expected_len)
        result = self._parse_rx_packet_resize(rx)
        uart_ms = (time.perf_counter() - uart_start) * 1000.0
        return result, uart_ms

    def _write_uart_throttled(self, data: bytes, chunk: int = 512, delay_s: float = 0.005) -> None:
        """Evită overflow RX pe FPGA la 921600 baud."""
        for i in range(0, len(data), chunk):
            self.serial.write(data[i:i + chunk])
            self.serial.flush()
            if i + chunk < len(data):
                time.sleep(delay_s)

    def _process_via_uart_nexys_paced(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        """Compatibil cu FSM-ul Vivado (RX ignorat in timpul TX pe fiecare pixel)."""
        uart_start = time.perf_counter()
        small = self._prepare_send_frame(frame)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        payload = rgb.tobytes()
        length = len(payload)

        header = MAGIC_TX + bytes([CMD_PREPROCESS]) + struct.pack(">I", length)
        body = bytes([CMD_PREPROCESS]) + struct.pack(">I", length) + payload
        host_checksum = xor_checksum(body)

        self.serial.reset_input_buffer()
        self.serial.write(header)
        self.serial.flush()

        rx_hdr = self._read_exact(7)
        if rx_hdr[:2] != MAGIC_TX or rx_hdr[2] != CMD_RESP_GRAY:
            raise ValueError(f"Header răspuns invalid: {rx_hdr.hex()}")
        resp_len = struct.unpack(">I", rx_hdr[3:7])[0]
        if resp_len != length:
            raise ValueError(f"Lungime răspuns FPGA {resp_len} != {length}")

        out = bytearray()
        for offset in range(0, length, 3):
            self.serial.write(payload[offset:offset + 3])
            self.serial.flush()
            out.extend(self._read_exact(3))

        self.serial.write(bytes([host_checksum]))
        self.serial.flush()
        fpga_checksum = self._read_exact(1)[0]

        expected = xor_checksum(bytes([CMD_RESP_GRAY]) + rx_hdr[3:7] + bytes(out))
        if expected != fpga_checksum:
            raise ValueError(
                f"Checksum RX invalid: primit 0x{fpga_checksum:02x}, așteptat 0x{expected:02x}"
            )

        result = self._parse_rx_packet_nexys(bytes(out), length)
        uart_ms = (time.perf_counter() - uart_start) * 1000.0
        return result, uart_ms

    def _process_via_uart_nexys(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        if self.uart_paced:
            return self._process_via_uart_nexys_paced(frame)

        uart_start = time.perf_counter()
        small = self._prepare_send_frame(frame)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        tx = self._build_tx_packet_nexys(rgb)
        payload_len = len(rgb.tobytes())

        self.serial.reset_input_buffer()
        self._write_uart_throttled(tx)

        # FPGA trimite header + pixeli procesati in timp ce primeste payload (UART full-duplex).
        resp_total = 7 + payload_len + 1
        rx = self._read_exact(resp_total)

        if rx[:2] != MAGIC_TX or rx[2] != CMD_RESP_GRAY:
            raise ValueError(f"Header răspuns invalid: {rx[:8].hex()}")

        len_bytes = rx[3:7]
        resp_len = struct.unpack(">I", len_bytes)[0]
        payload = rx[7:7 + resp_len]
        checksum_rx = rx[7 + resp_len]

        expected = xor_checksum(bytes([CMD_RESP_GRAY]) + len_bytes + payload)
        if expected != checksum_rx:
            raise ValueError(
                f"Checksum RX invalid: primit 0x{checksum_rx:02x}, așteptat 0x{expected:02x}"
            )

        result = self._parse_rx_packet_nexys(payload, resp_len)
        uart_ms = (time.perf_counter() - uart_start) * 1000.0
        return result, uart_ms

    def _process_via_uart(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        if self.protocol == "resize":
            return self._process_via_uart_resize(frame)
        return self._process_via_uart_nexys(frame)

    def process(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        start = time.perf_counter()

        if self.simulation_mode:
            result, _ = self._cpu_fallback.process(frame)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self.last_uart_time_ms = 0.0
        else:
            result, uart_ms = self._process_via_uart(frame)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self.last_uart_time_ms = uart_ms

        self.last_process_time_ms = elapsed_ms
        self._process_times.append(elapsed_ms)
        if len(self._process_times) > 100:
            self._process_times.pop(0)
        self.process_count += 1
        return result, elapsed_ms

    def is_simulation(self) -> bool:
        return self.simulation_mode

    def get_average_time_ms(self) -> float:
        if not self._process_times:
            return 0.0
        return sum(self._process_times) / len(self._process_times)

    def get_last_uart_time_ms(self) -> float:
        return self.last_uart_time_ms

    def cleanup(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.logger.info("Conexiune UART închisă")

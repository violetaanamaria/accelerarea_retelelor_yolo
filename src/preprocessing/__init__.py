
from .cpu_preprocessor import CPUPreprocessor
from .fpga_preprocessor import FPGAPreprocessor


def get_preprocessor(use_fpga: bool = False, config_path: str = "config/robot_config.yaml"):
    """
    Factory: returnează preprocesorul potrivit.

    Args:
        use_fpga: True → UART + Nexys 4 DDR; False → OpenCV pe CPU
        config_path: Calea către robot_config.yaml
    """
    if use_fpga:
        return FPGAPreprocessor(config_path)
    return CPUPreprocessor(config_path)

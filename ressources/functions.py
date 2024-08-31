import logging
from ressources import config as cfg
import ast


log = logging.getLogger(__name__)

def validate_aufgaben_str(aufgaben: str) -> bool:
    try:
        aufgaben_dict = ast.literal_eval(f"{{{aufgaben}}}")
        return True
    except SyntaxError:
        return False


def _to_roman_numeral(value: int) -> str:
    """Private function to convert integer number to roman string

    Args:
        value (int): Value to convert

    Returns:
        str: Roman number of given value
    """
    roman_map = {
        1: "I", 5: "V",
        10: "X", 50: "L", 
        100: "C", 500: "D",
        1000: "M",
    }
    result = ""
    remainder = value
    for i in sorted(roman_map.keys(), reverse=True):# 2
        if remainder > 0:
            multiplier = i
            roman_digit = roman_map[i]
            times = remainder // multiplier         # 3
            remainder = remainder % multiplier      # 4
            result += roman_digit * times           # 4
    log.debug(f"Input number {value} has been converted to '{result}'")
    return result

def start_log(level = logging.DEBUG) -> None:
    for module_name, log_level in cfg.logger_custom_level.items():
        logging.getLogger(module_name).setLevel(log_level)
    logging.root.handlers = []
    logging.basicConfig(
        level=level,
        format=cfg.logger_format,
        handlers=[
            logging.StreamHandler(),
        ]
    )
    log.debug("Logging started")
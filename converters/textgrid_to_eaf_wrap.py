from pathlib import Path
from typing import Literal
from xml.etree import ElementTree as ET

from . import textgrid_to_eaf_core as core
from . import ConversionError

Mode = Literal["short", "long"]


def convert(input_tg: str | Path,
            output_eaf: str | Path,
            *,
            mode: Mode = "short") -> None:
    """
    Конвертация *.TextGrid* → *.eaf* с нормализованным отловом ошибок.
    """
    try:
        path_in = Path(input_tg)
        path_out = Path(output_eaf)

        if mode not in ("short", "long"):
            raise ValueError(f"Неизвестный режим: {mode}")
        if not path_in.is_file():
            raise FileNotFoundError(path_in)
        if path_in.suffix.lower() not in {".textgrid", ".tg"}:
            raise ValueError("Файл должен иметь расширение .TextGrid / .tg")
        tg = core.parse_textgrid(path_in, mode=mode)
        core.write_eaf(path_out, core.textgrid_to_eaf(tg))

        if not path_out.exists():
            raise RuntimeError("Ядро не создало выходной .eaf")

    except (FileNotFoundError, UnicodeDecodeError, ET.ParseError,
            ValueError, RuntimeError) as exc:
        raise ConversionError(f"TextGrid → EAF: {exc}") from exc
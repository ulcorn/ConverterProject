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

        core.convert(str(path_in))

        produced = path_in.with_suffix(".eaf")
        if not produced.exists():
            raise RuntimeError("Ядро не создало выходной .eaf")

        produced.replace(path_out)

    except (FileNotFoundError, UnicodeDecodeError, ET.ParseError,
            ValueError, RuntimeError, core.ConversionError) as exc:
        raise ConversionError(f"TextGrid → EAF: {exc}") from exc

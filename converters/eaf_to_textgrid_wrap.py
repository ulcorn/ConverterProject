"""
Обёртка над eaf_to_textgrid_core.eaf_to_textgrid
"""

from pathlib import Path
from typing import Literal

from praatio import textgrid
import pympi

from . import eaf_to_textgrid_core as core
from . import ConversionError

Mode = Literal["short", "long"]


def convert(input_eaf: str | Path, output_tg: str | Path, mode: Mode = "short") -> None:
    """
    Конвертирует .eaf → .TextGrid (short или long).
    """
    path_in, path_out = Path(input_eaf), Path(output_tg)

    if not path_in.is_file():
        print(f"Файл не найден: {path_in}")
        return

    # Проверяем расширение
    if path_in.suffix.lower() not in {".eaf", ".xml"}:
        print("Это не тот файл")
        return

    try:
        if mode not in ("short", "long"):
            raise ValueError(f"Неизвестный режим: {mode}")

        core.eaf_to_textgrid(path_in, path_out)

        if mode == "long":
            tg = textgrid.openTextgrid(str(path_out), includeEmptyIntervals=True)
            tg.save(str(path_out), format="long_textgrid", includeBlankSpaces=True)
    except (textgrid.TGReadWriteError, ValueError, Exception) as exc:
        raise ConversionError(f"EAF → TextGrid: {exc}") from exc

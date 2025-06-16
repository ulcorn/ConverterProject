"""
Обёртка над textgrid_to_eaf_core.convert.
Параметр `mode` используется только для проверки входного файла:
короткий (`short`) или длинный (`long`) синтаксис TextGrid.
Сам core‑парсер умеет определять это автоматически, так что здесь
мы просто вызываем convert «как есть».
"""

from pathlib import Path
from typing import Literal

from . import textgrid_to_eaf_core as core

Mode = Literal["short", "long"]


def convert(input_tg: str | Path, output_eaf: str | Path, mode: Mode = "short") -> None:
    """
    Конвертация .TextGrid → .eaf.
    Вызов исходной функции `core.convert`, не меняя её.
    """
    path_in, path_out = Path(input_tg), Path(output_eaf)
    if not path_in.is_file():
        raise FileNotFoundError(path_in)

    # core.convert записывает файл рядом с входным,
    # поэтому временно подменяем имя, а потом переносим.
    core.convert(str(path_in))
    produced = path_in.with_suffix(".eaf")
    produced.rename(path_out)

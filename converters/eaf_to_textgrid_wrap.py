"""
Обёртка над eaf_to_textgrid_core.eaf_to_textgrid
добавляет параметр `mode` («short» | «long»).
"""

from pathlib import Path
from typing import Literal

from praatio import textgrid
import pympi

# импортируем ВАШ исходный код как отдельный модуль
from . import eaf_to_textgrid_core as core

Mode = Literal["short", "long"]


def convert(input_eaf: str | Path, output_tg: str | Path, mode: Mode = "short") -> None:
    """
    Конвертирует .eaf → .TextGrid (short / long).
    Не меняет исходный core‑код – просто повторяет его логику,
    но вызывая `tg.save(..., format="long_textgrid")`, если нужно.
    """
    path_in, path_out = Path(input_eaf), Path(output_tg)

    if not path_in.is_file():
        raise FileNotFoundError(path_in)

    # ► Повторяем шаги core‑функции. Она компактная – копируем здесь:
    elan = pympi.Elan.Eaf(str(path_in))
    ts_map = core.build_ts_map(elan)
    max_time = max(ts_map.values(), default=0.0)

    tg = textgrid.Textgrid(minTimestamp=0.0, maxTimestamp=max_time)

    for tier_name in elan.get_tier_names():
        raw_ann = elan.get_annotation_data_for_tier(tier_name)
        intervals = core.to_intervals(core.iter_annotations(raw_ann), ts_map)

        tg.addTier(textgrid.IntervalTier(
            name=tier_name,
            entries=intervals,
            minT=0.0,
            maxT=max_time,
        ))

    tg_fmt = "short_textgrid" if mode == "short" else "long_textgrid"

    tg.save(str(path_out), format=tg_fmt, includeBlankSpaces=True)

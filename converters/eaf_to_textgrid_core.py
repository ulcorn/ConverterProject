from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple, Union

import pympi
from praatio import textgrid

TimeSlotMap = Dict[str, float]  # id тайм-слота  ->  секунд
Interval = Tuple[float, float, str]


def build_ts_map(eaf: pympi.Elan.Eaf) -> TimeSlotMap:
    """Словарь «tsID → секунды»."""
    return {str(ts_id): ms / 1000.0 for ts_id, ms in eaf.timeslots.items()}


def _ms_or_slot(value: Union[str, int, float]) -> Union[str, float]:
    """
    Если value похоже на число (в миллисекундах), вернуть его как float/секунды.
    Иначе вернуть как str (будем искать в карте тайм-слотов).
    """
    try:
        ms = float(value)
        if ms.is_integer() or ms > 50:  # примитивная проверка, но работает
            return ms / 1000.0
    except (TypeError, ValueError):
        pass
    return str(value)


def iter_annotations(raw_ann) -> Iterable[Sequence]:
    """
    Привести raw_ann к последовательности
    (start_any, end_any, text), где start/end могут быть:
        float — уже секунды,
        str   — id тайм-слота ('ts3').
    """
    raw_iter = raw_ann.values() if isinstance(raw_ann, dict) else raw_ann

    for ann in raw_iter:
        if len(ann) == 3:
            start, end, text = ann
        elif len(ann) >= 4:
            _, start, end, text = ann[:4]
        else:
            continue
        yield _ms_or_slot(start), _ms_or_slot(end), text or ""


def to_intervals(
        ann_iter: Iterable[Sequence], ts_map: TimeSlotMap
) -> List[Interval]:
    """Преобразовать кортежи в итоговые интервалы (секунды, секунды, текст)."""
    intervals: List[Interval] = []

    for start_raw, end_raw, text in ann_iter:

        if isinstance(start_raw, float) and isinstance(end_raw, float):
            start_sec, end_sec = start_raw, end_raw
        else:
            try:
                start_sec = ts_map[str(start_raw)]
                end_sec = ts_map[str(end_raw)]
            except KeyError:
                print(f"[WARN]  неизвестный TIME_SLOT_ID "
                      f"{start_raw!r} / {end_raw!r}", file=sys.stderr)
                continue

        if end_sec < start_sec:
            start_sec, end_sec = end_sec, start_sec

        intervals.append((start_sec, end_sec, text.strip()))

    return sorted(intervals, key=lambda it: it[0])


def eaf_to_textgrid(eaf_path: Path, tg_path: Path) -> None:
    if not eaf_path.is_file():
        raise FileNotFoundError(f"EAF-файл не найден: {eaf_path}")

    elan = pympi.Elan.Eaf(str(eaf_path))
    ts_map = build_ts_map(elan)
    max_time = max(ts_map.values(), default=0.0)

    tg = textgrid.Textgrid(minTimestamp=0.0, maxTimestamp=max_time)

    for tier_name in elan.get_tier_names():
        raw_ann = elan.get_annotation_data_for_tier(tier_name)
        intervals = to_intervals(iter_annotations(raw_ann), ts_map)

        tg.addTier(textgrid.IntervalTier(
            name=tier_name,
            entries=intervals,
            minT=0.0,
            maxT=max_time,
        ))

    try:
        tg.save(str(tg_path), format="short_textgrid",
                includeEmptyIntervals=True)
    except TypeError:
        tg.save(str(tg_path), format="short_textgrid",
                includeBlankSpaces=True)

    print(f"Ваш файл тут - {tg_path}")


def cli() -> None:
    p = argparse.ArgumentParser(description="Convert .eaf to .TextGrid")
    p.add_argument("input", help=".eaf file")
    p.add_argument("output", help=".TextGrid destination")
    args = p.parse_args()

    eaf_to_textgrid(Path(args.input).expanduser(),
                    Path(args.output).expanduser())

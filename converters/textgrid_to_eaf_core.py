import sys
import typing as tp
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET


@dataclass
class EAF:
    """
    Представляет структуру аннотаций ELAN EAF.
    """

    @dataclass
    class Tier:
        """
        Контейнер для аннотаций внутри уровня EAF.
        """

        @dataclass
        class Annotation:
            pass

        @dataclass
        class AlignedAnnotation(Annotation):
            """
            Выравненная по времени аннотация.

            Attributes:
                value: Текст аннотации.
                start_ref: Идентификатор начальной временной метки.
                end_ref: Идентификатор конечной временной метки.
                svg_ref: Опциональная ссылка на SVG.
            """
            value: str
            start_ref: str
            end_ref: str
            svg_ref: str | None

        @dataclass
        class RefAnnotation(Annotation):
            ref_id: str
            prev_annot: str | None
            value: str = ""

        annotations: dict[str, 'EAF.Tier.Annotation'] = field(default_factory=dict)

    time_slots: dict[str, str | None] = field(default_factory=dict)
    tiers: dict[str, Tier] = field(default_factory=dict)


def _eaf_to_etree_root(eaf: EAF) -> ET.Element:
    date = datetime.now(timezone(timedelta(hours=3))).isoformat()
    root = ET.Element('ANNOTATION_DOCUMENT', attrib={
        'AUTHOR': '', 'DATE': date, 'VERSION': '1.0'
    })

    ET.SubElement(root, "LINGUISTIC_TYPE",
                  attrib={"LINGUISTIC_TYPE_ID": "default-lt",
                          "TIME_ALIGNABLE": "true"})

    ET.SubElement(root, 'HEADER', attrib={'MEDIA_FILE': '',
                                          'TIME_UNITS': 'milliseconds'})
    time_order = ET.SubElement(root, 'TIME_ORDER')

    for ts_id, ts_val in sorted(eaf.time_slots.items(),
                                key=lambda kv: int(kv[1])):
        ET.SubElement(time_order, 'TIME_SLOT',
                      attrib={'TIME_SLOT_ID': ts_id, 'TIME_VALUE': ts_val or ""})

    for tier_id, tier in eaf.tiers.items():
        cur_tier = ET.SubElement(root, 'TIER', attrib={
            'TIER_ID': tier_id,
            'LINGUISTIC_TYPE_REF': 'default-lt'
        })
        for ann_id, annot in tier.annotations.items():
            ann_el = ET.SubElement(cur_tier, 'ANNOTATION')
            if isinstance(annot, EAF.Tier.AlignedAnnotation):
                al_el = ET.SubElement(ann_el, 'ALIGNABLE_ANNOTATION', attrib={
                    'ANNOTATION_ID': ann_id,
                    'TIME_SLOT_REF1': annot.start_ref,
                    'TIME_SLOT_REF2': annot.end_ref,
                })
                if annot.svg_ref:
                    al_el.set('SVG_REF', annot.svg_ref)
                ET.SubElement(al_el, 'ANNOTATION_VALUE').text = annot.value
            else:
                ref_el = ET.SubElement(ann_el, 'REF_ANNOTATION', attrib={
                    'ANNOTATION_ID': ann_id,
                    'ANNOTATION_REF': annot.ref_id,
                })
                if annot.prev_annot:
                    ref_el.set('PREVIOUS_ANNOTATION', annot.prev_annot)
                ET.SubElement(ref_el, 'ANNOTATION_VALUE').text = annot.value
    return root


def write_eaf(path: str | Path, eaf: EAF) -> None:
    """
    Записывает объект EAF в EAF/XML файл с выравниванием и ссылками.

    Args:
        path: Путь до выходного .eaf файла.
        eaf: Экземпляр EAF для записи.
    """
    tree = ET.ElementTree(_eaf_to_etree_root(eaf))
    try:
        ET.indent(tree, space="    ", level=0)
    except AttributeError:
        pass
    tree.write(path, encoding="utf-8", xml_declaration=True)


@dataclass
class TextGrid:
    """
    Представляет TextGrid-файл (формат Praat) с несколькими уровнями (tiers),
    содержащими интервалы или метки во времени.
    """

    class Tier:
        """
        Базовый класс для уровня в TextGrid, хранит имя, диапазон и элементы.
        """

        def __init__(self, name: str, start: str = '1e9', end: str = '0.0', size: int = 0) -> None:
            self.name = name
            self.start = start
            self.end = end
            self.size = size
            self.items = []

        def extend(self, item) -> None:
            """
            Добавляет элемент (интервал или точку) в уровень.
            """
            self.items.append(item)

    class IntervalTier(Tier):
        @dataclass
        class Interval:
            """
            Представляет помеченный временной интервал.
            """
            label: str
            start: str
            end: str

    class TextTier(Tier):
        @dataclass
        class Point:
            """
            Представляет помеченную временную точку.
            """
            time: str
            label: str

    def __init__(self, xmin: str = '1e9', xmax: str = '0.0') -> None:
        self.xmin: str = xmin
        self.xmax: str = xmax
        self.tiers: list[TextGrid.Tier] = []

    @staticmethod
    def write(filepath: str, textgrid: 'TextGrid') -> None:
        """
        Записывает объект TextGrid в файл в тексовом формате Praat.
        """
        with open(filepath, 'w') as file:
            preface = 'File type = "ooTextFile"\nObject class = "TextGrid"\n'
            file.write(preface + '\n')

            file.write(str(textgrid.xmin) + '\n')
            file.write(str(textgrid.xmax) + '\n')

            if len(textgrid.tiers) > 0:
                file.writelines(['<exists>\n', str(len(textgrid.tiers)) + '\n'])

                for tier in textgrid.tiers:
                    file.writelines(['"Interval Tier"\n', f'"{tier.name}"\n', tier.start + '\n', tier.end + '\n',
                                     str(tier.size) + '\n'])
                    for item in tier.items:
                        file.writelines([item.start + '\n', item.end + '\n', f'"{item.label}"\n'])


def _parse_textgrid_short(lines: list[str]) -> TextGrid:
    """короткий формат Praat"""
    short_mode = lines[4][0].isdigit()
    xmin = lines[3].split('= ')[-1]
    xmax = lines[4].split('= ')[-1]
    tg = TextGrid(xmin, xmax)
    idx = 5
    while idx < len(lines):
        if lines[idx].endswith('Tier"'):
            name = lines[idx + 1].split('= ')[-1][1:-1]
            start = lines[idx + 2].split('= ')[-1]
            end = lines[idx + 3].split('= ')[-1]
            size = int(lines[idx + 4].split('= ')[-1])
            idx += 4

            if lines[idx - 4].split('= ')[-1][1] == 'I':
                tg.tiers.append(TextGrid.IntervalTier(name, start, end, size))
                for i in range(size):
                    if not short_mode:
                        idx += 1
                    start = lines[idx + 1].split('= ')[-1]
                    end = lines[idx + 2].split('= ')[-1]
                    label = lines[idx + 3].split('= ')[-1][1:-1]
                    tg.tiers[-1].extend(TextGrid.IntervalTier.Interval(label, start, end))
                    idx += 3

            elif lines[idx - 4].split('= ')[-1][1] == 'T':
                tg.tiers.append(TextGrid.TextTier(name, start, end, size))
                for i in range(size):
                    if not short_mode:
                        idx += 1
                    time = lines[idx + 1].split('= ')[-1]
                    label = lines[idx + 2].split('= ')[-1][1:-1]
                    tg.tiers[-1].extend(TextGrid.TextTier.Point(time, label))
                    idx += 2

        idx += 1

    return tg


def _parse_textgrid_long(lines: list[str]) -> TextGrid:
    xmin = lines[3].split('=')[-1].strip()
    xmax = lines[4].split('=')[-1].strip()
    tg = TextGrid(xmin, xmax)

    idx = 7
    while idx < len(lines):
        line = lines[idx].lstrip()

        if line.startswith("item []"):
            idx += 1
            continue

        if re.match(r"item \[\d+\]:", line):
            tier_type = lines[idx + 1].split('=')[-1].strip().strip('"')
            name = lines[idx + 2].split('=')[-1].strip().strip('"')
            start = lines[idx + 3].split('=')[-1].strip()
            end = lines[idx + 4].split('=')[-1].strip()
            size = int(lines[idx + 5].split('=')[-1].strip())
            idx += 6

            if tier_type.lower().startswith("interval"):
                tier = TextGrid.IntervalTier(name, start, end, size)
                for _ in range(size):
                    xmin_i = lines[idx + 1].split('=')[-1].strip()
                    xmax_i = lines[idx + 2].split('=')[-1].strip()
                    text_i = lines[idx + 3].split('=')[-1].strip().strip('"')
                    tier.extend(TextGrid.IntervalTier.Interval(text_i, xmin_i, xmax_i))
                    idx += 4
            else:  # TextTier
                tier = TextGrid.TextTier(name, start, end, size)
                for _ in range(size):
                    time_i = lines[idx + 1].split('=')[-1].strip()
                    text_i = lines[idx + 2].split('=')[-1].strip().strip('"')
                    tier.extend(TextGrid.TextTier.Point(time_i, text_i))
                    idx += 3

            tg.tiers.append(tier)
        else:
            idx += 1
    return tg


def parse_textgrid(filepath: str | Path, *, mode: str = "short") -> TextGrid:
    """универсальный вызов: mode='short' | 'long'"""
    with open(filepath, encoding='utf-8') as fh:
        lines = [ln.strip() for ln in fh]
    if mode == "short":
        return _parse_textgrid_short(lines)
    if mode == "long":
        return _parse_textgrid_long(lines)
    raise ValueError(f"Unknown TextGrid mode: {mode}")


def textgrid_to_eaf(tg: TextGrid) -> EAF:
    """
    Конвертирует TextGrid-структуру в EAF-структуру.

    Args:
        textgrid: Объект TextGrid с уровнями и метками.

    Returns:
        EAF: Эквивалентный EAF объект.
    """
    eaf = EAF()
    ts_id = 1
    a_id = 1
    time_stamps: dict[str, str] = {}

    for tier in tg.tiers:
        if not isinstance(tier, TextGrid.IntervalTier):
            continue
        annotations: dict[str, EAF.Tier.AlignedAnnotation] = {}
        for item in tier.items:
            start = str(int(float(item.start) * 1000))
            if start not in time_stamps:
                time_stamps[start] = f"ts{ts_id}";
                ts_id += 1
            end = str(int(float(item.end) * 1000))
            if end not in time_stamps:
                time_stamps[end] = f"ts{ts_id}";
                ts_id += 1
            annotations[f"a{a_id}"] = EAF.Tier.AlignedAnnotation(
                item.label, time_stamps[start], time_stamps[end], None
            )
            a_id += 1
        eaf.tiers[tier.name] = EAF.Tier(annotations)
    eaf.time_slots = {v: k for k, v in time_stamps.items()}
    return eaf

import pathlib
import sys
import typing as tp

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from xml.dom import minidom
from xml.etree import ElementTree as ET


@dataclass
class TextGrid:
    class Tier:
        def __init__(self, name: str, start: str = '1e9', end: str = '0.0', size: int = 0) -> None:
            self.name = name
            self.start = start
            self.end = end
            self.size = size
            self.items = []

        def extend(self, item) -> None:
            self.items.append(item)

    class IntervalTier(Tier):
        @dataclass
        class Interval:
            label: str
            start: str
            end: str

    class TextTier(Tier):
        @dataclass
        class Point:
            time: str
            label: str

    def __init__(self, xmin: str = '1e9', xmax: str = '0.0') -> None:
        self.xmin: str = xmin
        self.xmax: str = xmax
        self.tiers: list[TextGrid.Tier] = []

    @staticmethod
    def write(filepath: str, textgrid: 'TextGrid') -> None:
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


def parse_textgrid(filepath: str) -> TextGrid:
    with open(filepath) as file:
        lines = list(map(str.strip, file.readlines()))
        short_mode = lines[4][0].isdigit()
        xmin = lines[3].split('= ')[-1]
        xmax = lines[4].split('= ')[-1]
        textgrid = TextGrid(xmin, xmax)
        cur_line_idx = 5

        while cur_line_idx < len(lines):
            if lines[cur_line_idx].endswith('Tier"'):
                name = lines[cur_line_idx + 1].split('= ')[-1][1:-1]
                start = lines[cur_line_idx + 2].split('= ')[-1]
                end = lines[cur_line_idx + 3].split('= ')[-1]
                size = int(lines[cur_line_idx + 4].split('= ')[-1])
                cur_line_idx += 4

                if lines[cur_line_idx - 4].split('= ')[-1][1] == 'I':  # IntervalTier
                    textgrid.tiers.append(TextGrid.IntervalTier(name, start, end, size))
                    for i in range(size):
                        if not short_mode:
                            cur_line_idx += 1
                        start = lines[cur_line_idx + 1].split('= ')[-1]
                        end = lines[cur_line_idx + 2].split('= ')[-1]
                        label = lines[cur_line_idx + 3].split('= ')[-1][1:-1]
                        textgrid.tiers[-1].extend(TextGrid.IntervalTier.Interval(label, start, end))
                        cur_line_idx += 3

                elif lines[cur_line_idx - 4].split('= ')[-1][1] == 'T':  # TextTier
                    textgrid.tiers.append(TextGrid.TextTier(name, start, end, size))
                    for i in range(size):
                        if not short_mode:
                            cur_line_idx += 1
                        time = lines[cur_line_idx + 1].split('= ')[-1]
                        label = lines[cur_line_idx + 2].split('= ')[-1][1:-1]
                        textgrid.tiers[-1].extend(TextGrid.TextTier.Point(time, label))
                        cur_line_idx += 2

            cur_line_idx += 1

    return textgrid


@dataclass
class EAF:
    @dataclass
    class Tier:
        @dataclass
        class Annotation:
            pass

        @dataclass
        class AlignedAnnotation(Annotation):
            value: str
            start_ref: str
            end_ref: str
            svg_ref: str | None

        @dataclass
        class RefAnnotation(Annotation):
            ref_id: str
            prev_annot: str | None

        annotations: dict[str, 'EAF.Tier.Annotation'] = field(default_factory=dict)

    time_slots: dict[str, str | None] = field(default_factory=dict)
    tiers: dict[str, Tier] = field(default_factory=dict)


def parse_eaf(filepath: str) -> EAF:
    eaf = EAF()

    root = ET.parse(filepath).getroot()
    for child in root:
        match child.tag:
            case 'TIME_ORDER':
                for elem in child:
                    eaf.time_slots[elem.attrib['TIME_SLOT_ID']] = elem.attrib.get('TIME_VALUE', None)
            case 'TIER':
                tier_id = child.attrib['TIER_ID']
                eaf.tiers[tier_id] = EAF.Tier()
                for elem in child:
                    if elem.tag == 'ANNOTATION':
                        for annot in elem:
                            if annot.tag == 'ALIGNABLE_ANNOTATION':
                                value = annot[0].text
                                id = annot.attrib['ANNOTATION_ID']
                                start_ref = annot.attrib['TIME_SLOT_REF1']
                                end_ref = annot.attrib['TIME_SLOT_REF2']
                                svg_ref = annot.attrib.get('SVG_REF', None)
                                eaf.tiers[tier_id].annotations[id] = EAF.Tier.AlignedAnnotation(value, start_ref,
                                                                                                end_ref,
                                                                                                svg_ref)
                            elif annot.tag == 'REF_ANNOTATION':
                                id = annot.attrib['ANNOTATION_ID']
                                ref_id = annot.attrib['ANNOTATION_REF']
                                prev_annot = annot.attrib.get('PREVIOUS_ANNOTATION', None)
                                eaf.tiers[tier_id].annotations[id] = EAF.Tier.RefAnnotation(ref_id, prev_annot)

    return eaf


def write_eaf(path: str, eaf: 'EAF') -> None:
    def _eaf_to_etree_root(eaf: 'EAF') -> ET.Element:
        date = datetime.now(timezone(timedelta(hours=3))).isoformat()

        root = ET.Element('ANNOTATION_DOCUMENT', attrib={'AUTHOR': '', 'DATE': date, 'VERSION': '1.0'})

        ET.SubElement(root, 'HEADER', attrib={'MEDIA_FILE': '', 'TIME_UNITS': 'milliseconds'})
        time_order = ET.SubElement(root, 'TIME_ORDER')

        for time_slot_id in eaf.time_slots:
            ET.SubElement(time_order, 'TIME_SLOT',
                          attrib={'TIME_SLOT_ID': time_slot_id, 'TIME_VALUE': eaf.time_slots[time_slot_id]})

        # LINGUISTIC_TYPE_REF - ОТКУДА БРАТЬ???
        for tier_id in eaf.tiers:
            cur_tier = ET.SubElement(root, 'TIER', attrib={'TIER_ID': tier_id, 'LINGUISTIC_TYPE_REF': 'default-lt'})
            for annotation_id, annotation in eaf.tiers[tier_id].annotations.items():
                cur_annot = ET.SubElement(cur_tier, 'ANNOTATION')
                if isinstance(annotation, EAF.Tier.AlignedAnnotation):
                    elem = ET.SubElement(cur_annot, 'ALIGNABLE_ANNOTATION',
                                         attrib={'ANNOTATION_ID': annotation_id, 'TIME_SLOT_REF1': annotation.start_ref,
                                                 'TIME_SLOT_REF2': annotation.end_ref})
                    if annotation.svg_ref:
                        elem.attrib['SVG_REF'] = annotation.svg_ref
                    ET.SubElement(elem, 'ANNOTATION_VALUE').text = annotation.value
                elif isinstance(annotation, EAF.Tier.RefAnnotation):
                    elem = ET.SubElement(cur_annot, 'REF_ANNOTATION',
                                         attrib={'ANNOTATION_ID': annotation_id, 'ANNOTATION_REF': annotation.ref_id})
                    elem.text = annotation.value
                    if annotation.prev_annot:
                        elem.attrib['PREVIOUS_ANNOTATION'] = annotation.prev_annot
                    ET.SubElement(elem, 'ANNOTATION_VALUE').text = annotation.value

        return root

    root = _eaf_to_etree_root(eaf)
    pretty_xml = minidom.parseString(ET.tostring(root, encoding='utf-8')).toprettyxml(indent='  ')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)


def eaf_to_textgrid(eaf: EAF) -> TextGrid:
    textgrid = TextGrid()
    for tier_id, tier in eaf.tiers.items():
        tier_start = 1e9
        tier_end = 0.0
        textgrid.tiers.append(TextGrid.Tier(tier_id))
        for annotation_id, annotation in tier.annotations.items():
            label = annotation.value
            start = float(eaf.time_slots[annotation.start_ref]) / 1000.0
            end = float(eaf.time_slots[annotation.end_ref]) / 1000.0

            textgrid.tiers[-1].extend(TextGrid.IntervalTier.Interval(label, str(start), str(end)))

            tier_start = min(tier_start, start)
            tier_end = max(tier_end, end)
            textgrid.tiers[-1].size += 1

        textgrid.tiers[-1].start = str(tier_start)
        textgrid.tiers[-1].end = str(tier_end)

        textgrid.xmin = str(min(float(textgrid.xmin), tier_start))
        textgrid.xmax = str(max(float(textgrid.xmax), tier_end))

    return textgrid


def textgrid_to_eaf(textgrid: TextGrid) -> EAF:
    eaf = EAF()

    ts_id = 1
    a_id = 1
    time_stamps: dict[str, str] = {}
    for tier in textgrid.tiers:
        annotations: dict[str, EAF.Tier.AlignedAnnotation] = {}
        for item in tier.items:
            start = str(int(float(item.start) * 1000))
            if start not in time_stamps:
                time_stamps[start] = f'ts{ts_id}'
                ts_id += 1

            end = str(int(float(item.end) * 1000))
            if end not in time_stamps:
                time_stamps[end] = f'ts{ts_id}'
                ts_id += 1

            annotations[f'a{a_id}'] = EAF.Tier.AlignedAnnotation(item.label, time_stamps[start], time_stamps[end], None)
            a_id += 1

        eaf.tiers[tier.name] = EAF.Tier(annotations)
        eaf.time_slots = dict(zip(time_stamps.values(), time_stamps.keys()))

    return eaf


def convert(filepath: str) -> None:
    if filepath.endswith('.eaf') or filepath.endswith('.xml'):
        try:
            eaf = parse_eaf(filepath)
            # path = filepath.split('.')[0] + '.TextGrid'
            path = filepath.split('.')[0] + '.TextGrid'
            TextGrid.write(path, eaf_to_textgrid(eaf))
        except Exception as e:
            raise 'Something went wrong'
    else:
        textgrid = parse_textgrid(filepath)
        path = filepath.split('.')[0] + '.eaf'
        write_eaf(path, textgrid_to_eaf(textgrid))

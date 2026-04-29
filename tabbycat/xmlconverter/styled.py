from __future__ import annotations

import argparse
import copy
import zipfile
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

from .converter_core import (
    AdjudicatorInfo,
    TeamInfo,
    TeamStanding,
    SpeakerStanding,
    DebateResult,
    build_aggregates,
    build_output_path,
    adjudicator_short,
    format_number,
    parse_debatexml,
    safe_stdev,
    team_display,
    trimmed_total,
    weighted_ballots_for_side,
)

DEFAULT_TEMPLATE_PATH = Path(__file__).resolve().parent / "assets" / "sda_results_template.xlsx"

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS = {"m": MAIN_NS}

ET.register_namespace("", MAIN_NS)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
ET.register_namespace("mc", "http://schemas.openxmlformats.org/markup-compatibility/2006")
ET.register_namespace("x14ac", "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac")
ET.register_namespace("xr", "http://schemas.microsoft.com/office/spreadsheetml/2014/revision")
ET.register_namespace("xr2", "http://schemas.microsoft.com/office/spreadsheetml/2015/revision2")
ET.register_namespace("xr3", "http://schemas.microsoft.com/office/spreadsheetml/2016/revision3")


def q(tag: str) -> str:
    return f"{{{MAIN_NS}}}{tag}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert DebateXML to a styled SDA-like workbook using an XLSX template.")
    parser.add_argument("xml_path", type=Path, help="Path to the Tabbycat DebateXML export")
    parser.add_argument("-t", "--template", type=Path, required=True, help="Path to the reference XLSX template workbook")
    parser.add_argument("-o", "--output", type=Path, help="Optional output .xlsx path")
    return parser.parse_args()


def clear_cell(cell: ET.Element) -> None:
    cell.attrib.pop("t", None)
    for child in list(cell):
        cell.remove(child)


def cell_sort_key(ref: str) -> tuple[int, int]:
    letters = ""
    digits = ""
    for char in ref:
        if char.isalpha():
            letters += char
        elif char.isdigit():
            digits += char
    col = 0
    for char in letters:
        col = col * 26 + (ord(char.upper()) - 64)
    return int(digits), col


def get_sheet_data(sheet_root: ET.Element) -> ET.Element:
    return sheet_root.find(q("sheetData"))


def ensure_row(sheet_root: ET.Element, row_no: int) -> ET.Element:
    sheet_data = get_sheet_data(sheet_root)
    row = sheet_data.find(f"m:row[@r='{row_no}']", NS)
    if row is not None:
        return row
    row = ET.Element(q("row"), {"r": str(row_no)})
    inserted = False
    for index, existing in enumerate(list(sheet_data)):
        existing_r = int(existing.attrib.get("r", "0"))
        if existing_r > row_no:
            sheet_data.insert(index, row)
            inserted = True
            break
    if not inserted:
        sheet_data.append(row)
    return row


def ensure_cell(sheet_root: ET.Element, ref: str) -> ET.Element:
    row_no, _col_no = cell_sort_key(ref)
    row = ensure_row(sheet_root, row_no)
    for cell in row.findall(q("c")):
        if cell.attrib.get("r") == ref:
            return cell
    cell = ET.Element(q("c"), {"r": ref})
    inserted = False
    for index, existing in enumerate(list(row)):
        if cell_sort_key(existing.attrib.get("r", "A1"))[1] > _col_no:
            row.insert(index, cell)
            inserted = True
            break
    if not inserted:
        row.append(cell)
    return cell


def get_cell(sheet_root: ET.Element, ref: str) -> ET.Element | None:
    row_no, _col_no = cell_sort_key(ref)
    sheet_data = get_sheet_data(sheet_root)
    row = sheet_data.find(f"m:row[@r='{row_no}']", NS)
    if row is None:
        return None
    for cell in row.findall(q("c")):
        if cell.attrib.get("r") == ref:
            return cell
    return None


def set_cell_value(sheet_root: ET.Element, ref: str, value) -> None:
    if value in (None, ""):
        cell = get_cell(sheet_root, ref)
        if cell is not None:
            clear_cell(cell)
        return

    cell = ensure_cell(sheet_root, ref)
    clear_cell(cell)
    if isinstance(value, (int, float)):
        v = ET.SubElement(cell, q("v"))
        v.text = str(value)
        return
    cell.attrib["t"] = "inlineStr"
    is_node = ET.SubElement(cell, q("is"))
    t_node = ET.SubElement(is_node, q("t"))
    t_node.text = str(value)


def copy_cell_style(sheet_root: ET.Element, source_ref: str, target_ref: str) -> None:
    source_cell = get_cell(sheet_root, source_ref)
    target_cell = ensure_cell(sheet_root, target_ref)
    if source_cell is not None and "s" in source_cell.attrib:
        target_cell.attrib["s"] = source_cell.attrib["s"]
    else:
        target_cell.attrib.pop("s", None)


def copy_row_styles(sheet_root: ET.Element, source_row: int, target_row: int, start_col: int, end_col: int) -> None:
    for col_no in range(start_col, end_col + 1):
        col = col_ref(col_no)
        copy_cell_style(sheet_root, f"{col}{source_row}", f"{col}{target_row}")


def snapshot_styles(sheet_root: ET.Element) -> dict[str, str]:
    styles: dict[str, str] = {}
    for row in get_sheet_data(sheet_root).findall(q("row")):
        for cell in row.findall(q("c")):
            ref = cell.attrib.get("r")
            style = cell.attrib.get("s")
            if ref and style:
                styles[ref] = style
    return styles


def copy_cell_style_from_snapshot(style_map: dict[str, str], sheet_root: ET.Element, source_ref: str, target_ref: str) -> None:
    target_cell = ensure_cell(sheet_root, target_ref)
    if source_ref in style_map:
        target_cell.attrib["s"] = style_map[source_ref]
    else:
        target_cell.attrib.pop("s", None)


def copy_row_styles_from_snapshot(style_map: dict[str, str], sheet_root: ET.Element, source_row: int, target_row: int, start_col: int, end_col: int) -> None:
    for col_no in range(start_col, end_col + 1):
        col = col_ref(col_no)
        copy_cell_style_from_snapshot(style_map, sheet_root, f"{col}{source_row}", f"{col}{target_row}")


def copy_style_block_from_snapshot(style_map: dict[str, str], sheet_root: ET.Element, source_row: int, target_row: int, source_start_col: int, target_start_col: int, width: int) -> None:
    for offset in range(width):
        source_col = col_ref(source_start_col + offset)
        target_col = col_ref(target_start_col + offset)
        copy_cell_style_from_snapshot(style_map, sheet_root, f"{source_col}{source_row}", f"{target_col}{target_row}")


def set_explicit_column_widths(sheet_root: ET.Element, widths: dict[int, float]) -> None:
    cols = sheet_root.find(q("cols"))
    if cols is None:
        cols = ET.Element(q("cols"))
        sheet_data = get_sheet_data(sheet_root)
        children = list(sheet_root)
        sheet_root.insert(children.index(sheet_data), cols)

    existing: dict[int, dict[str, str]] = {}
    max_col = max(widths.keys(), default=0)
    for col in cols.findall(q("col")):
        min_col = int(col.attrib.get("min", "1"))
        max_col_attr = int(col.attrib.get("max", str(min_col)))
        max_col = max(max_col, max_col_attr)
        for col_no in range(min_col, max_col_attr + 1):
            existing[col_no] = {key: value for key, value in col.attrib.items() if key not in {"min", "max"}}

    for col_no, width in widths.items():
        attrs = existing.setdefault(col_no, {})
        attrs["width"] = str(width)
        attrs["customWidth"] = "1"

    for child in list(cols):
        cols.remove(child)

    previous_attrs = None
    start_col = 1
    for col_no in range(1, max_col + 1):
        attrs = existing.get(col_no, {}).copy()
        if previous_attrs is None:
            previous_attrs = attrs
            start_col = col_no
            continue
        if attrs != previous_attrs:
            if previous_attrs:
                ET.SubElement(cols, q("col"), {"min": str(start_col), "max": str(col_no - 1), **previous_attrs})
            start_col = col_no
            previous_attrs = attrs
    if previous_attrs:
        ET.SubElement(cols, q("col"), {"min": str(start_col), "max": str(max_col), **previous_attrs})


def remove_row_cells(sheet_root: ET.Element, row_no: int, start_col: int, end_col: int) -> None:
    sheet_data = get_sheet_data(sheet_root)
    row = sheet_data.find(f"m:row[@r='{row_no}']", NS)
    if row is None:
        return
    for cell in list(row):
        ref = cell.attrib.get("r", "A1")
        _row_no, col_no = cell_sort_key(ref)
        if start_col <= col_no <= end_col:
            row.remove(cell)


def clear_range(sheet_root: ET.Element, start_row: int, end_row: int, start_col: str, end_col: str) -> None:
    start_col_no = col_index(start_col)
    end_col_no = col_index(end_col)
    sheet_data = get_sheet_data(sheet_root)
    for row in sheet_data.findall(q("row")):
        row_no = int(row.attrib.get("r", "0"))
        if row_no < start_row or row_no > end_row:
            continue
        for cell in row.findall(q("c")):
            ref = cell.attrib.get("r", "A1")
            _row_no, col_no = cell_sort_key(ref)
            if start_col_no <= col_no <= end_col_no:
                clear_cell(cell)


def col_index(label: str) -> int:
    value = 0
    for char in label:
        value = value * 26 + (ord(char.upper()) - 64)
    return value


def col_ref(index: int) -> str:
    label = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        label = chr(65 + remainder) + label
    return label


def set_merge_ranges(sheet_root: ET.Element, refs: list[str]) -> None:
    existing = sheet_root.find(q("mergeCells"))
    merge_cells = ET.Element(q("mergeCells"), {"count": str(len(refs))})
    for ref in refs:
        ET.SubElement(merge_cells, q("mergeCell"), {"ref": ref})

    if existing is not None:
        index = list(sheet_root).index(existing)
        sheet_root.remove(existing)
        sheet_root.insert(index, merge_cells)
        return

    children = list(sheet_root)
    before_tags = {
        q("phoneticPr"),
        q("conditionalFormatting"),
        q("dataValidations"),
        q("hyperlinks"),
        q("printOptions"),
        q("pageMargins"),
        q("pageSetup"),
        q("headerFooter"),
        q("drawing"),
        q("legacyDrawing"),
    }
    for index, child in enumerate(children):
        if child.tag in before_tags:
            sheet_root.insert(index, merge_cells)
            return

    sheet_root.append(merge_cells)


def update_dimension(sheet_root: ET.Element) -> None:
    sheet_data = get_sheet_data(sheet_root)
    max_row = 1
    max_col = 1
    for row in sheet_data.findall(q("row")):
        row_no = int(row.attrib.get("r", "1"))
        max_row = max(max_row, row_no)
        for cell in row.findall(q("c")):
            _row, col = cell_sort_key(cell.attrib.get("r", "A1"))
            max_col = max(max_col, col)
    dimension = sheet_root.find(q("dimension"))
    if dimension is not None:
        dimension.attrib["ref"] = f"A1:{col_ref(max_col)}{max_row}"


def set_dimension(sheet_root: ET.Element, max_row: int, max_col: int) -> None:
    dimension = sheet_root.find(q("dimension"))
    if dimension is not None:
        dimension.attrib["ref"] = f"A1:{col_ref(max_col)}{max_row}"


def trim_sheet(sheet_root: ET.Element, max_row: int, max_col: int) -> None:
    sheet_data = get_sheet_data(sheet_root)
    for row in list(sheet_data):
        row_no = int(row.attrib.get("r", "0"))
        if row_no > max_row:
            sheet_data.remove(row)
            continue
        for cell in list(row):
            ref = cell.attrib.get("r", "A1")
            _row_no, col_no = cell_sort_key(ref)
            if col_no > max_col:
                row.remove(cell)
    set_dimension(sheet_root, max_row, max_col)


def serialize_worksheet(sheet_root: ET.Element) -> bytes:
    data = ET.tostring(sheet_root, encoding="utf-8", xml_declaration=True)
    text = data.decode("utf-8")
    if 'mc:Ignorable="x14ac xr xr2 xr3"' in text:
        if 'xmlns:xr2=' not in text:
            text = text.replace('<worksheet ', '<worksheet xmlns:xr2="http://schemas.microsoft.com/office/spreadsheetml/2015/revision2" ', 1)
        if 'xmlns:xr3=' not in text:
            text = text.replace('<worksheet ', '<worksheet xmlns:xr3="http://schemas.microsoft.com/office/spreadsheetml/2016/revision3" ', 1)
    return text.encode("utf-8")


def remove_sheet_protection(sheet_root: ET.Element) -> None:
    protection = sheet_root.find(q("sheetProtection"))
    if protection is not None:
        sheet_root.remove(protection)


def remove_calc_chain(entries: dict[str, bytes]) -> None:
    entries.pop("xl/calcChain.xml", None)

    content_types_name = "[Content_Types].xml"
    if content_types_name in entries:
        root = ET.fromstring(entries[content_types_name])
        overrides = root.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Override")
        for override in overrides:
            if override.attrib.get("PartName") == "/xl/calcChain.xml":
                root.remove(override)
        entries[content_types_name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    rels_name = "xl/_rels/workbook.xml.rels"
    if rels_name in entries:
        rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
        rel_root = ET.fromstring(entries[rels_name])
        for rel in list(rel_root):
            if rel.attrib.get("Target") == "calcChain.xml":
                rel_root.remove(rel)
        entries[rels_name] = ET.tostring(rel_root, encoding="utf-8", xml_declaration=True)


def load_template(template_path: Path) -> tuple[dict[str, bytes], list[ET.Element]]:
    entries: dict[str, bytes] = {}
    sheets: list[ET.Element] = []
    with zipfile.ZipFile(template_path) as zf:
        for name in zf.namelist():
            entries[name] = zf.read(name)
        for idx in range(1, 5):
            sheets.append(ET.fromstring(entries[f"xl/worksheets/sheet{idx}.xml"]))
    return entries, sheets


def adjudicator_pairs(adjudicator_ids: list[str], adjudicators: dict[str, AdjudicatorInfo]) -> tuple[str, str]:
    names = [adjudicator_short(adj.name) for adj_id in adjudicator_ids if (adj := adjudicators.get(adj_id)) is not None]
    if not names:
        return "", ""
    if len(names) == 1:
        return names[0], ""
    if len(names) == 2:
        return names[0], names[1]
    return names[0], ", ".join(names[1:])


def expand_by_weights(values: list[object], weights: list[int], slot_count: int) -> list[object]:
    expanded: list[object] = []
    for value, weight in zip(values, weights):
        for _ in range(weight):
            expanded.append(value)
    while len(expanded) < slot_count:
        expanded.append("")
    return expanded[:slot_count]


def round_slot_counts(rounds: list[str], debates: list[DebateResult]) -> dict[int, int]:
    counts = {seq: 3 for seq in range(1, len(rounds) + 1)}
    for debate in debates:
        if 1 <= debate.round_seq <= len(rounds):
            counts[debate.round_seq] = max(counts[debate.round_seq], sum(debate.weights.values()))
    return counts


def fill_codes_sheet(sheet_root: ET.Element, title: str, subtitle: str, teams: dict[str, TeamInfo], adjudicators: dict[str, AdjudicatorInfo]) -> None:
    style_map = snapshot_styles(sheet_root)
    clear_range(sheet_root, 8, 200, "A", "F")
    set_cell_value(sheet_root, "A8", title)
    set_cell_value(sheet_root, "A9", "")
    set_cell_value(sheet_root, "A11", "Kódy tímov, rozhodcov a rozhodkýň:")
    set_cell_value(sheet_root, "B13", "Tím")
    set_cell_value(sheet_root, "C13", "Rečníci/rečníčky")
    set_cell_value(sheet_root, "E13", "Rozhodcovia/rozhodkyne")

    top_merges = ["A1:F7", "A11:F11", "A12:F12", "B13:B14", "C13:C14", "D13:D14", "E13:F14"]
    data_merges: list[str] = []
    row = 15
    ordinal = 1
    for team in sorted(teams.values(), key=lambda team: team_display(team).lower()):
        speakers = team.speakers or [("", "")]
        start = row
        for index, (_speaker_id, speaker_name) in enumerate(speakers):
            if len(speakers) == 1:
                source_row = 15
            elif index == 0:
                source_row = 15
            elif index == len(speakers) - 1:
                source_row = 17
            else:
                source_row = 16
            copy_row_styles_from_snapshot(style_map, sheet_root, source_row, row, 1, 4)
            if index == 0:
                set_cell_value(sheet_root, f"A{row}", ordinal)
                set_cell_value(sheet_root, f"B{row}", team_display(team))
            set_cell_value(sheet_root, f"C{row}", speaker_name)
            row += 1
        if row - 1 > start:
            data_merges.extend([f"A{start}:A{row-1}", f"B{start}:B{row-1}"])
        ordinal += 1

    adj_row = 15
    for adj_index, adj in enumerate(sorted(adjudicators.values(), key=lambda item: (-(item.score or -1), item.name.lower()))):
        source_row = 15 if adj_index == 0 else 16
        copy_row_styles_from_snapshot(style_map, sheet_root, source_row, adj_row, 5, 6)
        set_cell_value(sheet_root, f"E{adj_row}", adj.name)
        set_cell_value(sheet_root, f"F{adj_row}", format_number(adj.score, 2))
        adj_row += 1

    max_row = max(row - 1, adj_row - 1, 14)
    set_merge_ranges(sheet_root, top_merges + data_merges)
    trim_sheet(sheet_root, max_row, col_index("F"))


def fill_debaty_sheet(sheet_root: ET.Element, title: str, subtitle: str, rounds: list[str], motions: dict[str, str], debates: list[DebateResult], teams: dict[str, TeamInfo], adjudicators: dict[str, AdjudicatorInfo]) -> None:
    style_map = snapshot_styles(sheet_root)
    clear_range(sheet_root, 8, 220, "A", "O")
    set_cell_value(sheet_root, "A8", title)
    set_cell_value(sheet_root, "A9", "")
    set_cell_value(sheet_root, "A11", "Výsledky debát v jednotlivých kolách:")

    debates_by_round: dict[int, list[DebateResult]] = {round_seq: [] for round_seq in range(1, len(rounds) + 1)}
    for debate in sorted(debates, key=lambda item: (item.round_seq, item.debate_id)):
        if debate.round_seq <= len(rounds):
            debates_by_round[debate.round_seq].append(debate)

    max_col = col_index("N") if len(rounds) > 1 else col_index("G")
    merges = [f"A1:{col_ref(max_col)}7", "A9:G9", f"A10:{col_ref(max_col)}10", f"A11:{col_ref(max_col)}11", f"A12:{col_ref(max_col)}12"]
    current_round_row = 13
    max_row = 14

    for group_start in range(0, len(rounds), 2):
        round_numbers = [group_start + 1]
        if group_start + 2 <= len(rounds):
            round_numbers.append(group_start + 2)
        group_debate_count = max((len(debates_by_round[round_no]) for round_no in round_numbers), default=0)
        data_rows = max(group_debate_count, 1)
        header_row = current_round_row + 1
        data_start_row = current_round_row + 2
        prototype_round_row = 13 if group_start == 0 else 32
        prototype_header_row = 14 if group_start == 0 else 33
        prototype_data_row = 15 if group_start == 0 else 34
        copy_row_styles_from_snapshot(style_map, sheet_root, prototype_round_row, current_round_row, 1, max_col)
        copy_row_styles_from_snapshot(style_map, sheet_root, prototype_header_row, header_row, 1, max_col)
        for offset in range(data_rows):
            row_no = data_start_row + offset
            copy_row_styles_from_snapshot(style_map, sheet_root, prototype_data_row, row_no, 1, max_col)
            copy_cell_style_from_snapshot(style_map, sheet_root, f"F{prototype_data_row}", f"G{row_no}")
            if len(round_numbers) == 2:
                copy_cell_style_from_snapshot(style_map, sheet_root, f"M{prototype_data_row}", f"N{row_no}")

        block_specs = [
            {"round_no": round_numbers[0], "round_col": "A", "motion_col": "B", "cols": ["B", "C", "D", "E", "F", "G"]},
        ]
        if len(round_numbers) == 2:
            block_specs.append({"round_no": round_numbers[1], "round_col": "H", "motion_col": "I", "cols": ["I", "J", "K", "L", "M", "N"]})

        for block in block_specs:
            round_no = block["round_no"]
            cols = block["cols"]
            set_cell_value(sheet_root, f"{block['round_col']}{current_round_row}", rounds[round_no - 1])
            motion_text = ""
            if debates_by_round[round_no]:
                motion_text = motions.get(debates_by_round[round_no][0].motion_id, "")
            set_cell_value(sheet_root, f"{block['motion_col']}{current_round_row}", motion_text)

            header_values = ["S", "N", "výsledok", "", "rozhodcovia/rozhodkyne", ""]
            for col, value in zip(cols, header_values):
                set_cell_value(sheet_root, f"{col}{header_row}", value)

            for row_no in range(data_start_row, data_start_row + data_rows):
                for col in cols:
                    set_cell_value(sheet_root, f"{col}{row_no}", "")

            for debate, row_no in zip(debates_by_round[round_no], range(data_start_row, data_start_row + data_rows)):
                if len(debate.sides) != 2:
                    continue
                side_s, side_n = debate.sides
                adj_a, adj_b = adjudicator_pairs(debate.adjudicator_ids, adjudicators)
                values = [
                    team_display(teams[side_s.team_id]),
                    team_display(teams[side_n.team_id]),
                    weighted_ballots_for_side(side_s, debate.weights),
                    weighted_ballots_for_side(side_n, debate.weights),
                    adj_a,
                    adj_b,
                ]
                for col, value in zip(cols, values):
                    set_cell_value(sheet_root, f"{col}{row_no}", value)

            left_col = cols[0]
            right_col = cols[-1]
            result_start = cols[2]
            result_end = cols[3]
            adj_start = cols[4]
            adj_end = cols[5]
            merges.extend([
                f"{left_col}{current_round_row}:{right_col}{current_round_row}",
                f"{result_start}{header_row}:{result_end}{header_row}",
                f"{adj_start}{header_row}:{adj_end}{header_row}",
            ])

        max_row = data_start_row + data_rows - 1
        if group_start + 2 < len(rounds):
            remove_row_cells(sheet_root, max_row + 1, 1, max_col)
        current_round_row = max_row + 2

    set_merge_ranges(sheet_root, merges)
    trim_sheet(sheet_root, max_row, max_col)


def fill_body_sheet(sheet_root: ET.Element, title: str, subtitle: str, rounds: list[str], team_stats: dict[str, TeamStanding], teams: dict[str, TeamInfo], speaker_stats: dict[str, SpeakerStanding]) -> None:
    style_map = snapshot_styles(sheet_root)
    clear_range(sheet_root, 7, 220, "A", "AC")
    set_cell_value(sheet_root, "A7", title)
    set_cell_value(sheet_root, "A8", "")
    set_cell_value(sheet_root, "A10", "Body a rečnícke body:")

    slot_counts = {
        round_seq: max(
            3,
            max(
                (sum(round_data.panel_weights) for row in team_stats.values() if (round_data := row.rounds.get(round_seq)) is not None),
                default=3,
            ),
        )
        for round_seq in range(1, len(rounds) + 1)
    }
    round_blocks: list[dict[str, object]] = []
    current_col = col_index("D")
    for round_seq, round_name in enumerate(rounds, start=1):
        slot_count = slot_counts[round_seq]
        start_col = current_col
        end_col = current_col + 1 + slot_count
        round_blocks.append({
            "round_seq": round_seq,
            "round_name": round_name,
            "start_col": start_col,
            "end_col": end_col,
            "slot_count": slot_count,
        })
        current_col = end_col + 1

    summary_start_col = current_col
    summary_end_col = summary_start_col + 5
    max_col = summary_end_col
    last_col = col_ref(max_col)
    set_explicit_column_widths(sheet_root, {
        summary_start_col: 3.33203125,
        summary_start_col + 1: 3.33203125,
        summary_start_col + 2: 10.6640625,
        summary_start_col + 3: 10.44140625,
        summary_start_col + 4: 10.44140625,
        summary_start_col + 5: 12.5,
    })

    merges = [f"A1:{last_col}6", "A8:G8", f"A9:{last_col}9", f"A10:{last_col}10", f"D11:{last_col}11"]
    set_cell_value(sheet_root, "B13", "Tím")
    set_cell_value(sheet_root, "C13", "Rečník/čka")
    for block in round_blocks:
        start_col = block["start_col"]
        end_col = block["end_col"]
        slot_count = block["slot_count"]
        set_cell_value(sheet_root, f"{col_ref(start_col)}12", block["round_name"])
        set_cell_value(sheet_root, f"{col_ref(start_col)}13", "V")
        set_cell_value(sheet_root, f"{col_ref(start_col + 1)}13", "B")
        set_cell_value(sheet_root, f"{col_ref(start_col + 2)}13", "RB")
        merges.append(f"{col_ref(start_col)}12:{col_ref(end_col)}12")
        if slot_count > 1:
            merges.append(f"{col_ref(start_col + 2)}13:{col_ref(end_col)}13")
        for col_no in range(start_col + 3, start_col + 2 + slot_count):
            set_cell_value(sheet_root, f"{col_ref(col_no)}13", "")

    set_cell_value(sheet_root, f"{col_ref(summary_start_col)}12", "Spolu")
    for offset, value in enumerate(["V", "B", "RB – tím", "RB - indiv", "RB-min/max", "standardná odchýlka"]):
        set_cell_value(sheet_root, f"{col_ref(summary_start_col + offset)}13", value)
    merges.append(f"{col_ref(summary_start_col)}12:{col_ref(summary_end_col)}12")
    copy_style_block_from_snapshot(style_map, sheet_root, 12, 12, col_index("X"), summary_start_col, 6)
    copy_style_block_from_snapshot(style_map, sheet_root, 13, 13, col_index("X"), summary_start_col, 6)

    sorted_teams = sorted(team_stats.values(), key=lambda row: (-row.wins, -row.ballots, -row.total_points, row.team_name.lower()))
    team_rank_rows = [{"team_id": row.team_id, "wins": row.wins, "ballots": row.ballots, "points": round(row.total_points, 6)} for row in sorted_teams]
    previous = None
    rank = 0
    for index, row in enumerate(team_rank_rows, start=1):
        key = (row["wins"], row["ballots"], row["points"])
        if key != previous:
            rank = index
            previous = key
        row["rank"] = rank
    ranks = {row["team_id"]: row["rank"] for row in team_rank_rows}

    start_row = 14
    current_row = start_row
    for team_index, team_row in enumerate(sorted_teams):
        base_row = current_row
        team = teams[team_row.team_id]
        speakers = team.speakers
        has_cross = any(any(score is not None for score in round_data.cross_panel_scores) for round_data in team_row.rounds.values())
        has_reply = any(any(score is not None for score in round_data.reply_panel_scores) for round_data in team_row.rounds.values())
        block_height = 1 + len(speakers) + (1 if has_cross else 0) + (1 if has_reply else 0)
        block_end_row = base_row + block_height - 1
        base_source_row = 14 if team_index == 0 else 20
        copy_row_styles_from_snapshot(style_map, sheet_root, base_source_row, base_row, 1, max_col)
        copy_style_block_from_snapshot(style_map, sheet_root, base_source_row, base_row, col_index("X"), summary_start_col, 6)
        for speaker_offset, _speaker in enumerate(speakers, start=1):
            source_row = 15 + min(speaker_offset - 1, 2)
            copy_row_styles_from_snapshot(style_map, sheet_root, source_row, base_row + speaker_offset, 1, max_col)
            copy_style_block_from_snapshot(style_map, sheet_root, source_row, base_row + speaker_offset, col_index("X"), summary_start_col, 6)
        next_row = base_row + 1 + len(speakers)
        if has_cross:
            copy_row_styles_from_snapshot(style_map, sheet_root, 18, next_row, 1, max_col)
            copy_style_block_from_snapshot(style_map, sheet_root, 18, next_row, col_index("X"), summary_start_col, 6)
            next_row += 1
        if has_reply:
            copy_row_styles_from_snapshot(style_map, sheet_root, 19, next_row, 1, max_col)
            copy_style_block_from_snapshot(style_map, sheet_root, 19, next_row, col_index("X"), summary_start_col, 6)
        set_cell_value(sheet_root, f"A{base_row}", ranks[team.team_id])
        set_cell_value(sheet_root, f"B{base_row}", team_display(team))
        set_cell_value(sheet_root, f"C{base_row}", "Rozh. panel")
        if block_height > 1:
            merges.extend([f"A{base_row}:A{block_end_row}", f"B{base_row}:B{block_end_row}"])

        for block in round_blocks:
            round_seq = block["round_seq"]
            start_col = block["start_col"]
            slot_count = block["slot_count"]
            cols = [col_ref(col_no) for col_no in range(start_col, block["end_col"] + 1)]
            round_data = team_row.rounds.get(round_seq)
            if round_data is None or not round_data.debated:
                for col in cols:
                    set_cell_value(sheet_root, f"{col}{base_row}", "")
                for offset in range(1, block_height):
                    for col in cols:
                        set_cell_value(sheet_root, f"{col}{base_row + offset}", "")
                continue

            expanded_names = expand_by_weights(round_data.adjudicator_names, round_data.panel_weights, slot_count)
            summary_values = [round_data.win, round_data.ballots] + expanded_names
            for col, value in zip(cols, summary_values):
                set_cell_value(sheet_root, f"{col}{base_row}", value)

            for speaker_offset, (speaker_id, speaker_name) in enumerate(speakers, start=1):
                row_no = base_row + speaker_offset
                set_cell_value(sheet_root, f"C{row_no}", speaker_name)
                scores = round_data.speaker_panel_scores.get(speaker_id, [])
                expanded_scores = expand_by_weights(scores, round_data.panel_weights, slot_count)
                for col, value in zip(cols[2:], expanded_scores):
                    set_cell_value(sheet_root, f"{col}{row_no}", format_number(value))

            next_row = base_row + 1 + len(speakers)
            cross_row = next_row if has_cross else None
            if cross_row is not None and any(score is not None for score in round_data.cross_panel_scores):
                set_cell_value(sheet_root, f"C{cross_row}", "Krížové výsluchy")
                expanded_scores = expand_by_weights(round_data.cross_panel_scores, round_data.panel_weights, slot_count)
                for col, value in zip(cols[2:], expanded_scores):
                    set_cell_value(sheet_root, f"{col}{cross_row}", format_number(value))
            elif cross_row is not None:
                set_cell_value(sheet_root, f"C{cross_row}", "")
                for col in cols:
                    set_cell_value(sheet_root, f"{col}{cross_row}", "")

            reply_row = next_row + (1 if has_cross else 0) if has_reply else None
            if reply_row is not None:
                set_cell_value(sheet_root, f"C{reply_row}", "Záverečná reč")
                expanded_scores = expand_by_weights(round_data.reply_panel_scores, round_data.panel_weights, slot_count)
                for col, value in zip(cols[2:], expanded_scores):
                    set_cell_value(sheet_root, f"{col}{reply_row}", format_number(value))

        set_cell_value(sheet_root, f"{col_ref(summary_start_col)}{base_row}", team_row.wins)
        set_cell_value(sheet_root, f"{col_ref(summary_start_col + 1)}{base_row}", team_row.ballots)
        set_cell_value(sheet_root, f"{col_ref(summary_start_col + 2)}{base_row}", format_number(team_row.total_points))
        if block_height > 1:
            merges.extend([
                f"{col_ref(summary_start_col)}{base_row}:{col_ref(summary_start_col)}{block_end_row}",
                f"{col_ref(summary_start_col + 1)}{base_row}:{col_ref(summary_start_col + 1)}{block_end_row}",
                f"{col_ref(summary_start_col + 2)}{base_row}:{col_ref(summary_start_col + 2)}{block_end_row}",
            ])

        for speaker_offset, (speaker_id, _speaker_name) in enumerate(speakers, start=1):
            row_no = base_row + speaker_offset
            speaker_entry = speaker_stats.get(speaker_id)
            if speaker_entry is not None:
                set_cell_value(sheet_root, f"{col_ref(summary_start_col + 3)}{row_no}", format_number(speaker_entry.total_points))
                set_cell_value(sheet_root, f"{col_ref(summary_start_col + 4)}{row_no}", format_number(trimmed_total(speaker_entry.round_totals)))
                set_cell_value(sheet_root, f"{col_ref(summary_start_col + 5)}{row_no}", format_number(safe_stdev(speaker_entry.round_averages)))

        cross_total = 0.0
        reply_total = 0.0
        for round_data in team_row.rounds.values():
            for score, weight in zip(round_data.cross_panel_scores, round_data.panel_weights):
                if score is not None:
                    cross_total += score * weight
            weighted_total = 0.0
            for score, weight in zip(round_data.reply_panel_scores, round_data.panel_weights):
                if score is None:
                    continue
                weighted_total += score * weight
            reply_total += weighted_total
        cross_row = base_row + 1 + len(speakers) if has_cross else None
        reply_row = base_row + 1 + len(speakers) + (1 if has_cross else 0) if has_reply else None
        if cross_total and cross_row is not None:
            set_cell_value(sheet_root, f"{col_ref(summary_start_col + 3)}{cross_row}", format_number(cross_total))
        if reply_row is not None:
            set_cell_value(sheet_root, f"{col_ref(summary_start_col + 3)}{reply_row}", format_number(reply_total))
        current_row = block_end_row + 1

    max_row = max(current_row - 1, start_row)
    set_merge_ranges(sheet_root, merges)
    trim_sheet(sheet_root, max_row, max_col)


def fill_results_sheet(sheet_root: ET.Element, title: str, subtitle: str, team_stats: dict[str, TeamStanding], speaker_stats: dict[str, SpeakerStanding]) -> None:
    clear_range(sheet_root, 8, 220, "A", "K")
    set_cell_value(sheet_root, "A8", title)
    set_cell_value(sheet_root, "A9", "")
    set_cell_value(sheet_root, "A11", "Konečné poradie tímov a rečníkov/rečníčok:")
    set_cell_value(sheet_root, "A13", "Poradie tímov")
    set_cell_value(sheet_root, "G13", "Poradie rečníkov/rečníčok")
    for cell, value in {
        "A14": "Miesto",
        "B14": "Tím",
        "C14": "V",
        "D14": "B",
        "E14": "RB",
        "G14": "Miesto",
        "H14": "Rečník/rečníčka",
        "I14": "Body",
        "J14": "Priemer",
        "K14": "B-MIN/MAX",
    }.items():
        set_cell_value(sheet_root, cell, value)

    sorted_teams = sorted(team_stats.values(), key=lambda row: (-row.wins, -row.ballots, -row.total_points, row.team_name.lower()))
    team_rank_rows = [{"team_id": row.team_id, "wins": row.wins, "ballots": row.ballots, "points": round(row.total_points, 6)} for row in sorted_teams]
    previous = None
    rank = 0
    for index, row in enumerate(team_rank_rows, start=1):
        key = (row["wins"], row["ballots"], row["points"])
        if key != previous:
            rank = index
            previous = key
        row["rank"] = rank
    team_ranks = {row["team_id"]: row["rank"] for row in team_rank_rows}

    sorted_speakers = sorted(speaker_stats.values(), key=lambda row: (-(row.total_points / row.weighted_ballot_count if row.weighted_ballot_count else 0), -row.total_points, row.team_name.lower(), row.speaker_name.lower()))
    speaker_rank_rows = [{"speaker_id": row.speaker_id, "avg": round(row.total_points / row.weighted_ballot_count if row.weighted_ballot_count else 0, 6), "points": round(row.total_points, 6)} for row in sorted_speakers]
    previous = None
    rank = 0
    for index, row in enumerate(speaker_rank_rows, start=1):
        key = (row["avg"], row["points"])
        if key != previous:
            rank = index
            previous = key
        row["rank"] = rank
    speaker_ranks = {row["speaker_id"]: row["rank"] for row in speaker_rank_rows}

    for index in range(max(len(sorted_teams), len(sorted_speakers))):
        row_no = 15 + index
        if index < len(sorted_teams):
            team = sorted_teams[index]
            set_cell_value(sheet_root, f"A{row_no}", team_ranks[team.team_id])
            set_cell_value(sheet_root, f"B{row_no}", team.team_name)
            set_cell_value(sheet_root, f"C{row_no}", team.wins)
            set_cell_value(sheet_root, f"D{row_no}", team.ballots)
            set_cell_value(sheet_root, f"E{row_no}", format_number(team.total_points))
        if index < len(sorted_speakers):
            speaker = sorted_speakers[index]
            set_cell_value(sheet_root, f"G{row_no}", speaker_ranks[speaker.speaker_id])
            set_cell_value(sheet_root, f"H{row_no}", speaker.speaker_name)
            set_cell_value(sheet_root, f"I{row_no}", format_number(speaker.total_points))
            set_cell_value(sheet_root, f"J{row_no}", format_number(speaker.total_points / speaker.weighted_ballot_count if speaker.weighted_ballot_count else 0))
            set_cell_value(sheet_root, f"K{row_no}", format_number(trimmed_total(speaker.round_totals)))

    max_row = 14 + max(len(sorted_teams), len(sorted_speakers), 1)
    set_merge_ranges(sheet_root, ["A1:K7", "A9:G9", "A11:J11", "A12:D12", "A13:E13", "G13:K13"])
    trim_sheet(sheet_root, max_row, col_index("K"))


def build_workbook_bytes(template_path: Path, title: str, subtitle: str, rounds: list[str], teams: dict[str, TeamInfo], adjudicators: dict[str, AdjudicatorInfo], motions: dict[str, str], debates: list[DebateResult], team_stats: dict[str, TeamStanding], speaker_stats: dict[str, SpeakerStanding]) -> bytes:
    entries, sheets = load_template(template_path)
    remove_calc_chain(entries)
    fill_codes_sheet(sheets[0], title, subtitle, teams, adjudicators)
    fill_debaty_sheet(sheets[1], title, subtitle, rounds, motions, debates, teams, adjudicators)
    fill_body_sheet(sheets[2], title, subtitle, rounds, team_stats, teams, speaker_stats)
    fill_results_sheet(sheets[3], title, subtitle, team_stats, speaker_stats)
    for sheet in sheets:
        remove_sheet_protection(sheet)

    output = BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            if name.startswith('xl/worksheets/sheet') and name.endswith('.xml') and '/_rels/' not in name:
                idx = int(name.rsplit('sheet', 1)[1].split('.xml')[0])
                if 1 <= idx <= 4:
                    zf.writestr(name, serialize_worksheet(sheets[idx - 1]))
                    continue
            zf.writestr(name, data)
    return output.getvalue()


def write_from_template(template_path: Path, output_path: Path, title: str, subtitle: str, rounds: list[str], teams: dict[str, TeamInfo], adjudicators: dict[str, AdjudicatorInfo], motions: dict[str, str], debates: list[DebateResult], team_stats: dict[str, TeamStanding], speaker_stats: dict[str, SpeakerStanding]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(build_workbook_bytes(
        template_path, title, subtitle, rounds, teams, adjudicators,
        motions, debates, team_stats, speaker_stats,
    ))


def convert_debatexml_to_xlsx_bytes(xml_source, source_name: str | None = None, template_path: Path = DEFAULT_TEMPLATE_PATH) -> bytes:
    tournament_name, tournament_short, rounds, teams, adjudicators, _venues, motions, debates = parse_debatexml(
        xml_source, source_name=source_name)
    team_stats, speaker_stats, _max_adj_count = build_aggregates(teams, adjudicators, debates)
    title = f"Výsledky {tournament_name}"
    subtitle = f"Zdroj: DebateXML export {tournament_short}"
    return build_workbook_bytes(
        template_path, title, subtitle, rounds, teams, adjudicators,
        motions, debates, team_stats, speaker_stats,
    )


def main() -> None:
    args = parse_args()
    xml_path = args.xml_path.resolve()
    template_path = args.template.resolve()
    output_path = build_output_path(xml_path, args.output.resolve() if args.output else None)
    if output_path.suffix.lower() != '.xlsx':
        output_path = output_path.with_suffix('.xlsx')

    tournament_name, tournament_short, rounds, teams, adjudicators, _venues, motions, debates = parse_debatexml(xml_path)
    team_stats, speaker_stats, _max_adj_count = build_aggregates(teams, adjudicators, debates)
    title = f"Výsledky {tournament_name}"
    subtitle = f"Zdroj: DebateXML export {tournament_short}"
    write_from_template(template_path, output_path, title, subtitle, rounds, teams, adjudicators, motions, debates, team_stats, speaker_stats)
    print(f"Wrote {output_path}")


if __name__ == '__main__':
    main()

from __future__ import annotations

import argparse
import math
import re
import unicodedata
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import pstdev
from typing import BinaryIO, Iterable
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


@dataclass
class TeamInfo:
    team_id: str
    name: str
    code: str
    speakers: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class AdjudicatorInfo:
    adjudicator_id: str
    name: str
    score: float | None


@dataclass
class BallotEntry:
    adjudicator_id: str
    total: float
    rank: int | None
    ignored: bool
    minority: bool


@dataclass
class SpeechEntry:
    speaker_id: str
    reply: bool
    scores_by_adj: dict[str, float]


@dataclass
class CrossEntry:
    scores_by_adj: dict[str, float]


@dataclass
class SideResult:
    team_id: str
    ballots_by_adj: dict[str, BallotEntry]
    speeches: list[SpeechEntry]
    crosses: list[CrossEntry] = field(default_factory=list)


@dataclass
class DebateResult:
    round_seq: int
    round_name: str
    debate_id: str
    venue_id: str
    motion_id: str
    adjudicator_ids: list[str]
    chair_id: str
    weights: dict[str, int]
    sides: list[SideResult]
    winner_team_id: str | None
    split: bool


@dataclass
class TeamRoundData:
    debated: bool = False
    win: int = 0
    ballots: int = 0
    weighted_team_total: float = 0.0
    team_average: float | None = None
    adjudicator_names: list[str] = field(default_factory=list)
    panel_weights: list[int] = field(default_factory=list)
    speaker_panel_scores: dict[str, list[float | None]] = field(default_factory=dict)
    cross_panel_scores: list[float | None] = field(default_factory=list)
    reply_panel_scores: list[float | None] = field(default_factory=list)


@dataclass
class TeamStanding:
    team_id: str
    team_name: str
    wins: int = 0
    ballots: int = 0
    total_points: float = 0.0
    weighted_ballot_count: int = 0
    round_totals: list[float] = field(default_factory=list)
    round_averages: list[float] = field(default_factory=list)
    rounds: dict[int, TeamRoundData] = field(default_factory=dict)


@dataclass
class SpeakerStanding:
    speaker_id: str
    speaker_name: str
    team_id: str
    team_name: str
    total_points: float = 0.0
    weighted_ballot_count: int = 0
    speech_count: int = 0
    round_totals: list[float] = field(default_factory=list)
    round_averages: list[float] = field(default_factory=list)


@dataclass
class SheetSpec:
    name: str
    rows: list[list[object]]
    widths: list[float] = field(default_factory=list)
    merges: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Tabbycat DebateXML export to a workbook similar to SDA result sheets.")
    parser.add_argument("xml_path", type=Path, help="Path to the Tabbycat DebateXML export")
    parser.add_argument("-o", "--output", type=Path, help="Optional output .xlsx path")
    return parser.parse_args()


def as_float(text: str | None) -> float:
    if text is None:
        return 0.0
    stripped = text.strip()
    return float(stripped) if stripped else 0.0


def is_reply(value: str | None) -> bool:
    return (value or "").strip().lower() == "true"


def format_number(value: float | int | None, digits: int = 2) -> float | int | str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    if math.isclose(value, round(value), abs_tol=1e-9):
        return int(round(value))
    return round(value, digits)


def team_display(team: TeamInfo) -> str:
    return team.name or team.code or team.team_id


def adjudicator_short(name: str) -> str:
    if not name:
        return ""
    surname = name.split()[-1]
    ascii_name = unicodedata.normalize("NFKD", surname).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9-]", "", ascii_name.lower())


def adjudicator_can_vote(adjudicator: AdjudicatorInfo | None) -> bool:
    if adjudicator is None or adjudicator.score is None:
        return True
    return adjudicator.score > 0


def build_output_path(xml_path: Path, output_path: Path | None) -> Path:
    if output_path is not None:
        return output_path
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{xml_path.stem}_converted.xlsx"


def panel_weights(adjudicator_ids: list[str], chair_id: str) -> dict[str, int]:
    if not adjudicator_ids:
        return {}
    if len(adjudicator_ids) == 1:
        return {adjudicator_ids[0]: 3}
    if len(adjudicator_ids) == 2:
        weights = {adj_id: 1 for adj_id in adjudicator_ids}
        weights[chair_id or adjudicator_ids[0]] = 2
        return weights
    return {adj_id: 1 for adj_id in adjudicator_ids}


def weighted_ballots_for_side(side: SideResult, weights: dict[str, int]) -> int:
    return sum(
        weights.get(adj_id, 1)
        for adj_id, ballot in side.ballots_by_adj.items()
        if ballot.rank == 1
    )


def expand_by_weights(values: list[object], weights: list[int], slot_count: int) -> list[object]:
    expanded: list[object] = []
    for value, weight in zip(values, weights):
        expanded.extend([value] * weight)
    while len(expanded) < slot_count:
        expanded.append("")
    return expanded[:slot_count]


ROMAN_NUMERALS = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI",
    7: "VII", 8: "VIII", 9: "IX", 10: "X",
}


def display_round_name(round_name: str, round_seq: int) -> str:
    match = re.fullmatch(r"\s*(?:round|r)\s*(\d+)\s*", round_name or "", re.IGNORECASE)
    if match:
        number = int(match.group(1))
        return f"{ROMAN_NUMERALS.get(number, str(number))}. kolo"
    if round_name:
        return round_name
    return f"{ROMAN_NUMERALS.get(round_seq, str(round_seq))}. kolo"


def average_or_none(total: float, count: int) -> float | None:
    if count <= 0:
        return None
    return total / count


def trimmed_total(values: Iterable[float]) -> float | None:
    items = [value for value in values if value is not None]
    if not items:
        return None
    if len(items) <= 2:
        return float(sum(items))
    sorted_items = sorted(items)
    return float(sum(sorted_items[1:-1]))


def safe_stdev(values: Iterable[float]) -> float | None:
    items = [value for value in values if value is not None]
    if len(items) <= 1:
        return None
    return float(pstdev(items))


def rank_rows(rows: list[dict], key_names: tuple[str, ...]) -> None:
    previous_key = None
    current_rank = 0
    for index, row in enumerate(rows, start=1):
        current_key = tuple(row[name] for name in key_names)
        if current_key != previous_key:
            current_rank = index
            previous_key = current_key
        row["rank"] = current_rank


def source_stem(xml_source: Path | str | BinaryIO, source_name: str | None = None) -> str:
    if source_name:
        return Path(source_name).stem
    if isinstance(xml_source, (str, Path)):
        return Path(xml_source).stem
    name = getattr(xml_source, "name", None)
    if name:
        return Path(name).stem
    return "DebateXML"


def parse_debatexml(xml_source: Path | str | BinaryIO, source_name: str | None = None) -> tuple[str, str, list[str], dict[str, TeamInfo], dict[str, AdjudicatorInfo], dict[str, str], dict[str, str], list[DebateResult]]:
    root = ET.parse(xml_source).getroot()
    fallback_name = source_stem(xml_source, source_name)
    tournament_name = root.attrib.get("name", fallback_name)
    tournament_short = root.attrib.get("short", fallback_name)

    teams: dict[str, TeamInfo] = {}
    adjudicators: dict[str, AdjudicatorInfo] = {}
    venues: dict[str, str] = {}
    motions: dict[str, str] = {}

    participants = root.find("participants")
    if participants is not None:
        for node in participants:
            if node.tag == "team":
                teams[node.attrib["id"]] = TeamInfo(
                    team_id=node.attrib["id"],
                    name=node.attrib.get("name", ""),
                    code=node.attrib.get("code", ""),
                    speakers=[(speaker.attrib["id"], (speaker.text or "").strip()) for speaker in node.findall("speaker")],
                )
            elif node.tag == "adjudicator":
                score_value = node.attrib.get("score")
                adjudicators[node.attrib["id"]] = AdjudicatorInfo(
                    adjudicator_id=node.attrib["id"],
                    name=node.attrib.get("name", ""),
                    score=float(score_value) if score_value not in (None, "") else None,
                )

    for venue in root.findall("venue"):
        venues[venue.attrib["id"]] = venue.attrib.get("name", venue.attrib["id"])

    for motion in root.findall("motion"):
        text = (motion.text or "").strip()
        reference = motion.attrib.get("reference", "")
        motions[motion.attrib["id"]] = f"{reference}: {text}".strip(": ") if reference or text else motion.attrib["id"]

    rounds: list[str] = []
    debates: list[DebateResult] = []
    round_seq = 0
    for round_node in root.findall("round"):
        if round_node.attrib.get("elimination", "false").lower() == "true":
            continue
        round_seq += 1
        round_name = display_round_name(round_node.attrib.get("name", ""), round_seq)
        rounds.append(round_name)
        for debate_node in round_node.findall("debate"):
            raw_adjudicator_ids = debate_node.attrib.get("adjudicators", "").split()
            adjudicator_ids = [
                adjudicator_id for adjudicator_id in raw_adjudicator_ids
                if adjudicator_can_vote(adjudicators.get(adjudicator_id))
            ]
            if not adjudicator_ids:
                adjudicator_ids = raw_adjudicator_ids[:]
            raw_chair_id = debate_node.attrib.get("chair", raw_adjudicator_ids[0] if raw_adjudicator_ids else "")
            chair_id = raw_chair_id if raw_chair_id in adjudicator_ids else (adjudicator_ids[0] if adjudicator_ids else "")
            weights = panel_weights(adjudicator_ids, chair_id)
            voting_adjudicator_ids = set(adjudicator_ids)
            winners_by_adj: dict[str, str] = {}
            official_ballots: dict[str, int] = defaultdict(int)
            sides: list[SideResult] = []

            for side_node in debate_node.findall("side"):
                ballots_by_adj: dict[str, BallotEntry] = {}
                speeches: list[SpeechEntry] = []
                crosses: list[CrossEntry] = []
                team_id = side_node.attrib["team"]
                for child in side_node:
                    if child.tag == "ballot":
                        adj_ids = child.attrib.get("adjudicators", "").split()
                        if not adj_ids:
                            continue
                        adjudicator_id = adj_ids[0]
                        if adjudicator_id not in voting_adjudicator_ids:
                            continue
                        rank = int(child.attrib["rank"]) if child.attrib.get("rank") else None
                        ballot = BallotEntry(
                            adjudicator_id=adjudicator_id,
                            total=as_float(child.text),
                            rank=rank,
                            ignored=child.attrib.get("ignored", "false").lower() == "true",
                            minority=child.attrib.get("minority", "false").lower() == "true",
                        )
                        ballots_by_adj[adjudicator_id] = ballot
                        if rank == 1:
                            winners_by_adj[adjudicator_id] = team_id
                    elif child.tag == "speech":
                        scores_by_adj: dict[str, float] = {}
                        for ballot_node in child.findall("ballot"):
                            adj_ids = ballot_node.attrib.get("adjudicators", "").split()
                            if adj_ids and adj_ids[0] in voting_adjudicator_ids:
                                scores_by_adj[adj_ids[0]] = as_float(ballot_node.text)
                        speeches.append(SpeechEntry(
                            speaker_id=child.attrib.get("speaker", ""),
                            reply=is_reply(child.attrib.get("reply")),
                            scores_by_adj=scores_by_adj,
                        ))
                    elif child.tag == "cross":
                        scores_by_adj: dict[str, float] = {}
                        for ballot_node in child.findall("ballot"):
                            adj_ids = ballot_node.attrib.get("adjudicators", "").split()
                            if adj_ids and adj_ids[0] in voting_adjudicator_ids:
                                scores_by_adj[adj_ids[0]] = as_float(ballot_node.text)
                        crosses.append(CrossEntry(scores_by_adj=scores_by_adj))
                side = SideResult(team_id=team_id, ballots_by_adj=ballots_by_adj, speeches=speeches, crosses=crosses)
                official_ballots[team_id] = weighted_ballots_for_side(side, weights)
                sides.append(side)

            winner_team_id = None
            ordered = sorted(((official_ballots.get(side.team_id, 0), side.team_id) for side in sides), reverse=True)
            if ordered:
                if len(ordered) == 1 or ordered[0][0] > ordered[1][0]:
                    winner_team_id = ordered[0][1]
                elif chair_id and chair_id in winners_by_adj:
                    winner_team_id = winners_by_adj[chair_id]

            debates.append(DebateResult(
                round_seq=round_seq,
                round_name=round_name,
                debate_id=debate_node.attrib.get("id", f"D{round_seq}"),
                venue_id=debate_node.attrib.get("venue", ""),
                motion_id=debate_node.attrib.get("motion", ""),
                adjudicator_ids=adjudicator_ids,
                chair_id=chair_id,
                weights=weights,
                sides=sides,
                winner_team_id=winner_team_id,
                split=len(set(winners_by_adj.values())) > 1,
            ))

    return tournament_name, tournament_short, rounds, teams, adjudicators, venues, motions, debates


def build_aggregates(
    teams: dict[str, TeamInfo],
    adjudicators: dict[str, AdjudicatorInfo],
    debates: list[DebateResult],
) -> tuple[dict[str, TeamStanding], dict[str, SpeakerStanding], int]:
    team_stats: dict[str, TeamStanding] = {
        team_id: TeamStanding(team_id=team_id, team_name=team_display(team))
        for team_id, team in teams.items()
    }
    speaker_stats: dict[str, SpeakerStanding] = {}
    max_adj_count = 0

    for debate in debates:
        max_adj_count = max(max_adj_count, len(debate.adjudicator_ids))
        weight_total = sum(debate.weights.get(adj_id, 1) for adj_id in debate.adjudicator_ids)
        display_adjudicator_ids = []
        if debate.chair_id:
            display_adjudicator_ids.append(debate.chair_id)
        display_adjudicator_ids.extend(adj_id for adj_id in debate.adjudicator_ids if adj_id != debate.chair_id)
        adjudicator_names = [adjudicator_short(adjudicators.get(adj_id, AdjudicatorInfo(adj_id, adj_id, None)).name) for adj_id in display_adjudicator_ids]
        panel_weights = [debate.weights.get(adj_id, 1) for adj_id in display_adjudicator_ids]

        for side in debate.sides:
            standing = team_stats[side.team_id]
            round_data = TeamRoundData(
                debated=True,
                win=1 if debate.winner_team_id == side.team_id else 0,
                ballots=weighted_ballots_for_side(side, debate.weights),
                weighted_team_total=sum(ballot.total * debate.weights.get(adj_id, 1) for adj_id, ballot in side.ballots_by_adj.items()),
                adjudicator_names=adjudicator_names[:],
                panel_weights=panel_weights[:],
                speaker_panel_scores={},
                cross_panel_scores=[None for _ in debate.adjudicator_ids],
                reply_panel_scores=[None for _ in debate.adjudicator_ids],
            )
            round_data.team_average = average_or_none(round_data.weighted_team_total, weight_total)
            standing.rounds[debate.round_seq] = round_data
            standing.wins += round_data.win
            standing.ballots += round_data.ballots
            standing.total_points += round_data.weighted_team_total
            standing.weighted_ballot_count += weight_total
            if round_data.weighted_team_total:
                standing.round_totals.append(round_data.weighted_team_total)
            if round_data.team_average is not None:
                standing.round_averages.append(round_data.team_average)

            speaker_panel_accumulator: dict[str, list[float | None]] = {}
            speaker_weighted_round_totals: dict[str, float] = defaultdict(float)
            speaker_weighted_round_counts: dict[str, int] = defaultdict(int)

            cross_totals = [0.0 for _ in display_adjudicator_ids]
            cross_seen = [False for _ in display_adjudicator_ids]
            for cross in side.crosses:
                for index, adj_id in enumerate(display_adjudicator_ids):
                    score = cross.scores_by_adj.get(adj_id)
                    if score is None:
                        continue
                    cross_totals[index] += score
                    cross_seen[index] = True
            round_data.cross_panel_scores = [
                total if seen else None for total, seen in zip(cross_totals, cross_seen)
            ]

            for speech in side.speeches:
                ordered_scores = [speech.scores_by_adj.get(adj_id) for adj_id in display_adjudicator_ids]
                if speech.reply:
                    round_data.reply_panel_scores = ordered_scores
                    continue

                speaker_panel_accumulator.setdefault(speech.speaker_id, [0.0 for _ in display_adjudicator_ids])
                for index, adj_id in enumerate(display_adjudicator_ids):
                    score = speech.scores_by_adj.get(adj_id)
                    if score is None:
                        continue
                    speaker_panel_accumulator[speech.speaker_id][index] = (speaker_panel_accumulator[speech.speaker_id][index] or 0.0) + score
                    speaker_weighted_round_totals[speech.speaker_id] += score * debate.weights.get(adj_id, 1)
                    speaker_weighted_round_counts[speech.speaker_id] += debate.weights.get(adj_id, 1)

                speaker_name = next((name for spk_id, name in teams[side.team_id].speakers if spk_id == speech.speaker_id), speech.speaker_id)
                speaker_entry = speaker_stats.setdefault(
                    speech.speaker_id,
                    SpeakerStanding(
                        speaker_id=speech.speaker_id,
                        speaker_name=speaker_name,
                        team_id=side.team_id,
                        team_name=team_display(teams[side.team_id]),
                    ),
                )
                speaker_entry.speech_count += 1
                for adj_id, score in speech.scores_by_adj.items():
                    speaker_entry.total_points += score * debate.weights.get(adj_id, 1)
                    speaker_entry.weighted_ballot_count += debate.weights.get(adj_id, 1)

            for speaker_id, panel_scores in speaker_panel_accumulator.items():
                round_data.speaker_panel_scores[speaker_id] = panel_scores
                speaker_entry = speaker_stats[speaker_id]
                round_total = speaker_weighted_round_totals[speaker_id]
                round_average = average_or_none(round_total, speaker_weighted_round_counts[speaker_id])
                speaker_entry.round_totals.append(round_total)
                if round_average is not None:
                    speaker_entry.round_averages.append(round_average)

    return team_stats, speaker_stats, max_adj_count


def build_title_rows(title: str, subtitle: str) -> list[list[object]]:
    rows = [[] for _ in range(7)]
    rows.append([title])
    rows.append([subtitle])
    rows.append([])
    return rows


def build_codes_sheet(tournament_name: str, tournament_short: str, teams: dict[str, TeamInfo], adjudicators: dict[str, AdjudicatorInfo]) -> SheetSpec:
    rows = build_title_rows(f"Výsledky {tournament_name}", f"Zdroj: DebateXML export {tournament_short}")
    rows.append(["Kódy tímov, rozhodcov a rozhodkýň:"])
    rows.append([])
    rows.append(["", "Tím", "Rečníci/rečníčky", "", "Rozhodcovia/rozhodkyne", "Akreditácia"])

    merges: list[str] = ["A8:F8", "A11:F11"]
    team_items = sorted(teams.values(), key=lambda team: team_display(team).lower())
    adjudicator_items = sorted(adjudicators.values(), key=lambda adj: adj.name.lower())
    max_len = max(sum(max(len(team.speakers), 1) for team in team_items), len(adjudicator_items))

    current_row = 14
    team_pointer = 0
    team_remaining_rows: list[list[object]] = []
    left_rows: list[list[object]] = []
    left_meta: list[tuple[int, int]] = []
    ordinal = 1
    for team in team_items:
        start = current_row
        speakers = team.speakers or [("", "")]
        for index, (_speaker_id, speaker_name) in enumerate(speakers):
            left_rows.append([
                ordinal if index == 0 else "",
                team_display(team) if index == 0 else "",
                speaker_name,
                "",
            ])
            current_row += 1
        if len(speakers) > 1:
            left_meta.append((start, current_row - 1))
        ordinal += 1

    while len(left_rows) < len(adjudicator_items):
        left_rows.append(["", "", "", ""])

    final_rows = rows[:]
    for index in range(max(len(left_rows), len(adjudicator_items))):
        left = left_rows[index] if index < len(left_rows) else ["", "", "", ""]
        if index < len(adjudicator_items):
            adj = adjudicator_items[index]
            final_rows.append(left + [adj.name, format_number(adj.score, 2)])
        else:
            final_rows.append(left + ["", ""])

    for start, end in left_meta:
        merges.append(f"A{start}:A{end}")
        merges.append(f"B{start}:B{end}")

    widths = [4.5, 24.0, 30.0, 4.0, 28.0, 11.0]
    return SheetSpec(name="kódy", rows=final_rows, widths=widths, merges=merges)


def build_debaty_sheet(
    tournament_name: str,
    tournament_short: str,
    rounds: list[str],
    teams: dict[str, TeamInfo],
    adjudicators: dict[str, AdjudicatorInfo],
    venues: dict[str, str],
    motions: dict[str, str],
    debates: list[DebateResult],
) -> SheetSpec:
    rows = build_title_rows(f"Výsledky {tournament_name}", f"Zdroj: DebateXML export {tournament_short}")
    rows.append(["Výsledky debát v jednotlivých kolách:"])
    rows.append([])

    debates_by_round: dict[int, list[DebateResult]] = defaultdict(list)
    for debate in sorted(debates, key=lambda item: (item.round_seq, item.debate_id)):
        debates_by_round[debate.round_seq].append(debate)

    block_width = 7
    spacer = 1
    max_debates = max((len(items) for items in debates_by_round.values()), default=0)
    total_cols = len(rounds) * block_width + max(0, len(rounds) - 1) * spacer

    row_round = ["" for _ in range(total_cols)]
    row_header = ["" for _ in range(total_cols)]
    merges = [f"A8:{col_ref(total_cols)}8", f"A11:{col_ref(total_cols)}11"]

    for index, round_name in enumerate(rounds):
        start = index * (block_width + spacer)
        end = start + block_width - 1
        motion_text = ""
        if debates_by_round.get(index + 1):
            motion_id = debates_by_round[index + 1][0].motion_id
            motion_text = motions.get(motion_id, motion_id)
        row_round[start] = round_name
        row_round[start + 1] = motion_text
        row_header[start + 1:start + 7] = ["S", "N", "výsledok", "", "rozhodcovia/rozhodkyne", "miestnosť"]
        merges.append(f"{col_ref(start + 2)}13:{col_ref(end + 1)}13")

    rows.append(row_round)
    rows.append(row_header)

    for debate_index in range(max_debates):
        row = ["" for _ in range(total_cols)]
        for round_index, _round_name in enumerate(rounds):
            start = round_index * (block_width + spacer)
            items = debates_by_round.get(round_index + 1, [])
            if debate_index >= len(items):
                continue
            debate = items[debate_index]
            if len(debate.sides) != 2:
                continue
            side_s, side_n = debate.sides
            team_s = teams[side_s.team_id]
            team_n = teams[side_n.team_id]
            votes_s = weighted_ballots_for_side(side_s, debate.weights)
            votes_n = weighted_ballots_for_side(side_n, debate.weights)
            adjudicator_text = ", ".join(adjudicator_short(adjudicators[adj_id].name) for adj_id in debate.adjudicator_ids if adj_id in adjudicators)
            row[start + 1:start + 7] = [
                team_display(team_s),
                team_display(team_n),
                votes_s,
                votes_n,
                adjudicator_text,
                venues.get(debate.venue_id, debate.venue_id),
            ]
        rows.append(row)

    widths = []
    for _ in rounds:
        widths.extend([2.5, 16.0, 16.0, 5.0, 5.0, 22.0, 12.0])
        widths.extend([3.0])
    if widths:
        widths = widths[:-1]
    return SheetSpec(name="debaty", rows=rows, widths=widths, merges=merges)


def build_body_sheet(
    tournament_name: str,
    tournament_short: str,
    rounds: list[str],
    teams: dict[str, TeamInfo],
    team_stats: dict[str, TeamStanding],
    speaker_stats: dict[str, SpeakerStanding],
    max_adj_count: int,
) -> SheetSpec:
    rows = build_title_rows(f"Výsledky {tournament_name}", f"Zdroj: DebateXML export {tournament_short}")
    rows.append(["Body a rečnícke body:"])
    rows.append([])

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
    round_offsets: dict[int, tuple[int, int]] = {}
    summary_size = 6
    total_cols = 3 + sum(2 + slot_counts[round_seq] for round_seq in range(1, len(rounds) + 1)) + summary_size
    row_round = ["" for _ in range(total_cols)]
    row_header = ["", "Tím", "Rečník/čka"] + ["" for _ in range(total_cols - 3)]
    merges = [f"A8:{col_ref(total_cols)}8", f"A11:{col_ref(total_cols)}11"]

    offset = 4
    for round_seq, round_name in enumerate(rounds, start=1):
        slot_count = slot_counts[round_seq]
        block_size = 2 + slot_count
        start = offset
        round_offsets[round_seq] = (start, slot_count)
        row_round[start - 1] = round_name
        row_header[start - 1:start - 1 + block_size] = ["V", "B", "RB"] + ["" for _ in range(slot_count - 1)]
        merges.append(f"{col_ref(start)}12:{col_ref(start + block_size - 1)}12")
        offset += block_size
    summary_start = offset
    row_round[summary_start - 1] = "Spolu"
    row_header[summary_start - 1:summary_start - 1 + summary_size] = ["V", "B", "RB – tím", "RB - indiv", "RB-min/max", "standardná odchýlka"]
    merges.append(f"{col_ref(summary_start)}12:{col_ref(summary_start + summary_size - 1)}12")

    rows.append(row_round)
    rows.append(row_header)

    sorted_teams = sorted(team_stats.values(), key=lambda row: (-row.wins, -row.ballots, -row.total_points, row.team_name.lower()))
    team_rank_rows = [{"team_id": row.team_id, "wins": row.wins, "ballots": row.ballots, "points": round(row.total_points, 6)} for row in sorted_teams]
    rank_rows(team_rank_rows, ("wins", "ballots", "points"))
    team_ranks = {row["team_id"]: row["rank"] for row in team_rank_rows}

    current_excel_row = len(rows) + 1
    for team_row in sorted_teams:
        team = teams[team_row.team_id]
        summary_row = [team_ranks[team.team_id], team_display(team), "Rozh. panel"]
        for round_seq, _round_name in enumerate(rounds, start=1):
            round_data = team_row.rounds.get(round_seq)
            if round_data is None or not round_data.debated:
                _start, slot_count = round_offsets[round_seq]
                summary_row.extend(["", ""] + ["" for _ in range(slot_count)])
                continue
            _start, slot_count = round_offsets[round_seq]
            names = expand_by_weights(round_data.adjudicator_names, round_data.panel_weights, slot_count)
            summary_row.extend([round_data.win, round_data.ballots] + names)
        summary_row.extend([
            team_row.wins,
            team_row.ballots,
            format_number(team_row.total_points),
            "",
            format_number(trimmed_total(team_row.round_totals)),
            format_number(safe_stdev(team_row.round_averages)),
        ])
        rows.append(summary_row)
        start_merge_row = current_excel_row
        current_excel_row += 1

        for speaker_id, speaker_name in team.speakers:
            speaker_row = ["", "", speaker_name]
            for round_seq, _round_name in enumerate(rounds, start=1):
                round_data = team_row.rounds.get(round_seq)
                _start, slot_count = round_offsets[round_seq]
                if round_data is None or not round_data.debated:
                    speaker_row.extend(["", ""] + ["" for _ in range(slot_count)])
                    continue
                panel_scores = round_data.speaker_panel_scores.get(speaker_id)
                if panel_scores is None:
                    speaker_row.extend(["", ""] + ["" for _ in range(slot_count)])
                    continue
                padded = [format_number(score) if score is not None else "" for score in expand_by_weights(panel_scores, round_data.panel_weights, slot_count)]
                speaker_row.extend(["", ""] + padded)
            speaker_entry = speaker_stats.get(speaker_id)
            if speaker_entry is None:
                speaker_row.extend(["", "", "", "", "", ""])
            else:
                speaker_row.extend([
                    "",
                    "",
                    "",
                    format_number(speaker_entry.total_points),
                    format_number(trimmed_total(speaker_entry.round_totals)),
                    format_number(safe_stdev(speaker_entry.round_averages)),
                ])
            rows.append(speaker_row)
            current_excel_row += 1

        cross_row = ["", "", "Krížové výsluchy"]
        cross_total = 0.0
        for round_seq, _round_name in enumerate(rounds, start=1):
            round_data = team_row.rounds.get(round_seq)
            _start, slot_count = round_offsets[round_seq]
            if round_data is None or not round_data.debated or not any(score is not None for score in round_data.cross_panel_scores):
                cross_row.extend(["", ""] + ["" for _ in range(slot_count)])
                continue
            padded = [format_number(score) if score is not None else "" for score in expand_by_weights(round_data.cross_panel_scores, round_data.panel_weights, slot_count)]
            cross_row.extend(["", ""] + padded)
            for score, weight in zip(round_data.cross_panel_scores, round_data.panel_weights):
                if score is not None:
                    cross_total += score * weight
        cross_row.extend(["", "", "", format_number(cross_total) if cross_total else "", "", ""])
        rows.append(cross_row)
        current_excel_row += 1

        reply_row = ["", "", "Záverečná reč"]
        reply_round_totals: list[float] = []
        reply_round_averages: list[float] = []
        reply_total = 0.0
        for round_seq, _round_name in enumerate(rounds, start=1):
            round_data = team_row.rounds.get(round_seq)
            _start, slot_count = round_offsets[round_seq]
            if round_data is None or not round_data.debated or not any(score is not None for score in round_data.reply_panel_scores):
                reply_row.extend(["", ""] + ["" for _ in range(slot_count)])
                continue
            padded = [format_number(score) if score is not None else "" for score in expand_by_weights(round_data.reply_panel_scores, round_data.panel_weights, slot_count)]
            reply_row.extend(["", ""] + padded)
            weighted_total = 0.0
            weighted_count = 0
            for score, weight in zip(round_data.reply_panel_scores, round_data.panel_weights):
                if score is None:
                    continue
                weighted_total += score * weight
                weighted_count += weight
            if weighted_count:
                reply_round_totals.append(weighted_total)
                reply_round_averages.append(weighted_total / weighted_count)
                reply_total += weighted_total
        reply_row.extend(["", "", "", format_number(reply_total), format_number(trimmed_total(reply_round_totals)), format_number(safe_stdev(reply_round_averages))])
        rows.append(reply_row)
        current_excel_row += 1

        end_merge_row = current_excel_row - 1
        if end_merge_row > start_merge_row:
            merges.append(f"A{start_merge_row}:A{end_merge_row}")
            merges.append(f"B{start_merge_row}:B{end_merge_row}")
        rows.append([])
        current_excel_row += 1

    widths = [4.0, 18.0, 24.0]
    for _ in rounds:
        widths.extend([4.0, 4.5] + [12.0 for _ in range(max_adj_count)] + [3.0])
    widths.extend([4.0, 4.5, 10.0, 10.0, 11.0, 12.0])
    return SheetSpec(name="body v kolách", rows=rows, widths=widths, merges=merges)


def build_results_sheet(
    tournament_name: str,
    tournament_short: str,
    team_stats: dict[str, TeamStanding],
    speaker_stats: dict[str, SpeakerStanding],
) -> SheetSpec:
    rows = build_title_rows(f"Výsledky {tournament_name}", f"Zdroj: DebateXML export {tournament_short}")
    rows.append(["Konečné poradie tímov a rečníkov/rečníčok:"])
    rows.append([])
    rows.append(["Poradie tímov", "", "", "", "", "", "Poradie rečníkov/rečníčok"])
    rows.append(["Miesto", "Tím", "V", "B", "RB", "", "Miesto", "Rečník/rečníčka", "Body", "Priemer", "B-MIN/MAX"])

    sorted_teams = sorted(team_stats.values(), key=lambda row: (-row.wins, -row.ballots, -row.total_points, row.team_name.lower()))
    team_rank_rows = [{"team_id": row.team_id, "wins": row.wins, "ballots": row.ballots, "points": round(row.total_points, 6)} for row in sorted_teams]
    rank_rows(team_rank_rows, ("wins", "ballots", "points"))
    team_ranks = {row["team_id"]: row["rank"] for row in team_rank_rows}

    sorted_speakers = sorted(
        speaker_stats.values(),
        key=lambda row: (-(average_or_none(row.total_points, row.weighted_ballot_count) or 0), -row.total_points, row.team_name.lower(), row.speaker_name.lower()),
    )
    speaker_rank_rows = [{"speaker_id": row.speaker_id, "avg": round(average_or_none(row.total_points, row.weighted_ballot_count) or 0, 6), "points": round(row.total_points, 6)} for row in sorted_speakers]
    rank_rows(speaker_rank_rows, ("avg", "points"))
    speaker_ranks = {row["speaker_id"]: row["rank"] for row in speaker_rank_rows}

    max_rows = max(len(sorted_teams), len(sorted_speakers))
    for index in range(max_rows):
        team_cells = ["", "", "", "", "", ""]
        speaker_cells = ["", "", "", "", ""]
        if index < len(sorted_teams):
            team = sorted_teams[index]
            team_cells = [team_ranks[team.team_id], team.team_name, team.wins, team.ballots, format_number(team.total_points), ""]
        if index < len(sorted_speakers):
            speaker = sorted_speakers[index]
            speaker_cells = [speaker_ranks[speaker.speaker_id], speaker.speaker_name, format_number(speaker.total_points), format_number(average_or_none(speaker.total_points, speaker.weighted_ballot_count)), format_number(trimmed_total(speaker.round_totals))]
        rows.append(team_cells + speaker_cells)

    merges = ["A8:K8", "A11:J11", "A13:E13", "G13:K13"]
    widths = [7.0, 24.0, 5.0, 5.0, 10.0, 4.0, 7.0, 30.0, 8.0, 8.5, 11.0]
    return SheetSpec(name="výsledky", rows=rows, widths=widths, merges=merges)


def col_ref(index: int) -> str:
    label = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        label = chr(65 + remainder) + label
    return label


def xml_cell(reference: str, value: object) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        return f'<c r="{reference}"><v>{value}</v></c>'
    return f'<c r="{reference}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'


def worksheet_xml(spec: SheetSpec) -> str:
    row_xml_parts: list[str] = []
    max_col = max((len(row) for row in spec.rows), default=1)
    last_ref = f"{col_ref(max_col)}{max(len(spec.rows), 1)}"
    for row_index, row in enumerate(spec.rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            cell = xml_cell(f"{col_ref(col_index)}{row_index}", value)
            if cell:
                cells.append(cell)
        row_xml_parts.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    cols_xml = ''
    if spec.widths:
        col_parts = []
        for index, width in enumerate(spec.widths, start=1):
            col_parts.append(f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>')
        cols_xml = f'<cols>{"".join(col_parts)}</cols>'
    merges_xml = ''
    if spec.merges:
        merge_parts = ''.join(f'<mergeCell ref="{ref}"/>' for ref in spec.merges)
        merges_xml = f'<mergeCells count="{len(spec.merges)}">{merge_parts}</mergeCells>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{last_ref}"/>'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f'{cols_xml}'
        f'<sheetData>{"".join(row_xml_parts)}</sheetData>'
        f'{merges_xml}'
        '</worksheet>'
    )


def workbook_xml(sheet_names: list[str]) -> str:
    sheet_xml = ''.join(f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>' for index, name in enumerate(sheet_names, start=1))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<bookViews><workbookView/></bookViews>'
        f'<sheets>{sheet_xml}</sheets>'
        '</workbook>'
    )


def workbook_rels_xml(sheet_count: int) -> str:
    rels = []
    for index in range(1, sheet_count + 1):
        rels.append(f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>')
    rels.append(f'<Relationship Id="rId{sheet_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'{"".join(rels)}'
        '</Relationships>'
    )


def root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        '</Relationships>'
    )


def content_types_xml(sheet_count: int) -> str:
    overrides = ''.join(f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for index in range(1, sheet_count + 1))
    overrides += '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    overrides += '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
    overrides += '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
    overrides += '<Override PartName="/xl/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'{overrides}'
        '</Types>'
    )


def app_xml(sheet_names: list[str]) -> str:
    parts = ''.join(f'<vt:lpstr>{escape(name)}</vt:lpstr>' for name in sheet_names)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        '<Application>DebateXML Converter</Application>'
        f'<TitlesOfParts><vt:vector size="{len(sheet_names)}" baseType="lpstr">{parts}</vt:vector></TitlesOfParts>'
        '</Properties>'
    )


def core_xml() -> str:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:creator>Tabbycat XML Converter</dc:creator>'
        '<cp:lastModifiedBy>Tabbycat XML Converter</cp:lastModifiedBy>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:modified>'
        '</cp:coreProperties>'
    )


def theme_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">'
        '<a:themeElements><a:clrScheme name="Office"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1><a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1></a:clrScheme><a:fontScheme name="Office"><a:majorFont/><a:minorFont/></a:fontScheme><a:fmtScheme name="Office"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme></a:themeElements>'
        '</a:theme>'
    )


def write_xlsx(output_path: Path, sheets: list[SheetSpec]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr('[Content_Types].xml', content_types_xml(len(sheets)))
        workbook.writestr('_rels/.rels', root_rels_xml())
        workbook.writestr('docProps/app.xml', app_xml([sheet.name for sheet in sheets]))
        workbook.writestr('docProps/core.xml', core_xml())
        workbook.writestr('xl/workbook.xml', workbook_xml([sheet.name for sheet in sheets]))
        workbook.writestr('xl/_rels/workbook.xml.rels', workbook_rels_xml(len(sheets)))
        workbook.writestr('xl/theme/theme1.xml', theme_xml())
        for index, sheet in enumerate(sheets, start=1):
            workbook.writestr(f'xl/worksheets/sheet{index}.xml', worksheet_xml(sheet))


def main() -> None:
    args = parse_args()
    xml_path = args.xml_path.resolve()
    output_path = build_output_path(xml_path, args.output.resolve() if args.output else None)

    tournament_name, tournament_short, rounds, teams, adjudicators, venues, motions, debates = parse_debatexml(xml_path)
    team_stats, speaker_stats, max_adj_count = build_aggregates(teams, adjudicators, debates)

    sheets = [
        build_codes_sheet(tournament_name, tournament_short, teams, adjudicators),
        build_debaty_sheet(tournament_name, tournament_short, rounds, teams, adjudicators, venues, motions, debates),
        build_body_sheet(tournament_name, tournament_short, rounds, teams, team_stats, speaker_stats, max_adj_count or 3),
        build_results_sheet(tournament_name, tournament_short, team_stats, speaker_stats),
    ]
    write_xlsx(output_path, sheets)
    print(f'Wrote {output_path}')


if __name__ == '__main__':
    main()

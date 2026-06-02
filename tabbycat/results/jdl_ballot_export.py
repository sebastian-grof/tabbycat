from __future__ import annotations

import zipfile
from io import BytesIO
from numbers import Number
from pathlib import Path
from xml.etree import ElementTree as ET

from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify

from adjallocation.models import DebateAdjudicator
from draw.types import DebateSide
from xmlconverter.converter_core import adjudicator_short, format_number
from xmlconverter.styled import (
    col_index,
    q,
    remove_calc_chain,
    remove_sheet_protection,
    serialize_worksheet,
    set_cell_value,
    trim_sheet,
)

from .models import BallotSubmission, ScoreCriterion, SpeakerScore, SpeakerScoreByAdj


JDL_FIRST_CATEGORY_EXPORT_FORMAT = 'jdl_first_category'
DEFAULT_TEMPLATE_PATH = Path(__file__).resolve().parent / "assets" / "jdl_first_category_ballot.xlsx"


class JDLFirstCategoryBallotExportError(ValueError):
    pass


def is_jdl_first_category_ballot_export_enabled(tournament):
    return tournament.pref('ballot_export_format') == JDL_FIRST_CATEGORY_EXPORT_FORMAT


def build_jdl_first_category_ballot_xlsx(
    ballot_submission: BallotSubmission,
    template_path: Path = DEFAULT_TEMPLATE_PATH,
) -> bytes:
    context = _build_export_context(ballot_submission)
    entries, sheet_root = _load_single_sheet_template(template_path)

    remove_calc_chain(entries)
    remove_sheet_protection(sheet_root)
    _fill_sheet(sheet_root, context)
    trim_sheet(sheet_root, max_row=38, max_col=col_index("AE"))

    output = BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            if name == "xl/worksheets/sheet1.xml":
                zf.writestr(name, serialize_worksheet(sheet_root))
            else:
                zf.writestr(name, data)
    return output.getvalue()


def jdl_first_category_ballot_filename_slug(ballot_submission: BallotSubmission) -> str:
    tournament = ballot_submission.debate.round.tournament
    debate_team = _get_single_debate_team(ballot_submission.debate)
    return slugify_filename_parts(
        tournament.short_name or tournament.name or tournament.slug,
        _speaker_name(ballot_submission, debate_team, tournament),
        _jdl_first_category_position_name(debate_team.side),
    )


def slugify_filename_parts(*parts: object) -> str:
    filename = "-".join(str(part).strip() for part in parts if str(part).strip())
    return slugify(filename) or "jdl-1-ballot"


def _load_single_sheet_template(template_path: Path) -> tuple[dict[str, bytes], ET.Element]:
    entries: dict[str, bytes] = {}
    with zipfile.ZipFile(template_path) as zf:
        for name in zf.namelist():
            entries[name] = zf.read(name)
    return entries, ET.fromstring(entries["xl/worksheets/sheet1.xml"])


def _build_export_context(ballot_submission: BallotSubmission) -> dict[str, object]:
    debate = ballot_submission.debate
    tournament = debate.round.tournament

    if not is_jdl_first_category_ballot_export_enabled(tournament):
        raise JDLFirstCategoryBallotExportError("JDL first category ballot export is not enabled.")

    debate_team = _get_single_debate_team(debate)
    voting_adjudications = _get_voting_adjudications(debate)
    if not voting_adjudications:
        raise JDLFirstCategoryBallotExportError("No voting adjudicators found for this debate.")

    criteria = _get_export_criteria(tournament)
    score_rows = _build_score_rows(ballot_submission, debate_team, voting_adjudications, criteria)
    slot_weights = [_adjudication_weight(tournament, voting_adjudications, da) for da in voting_adjudications]
    panel_names = _expand_by_weights(
        [adjudicator_short(da.adjudicator.name) for da in voting_adjudications],
        slot_weights,
        3,
    )

    chair = next(
        (da for da in voting_adjudications if da.type == DebateAdjudicator.TYPE_CHAIR),
        voting_adjudications[0],
    )
    try:
        notes = ballot_submission.text_feedback
    except ObjectDoesNotExist:
        notes = None

    return {
        'tournament': tournament.name,
        'motion': _motion_text(ballot_submission),
        'position': _jdl_first_category_position_name(debate_team.side),
        'speaker': _speaker_name(ballot_submission, debate_team, tournament),
        'criteria': criteria,
        'panel_names': panel_names,
        'score_rows': score_rows,
        'notes': notes.text if notes else '',
        'chair_signature': adjudicator_short(chair.adjudicator.name),
    }


def _jdl_first_category_position_name(side: DebateSide) -> str:
    if side == DebateSide.AFF:
        return "Súhlas"
    if side == DebateSide.NEG:
        return "Nesúhlas"
    return ""


def _get_single_debate_team(debate):
    debate_teams = list(debate.debateteam_set.exclude(side=DebateSide.BYE).select_related('team'))
    if len(debate_teams) != 1:
        raise JDLFirstCategoryBallotExportError("JDL first category ballot export requires exactly one debate team.")
    return debate_teams[0]


def _get_voting_adjudications(debate) -> list[DebateAdjudicator]:
    adjudications = list(debate.debateadjudicator_set.exclude(
        type=DebateAdjudicator.TYPE_TRAINEE,
    ).select_related('adjudicator').order_by('id'))
    return sorted(adjudications, key=lambda da: (0 if da.type == DebateAdjudicator.TYPE_CHAIR else 1, da.id))


def _adjudication_weight(
    tournament,
    voting_adjudications: list[DebateAdjudicator],
    adjudication: DebateAdjudicator,
) -> int:
    if tournament.pref('adjudicator_weighting') != 'weighted-to-three':
        return 1
    if len(voting_adjudications) == 1:
        return 3
    if len(voting_adjudications) == 2:
        return 2 if adjudication.type == DebateAdjudicator.TYPE_CHAIR else 1
    return 1


def _expand_by_weights(values: list[object], weights: list[int], slot_count: int) -> list[object]:
    expanded: list[object] = []
    for value, weight in zip(values, weights):
        expanded.extend([value] * weight)
    while len(expanded) < slot_count:
        expanded.append("")
    return expanded[:slot_count]


def _get_export_criteria(tournament) -> list[ScoreCriterion]:
    criteria = [
        criterion for criterion in ScoreCriterion.objects.filter(tournament=tournament).order_by('seq')
        if criterion.applies_to_position(1, tournament.reply_position, tournament.pref('reply_scores_enabled'))
    ]
    return criteria[:5]


def _build_score_rows(ballot_submission, debate_team, voting_adjudications, criteria) -> list[list[object]]:
    scores_by_adjudication = {}
    speaker_scores = SpeakerScoreByAdj.objects.filter(
        ballot_submission=ballot_submission,
        debate_team=debate_team,
        debate_adjudicator__in=voting_adjudications,
        position=1,
    ).prefetch_related('speakercriterionscorebyadj_set')

    for speaker_score in speaker_scores:
        scores_by_adjudication[speaker_score.debate_adjudicator_id] = {
            criterion_score.criterion_id: criterion_score.score
            for criterion_score in speaker_score.speakercriterionscorebyadj_set.all()
        }

    weights = [
        _adjudication_weight(ballot_submission.debate.round.tournament, voting_adjudications, adjudication)
        for adjudication in voting_adjudications
    ]

    rows: list[list[object]] = []
    for criterion in criteria:
        values = [
            scores_by_adjudication.get(adjudication.id, {}).get(criterion.id, "")
            for adjudication in voting_adjudications
        ]
        rows.append(_expand_by_weights(values, weights, 3))
    return rows


def _speaker_name(ballot_submission, debate_team, tournament) -> str:
    speaker_score = SpeakerScore.objects.filter(
        ballot_submission=ballot_submission,
        debate_team=debate_team,
        position=1,
    ).select_related('speaker').first()
    if speaker_score is not None and speaker_score.speaker_id:
        return str(speaker_score.speaker.get_public_name(tournament))

    speaker = debate_team.team.speaker_set.order_by('name').first()
    return str(speaker.get_public_name(tournament)) if speaker else debate_team.team.short_name


def _motion_text(ballot_submission) -> str:
    if ballot_submission.motion_id:
        return ballot_submission.motion.text
    round_motion = ballot_submission.debate.round.roundmotion_set.order_by('seq').select_related('motion').first()
    return round_motion.motion.text if round_motion else ""


def _fill_sheet(sheet_root: ET.Element, context: dict[str, object]) -> None:
    set_cell_value(sheet_root, "D3", context['tournament'])
    set_cell_value(sheet_root, "Y3", context['position'])
    set_cell_value(sheet_root, "D5", context['motion'])
    set_cell_value(sheet_root, "L8", context['speaker'])

    for column, name in zip(("L", "M", "N"), context['panel_names']):
        set_cell_value(sheet_root, f"{column}9", name)

    score_total = 0.0
    criteria = context['criteria']
    score_rows = context['score_rows']
    for offset in range(5):
        row = 10 + offset
        criterion = criteria[offset] if offset < len(criteria) else None
        set_cell_value(sheet_root, f"B{row}", criterion.name if criterion else "")

        values = score_rows[offset] if offset < len(score_rows) else ["", "", ""]
        for column, value in zip(("L", "M", "N"), values):
            set_cell_value(sheet_root, f"{column}{row}", format_number(value) if isinstance(value, Number) else value)
            if isinstance(value, Number):
                score_total += float(value)

    _set_formula_cached_value(sheet_root, "L15", score_total)
    _set_formula_cached_value(sheet_root, "L16", score_total / 3 if score_total else 0)
    set_cell_value(sheet_root, "A19", context['notes'])
    set_cell_value(sheet_root, "I36", context['chair_signature'])


def _set_formula_cached_value(sheet_root: ET.Element, ref: str, value: float) -> None:
    cell = sheet_root.find(f".//{q('c')}[@r='{ref}']")
    if cell is None:
        return

    for child in list(cell):
        if child.tag == q("v"):
            cell.remove(child)

    v_node = ET.SubElement(cell, q("v"))
    v_node.text = str(round(value, 2))

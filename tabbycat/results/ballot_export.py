from __future__ import annotations

import logging
import zipfile
from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from typing import Callable, Iterable

from django.http import Http404, HttpResponse
from django.utils.text import slugify

from draw.models import Debate
from draw.types import DebateSide

from .jdl_ballot_export import (
    JDLFirstCategoryBallotExportError,
    build_jdl_first_category_ballot_xlsx,
    jdl_first_category_ballot_filename_slug,
)
from .models import BallotSubmission

logger = logging.getLogger(__name__)

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@dataclass(frozen=True)
class BallotExporter:
    """Describes how to export a single ballot for a given ``ballot_export_format``.

    Register one entry per format in :data:`BALLOT_EXPORTERS`. Both the
    single-ballot download and the bulk (zip) download dispatch through here, so
    adding a new format is a one-line registration with no other code changes.
    """
    build: Callable[[BallotSubmission], bytes]
    filename_slug: Callable[[BallotSubmission], str]
    extension: str
    content_type: str
    error: type[Exception]


BALLOT_EXPORTERS: dict[str, BallotExporter] = {
    'jdl_first_category': BallotExporter(
        build=build_jdl_first_category_ballot_xlsx,
        filename_slug=jdl_first_category_ballot_filename_slug,
        extension='xlsx',
        content_type=XLSX_CONTENT_TYPE,
        error=JDLFirstCategoryBallotExportError,
    ),
}


def get_ballot_exporter(tournament) -> BallotExporter | None:
    """Return the exporter configured for the tournament, or ``None`` if ballot
    export is off (or set to a format with no registered exporter)."""
    return BALLOT_EXPORTERS.get(tournament.pref('ballot_export_format'))


def confirmed_ballots_for(*, tournament=None, round=None):
    """Queryset of confirmed ballots in scope — the ballots a bulk download
    would contain. Bye debates are excluded (they have no exportable ballot)."""
    qs = BallotSubmission.objects.filter(confirmed=True).exclude(
        debate__debateteam__side=DebateSide.BYE)
    if round is not None:
        return qs.filter(debate__round=round)
    if tournament is not None:
        return qs.filter(debate__round__tournament=tournament)
    return qs


@dataclass
class BallotExportSummary:
    """Completeness counters for a bulk ballot download, so a user can tell
    whether the package will be incomplete before downloading it."""
    debates: int        # non-bye debates in scope (the ballots we expect)
    submitted: int      # confirmed ballots (what the zip will contain)
    with_notes: int     # confirmed ballots carrying a non-empty note

    @property
    def complete(self) -> bool:
        return self.submitted > 0 and self.submitted >= self.debates


def ballot_export_summary(*, tournament=None, round=None) -> BallotExportSummary:
    ballots = confirmed_ballots_for(tournament=tournament, round=round)
    submitted = ballots.count()
    with_notes = ballots.filter(text_feedback__isnull=False).exclude(
        text_feedback__text='').count()

    debates = Debate.objects.exclude(debateteam__side=DebateSide.BYE)
    if round is not None:
        debates = debates.filter(round=round)
    elif tournament is not None:
        debates = debates.filter(round__tournament=tournament)

    return BallotExportSummary(debates=debates.count(), submitted=submitted, with_notes=with_notes)


def ballot_download_response(ballot_submission: BallotSubmission) -> HttpResponse:
    """Build a single-ballot download response for the tournament's configured
    export format. Raises ``Http404`` if export is disabled or the ballot can't
    be exported."""
    tournament = ballot_submission.debate.round.tournament
    exporter = get_ballot_exporter(tournament)
    if exporter is None:
        raise Http404

    try:
        contents = exporter.build(ballot_submission)
        filename_slug = exporter.filename_slug(ballot_submission)
    except exporter.error as exc:
        logger.warning("Unable to export ballot %s: %s", ballot_submission.id, exc)
        raise Http404(str(exc))

    response = HttpResponse(contents, content_type=exporter.content_type)
    response["Content-Disposition"] = 'attachment; filename="%s.%s"' % (filename_slug, exporter.extension)
    return response


@dataclass
class BulkBallotExport:
    content: bytes
    exported: int
    skipped: int


def build_ballots_zip(
    exporter: BallotExporter,
    ballots: Iterable[tuple[str, BallotSubmission]],
) -> BulkBallotExport:
    """Zip up a collection of exported ballots.

    ``ballots`` yields ``(folder, ballot_submission)`` pairs; ``folder`` may be
    an empty string for a flat archive, otherwise it becomes a directory inside
    the zip. Ballots that fail to export (e.g. a debate that doesn't fit the
    format) are skipped and counted rather than aborting the whole archive.
    """
    output = BytesIO()
    used_names: Counter[str] = Counter()
    exported = skipped = 0

    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for folder, ballot in ballots:
            try:
                data = exporter.build(ballot)
                slug = exporter.filename_slug(ballot)
            except exporter.error as exc:
                logger.info("Skipping ballot %s in bulk export: %s", ballot.id, exc)
                skipped += 1
                continue

            zf.writestr(_unique_member_name(used_names, folder, slug, exporter.extension), data)
            exported += 1

    return BulkBallotExport(content=output.getvalue(), exported=exported, skipped=skipped)


def _unique_member_name(used: Counter, folder: str, slug: str, extension: str) -> str:
    """Build a collision-free archive member path. Two ballots can slugify to
    the same name (e.g. identical speaker names), so disambiguate with a counter
    suffix."""
    base = "%s/%s" % (slugify(folder), slug) if folder else slug
    used[base] += 1
    if used[base] > 1:
        base = "%s-%d" % (base, used[base])
    return "%s.%s" % (base, extension)

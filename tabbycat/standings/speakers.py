"""Standings generator for speakers."""

import logging
from builtins import round as round_score
from collections import defaultdict
from functools import partialmethod

from django.db.models import Avg, Case, Count, F, FloatField, Max, Min, OuterRef, Q, StdDev, Subquery, Sum, Value, When
from django.db.models.functions import Cast, Coalesce, NullIf, Round as RoundScore
from django.utils.translation import gettext_lazy as _

from results.models import SpeakerScore, TeamScore
from tournaments.models import Round

from .base import BaseStandingsGenerator, StandingsError
from .metrics import BaseMetricAnnotator, QuerySetMetricAnnotator, SCORE_PRECISION
from .ranking import BasicRankAnnotator

logger = logging.getLogger(__name__)


# ==============================================================================
# Metric annotators
# ==============================================================================

class SpeakerScoreQuerySetMetricAnnotator(QuerySetMetricAnnotator):
    """Base class for annotators for metrics based on conditional aggregations
    of SpeakerScore instances."""

    function = None
    replies = False
    field = 'speakerscore__score'
    where_value = None
    round_value = True
    preserve_sda_precision = True

    def get_annotation_filter(self, round):
        """Returns the Q object restricting which speeches the metric counts."""
        annotation_filter = Q(
            speakerscore__ballot_submission__confirmed=True,
            speakerscore__debate_team__debate__round__seq__lte=round.seq,
            speakerscore__debate_team__debate__round__stage=Round.Stage.PRELIMINARY,
            speakerscore__ghost=False,
        )
        if self.replies:
            annotation_filter &= Q(speakerscore__position=round.tournament.reply_position)
        else:
            annotation_filter &= Q(speakerscore__position__lte=round.tournament.last_substantive_position)

        return annotation_filter

    def get_annotation(self, round):
        annotation = self.get_aggregation(round)
        if self.round_value and (not self.preserve_sda_precision or
                round.tournament.pref('adjudicator_weighting') != 'weighted-to-three'):
            return RoundScore(annotation, precision=SCORE_PRECISION)
        return annotation

    def get_aggregation(self, round):
        """Build the unrounded aggregate so derived metrics round only once."""
        return self.function(self.field, filter=self.get_annotation_filter(round))


class TeamMetricQuerySetMetricAnnotator(SpeakerScoreQuerySetMetricAnnotator):

    combinable = False
    round_value = False

    def get_annotation(self, round):
        """Returns a QuerySet annotated with the metric."""
        annotation_filter = Q(
            team__debateteam__teamscore__ballot_submission__confirmed=True,
            team__debateteam__debate__round__seq__lte=round.seq,
            team__debateteam__debate__round__stage=Round.Stage.PRELIMINARY,
        )
        if self.where_value is not None:
            annotation_filter &= Q(**{self.field: self.where_value})

        return self.function(self.field, filter=annotation_filter)


class TotalSpeakerScoreMetricAnnotator(SpeakerScoreQuerySetMetricAnnotator):
    """Metric annotator for total speaker score."""
    key = "total"
    name = _("total")
    abbr = _("Total")
    function = Sum


class AverageSpeakerScoreMetricAnnotator(BaseMetricAnnotator):
    """Metric annotator for average speaker score."""
    key = "average"
    name = _("average")
    abbr = _("Avg")

    replies = False

    def annotate(self, queryset, standings, round=None):
        speakers = list(queryset)
        speaker_ids = [speaker.id for speaker in speakers]
        scores_by_speaker = defaultdict(list)

        tournament = round.tournament if round is not None else (speakers[0].team.tournament if speakers else None)
        normalize_weighted_scores = (
            tournament is not None and
            tournament.pref('adjudicator_weighting') == 'weighted-to-three'
        )

        if speaker_ids and tournament is not None:
            annotation_filter = Q(
                ballot_submission__confirmed=True,
                debate_team__debate__round__stage=Round.Stage.PRELIMINARY,
                ghost=False,
                speaker_id__in=speaker_ids,
            )
            if round is not None:
                annotation_filter &= Q(debate_team__debate__round__seq__lte=round.seq)
            if self.replies:
                annotation_filter &= Q(position=tournament.reply_position)
            else:
                annotation_filter &= Q(position__lte=tournament.last_substantive_position)

            speaker_scores = list(SpeakerScore.objects.filter(annotation_filter).values_list(
                'speaker_id', 'score', 'ballot_submission_id',
            ))
            ballot_submission_ids = {ballot_submission_id for _, _, ballot_submission_id in speaker_scores}

            votes_possible_by_ballot = {}
            if ballot_submission_ids:
                for ballot_submission_id, votes_possible in TeamScore.objects.filter(
                    ballot_submission_id__in=ballot_submission_ids,
                ).values_list('ballot_submission_id', 'votes_possible'):
                    if votes_possible is not None and ballot_submission_id not in votes_possible_by_ballot:
                        votes_possible_by_ballot[ballot_submission_id] = votes_possible

            for speaker_id, score, ballot_submission_id in speaker_scores:
                divisor = (votes_possible_by_ballot.get(ballot_submission_id) or 1) if normalize_weighted_scores else 1
                scores_by_speaker[speaker_id].append(score / divisor)

        for speaker in speakers:
            scores = scores_by_speaker.get(speaker.id)
            value = sum(scores) / len(scores) if scores else None
            # Existing SDA rankings compare these values at their original
            # precision. Rounding first can create ties or move tied speakers.
            if value is not None and not normalize_weighted_scores:
                value = round_score(value, SCORE_PRECISION)
            standings.add_metric(speaker, self.key, value)


class SpeakerTeamPointsMetricAnnotator(TeamMetricQuerySetMetricAnnotator):
    """Metric annotator for team points."""
    key = "team_points"
    name = _("team points")
    abbr = _("Team")

    field = 'team__debateteam__teamscore__points'
    function = Sum


class SpeakerTeamWinsMetricAnnotator(TeamMetricQuerySetMetricAnnotator):
    """Metric annotator for total number of wins for the team that the speaker is in."""
    key = "team_wins"
    name = _("Wins")
    abbr = _("Wins")

    function = Count
    field = 'team__debateteam__teamscore__win'
    where_value = True


class SpeakerFirstsMetricAnnotator(TeamMetricQuerySetMetricAnnotator):
    """Metric annotator for counting the number of first-place finishes (points = 3) for a speaker's team."""
    key = "firsts"
    name = _("number of firsts")
    abbr = _("1sts")

    function = Count
    field = 'team__debateteam__teamscore__points'
    where_value = 3


class SpeakerNumberOfSecondsMetricAnnotator(TeamMetricQuerySetMetricAnnotator):
    """Metric annotator for counting the number of second-place finishes (points = 2) for a speaker's team."""
    key = "seconds"
    name = _("number of seconds")
    abbr = _("2nds")

    function = Count
    field = 'team__debateteam__teamscore__points'
    where_value = 2


class SpeakerNumberOfThirdsMetricAnnotator(TeamMetricQuerySetMetricAnnotator):
    """Metric annotator for counting the number of third-place finishes (points = 1) for a speaker's team."""
    key = "thirds"
    name = _("number of thirds")
    abbr = _("3rds")

    function = Count
    field = 'team__debateteam__teamscore__points'
    where_value = 1


class NumberOfAdjudicatorsMetricAnnotator(TeamMetricQuerySetMetricAnnotator):
    key = "num_adjs"
    name = _("number of adjudicators who voted for this team")
    abbr = _("Ballots")
    choice_name = _("votes/ballots carried")
    function = Sum

    def __init__(self, adjs_per_debate=3):
        self.adjs_per_debate = adjs_per_debate

    def get_field(self):
        return (Cast('team__debateteam__teamscore__votes_given', FloatField()) /
            NullIf('team__debateteam__teamscore__votes_possible', 0, output_field=FloatField()) *
            self.adjs_per_debate)

    def annotate_with_queryset(self, queryset, standings):
        cast = int if all(t.num_adjs == int(t.num_adjs) for t in queryset if t.num_adjs is not None) else float
        for item in queryset:
            metric = item.num_adjs or 0
            standings.add_metric(item, self.key, cast(metric))


class StandardDeviationSpeakerScoreMetricAnnotator(SpeakerScoreQuerySetMetricAnnotator):
    """Metric annotator for standard deviation of speaker score."""
    key = "stdev"
    name = _("standard deviation")
    abbr = _("Stdev")
    function = StdDev
    ascending = True


class NumberOfSpeechesMetricAnnotator(SpeakerScoreQuerySetMetricAnnotator):
    """Metric annotator for number of speeches given."""
    key = "count"
    name = _("number of speeches given")
    abbr = _("Num")
    function = Count
    round_value = False


class TotalReplyScoreMetricAnnotator(SpeakerScoreQuerySetMetricAnnotator):
    """Metric annotator for total reply score."""
    key = "replies_sum"
    name = _("total")
    abbr = _("Total")
    function = Sum
    replies = True
    listed = False


class AverageReplyScoreMetricAnnotator(AverageSpeakerScoreMetricAnnotator):
    """Metric annotator for average reply score."""
    key = "replies_avg"
    name = _("average")
    abbr = _("Avg")
    replies = True
    listed = False


class StandardDeviationReplyScoreMetricAnnotator(SpeakerScoreQuerySetMetricAnnotator):
    """Metric annotator for standard deviation of reply score."""
    key = "replies_stddev"
    name = _("standard deviation")
    abbr = _("Stdev")
    function = StdDev
    replies = True
    listed = False
    ascending = True


class NumberOfRepliesMetricAnnotator(SpeakerScoreQuerySetMetricAnnotator):
    """Metric annotator for number of replies given."""
    key = "replies_count"
    name = _("replies given")
    abbr = _("Num")
    function = Count
    round_value = False
    replies = True
    listed = False


class TrimmedMeanSpeakerScoreMetricAnnotator(SpeakerScoreQuerySetMetricAnnotator):
    """Metric annotator for trimmed mean speaker score."""
    key = "trimmed_mean"
    name = _("trimmed mean (high-low drop)")
    abbr = _("Trim")

    class SpeechCount(NumberOfSpeechesMetricAnnotator):
        key = 'speech_count'

    class MaximumScore(SpeakerScoreQuerySetMetricAnnotator):
        function = Max

    class MinimumScore(SpeakerScoreQuerySetMetricAnnotator):
        function = Min

    def get_annotated_queryset(self, queryset, round=None):
        # Slight breach of separation of concerns: add the 'count' annotation so
        # that the main annotation will know what 'count' means. We can't do
        # this inline in get_annotation() because Django doesn't support the
        # syntax F('count') > 2, and we're forced to use count__gt=2 instead.
        queryset = self.SpeechCount().get_annotated_queryset(queryset, round=round)
        return super().get_annotated_queryset(queryset, round=round)

    def get_annotation(self, round=None):
        total = TotalSpeakerScoreMetricAnnotator().get_aggregation(round)
        highest = self.MaximumScore().get_aggregation(round)
        lowest = self.MinimumScore().get_aggregation(round)

        annotation = Case(
            When(speech_count__gt=2, then=(total - highest - lowest) / (F('speech_count') - 2)),
            When(speech_count__gt=0, then=total / F('speech_count')),
            output_field=FloatField(),
        )
        if round.tournament.pref('adjudicator_weighting') == 'weighted-to-three':
            return annotation
        return RoundScore(annotation, precision=SCORE_PRECISION)


class SpeakerScoreRankingsMetricAnnotator(SpeakerScoreQuerySetMetricAnnotator):
    """Metric annotator for standard deviation of speaker score."""
    key = "srank"
    name = _("speech ranks")
    abbr = _("SRank")
    function = Sum
    ascending = True
    field = 'speakerscore__rank'
    round_value = False


# ==============================================================================
# Score criterion metric annotators
# ==============================================================================

class BaseCriterionMetricAnnotator(SpeakerScoreQuerySetMetricAnnotator):
    """Base class for metrics on a single score criterion. These are keyed by
    the criterion's seq, so use criterion_metric_annotator_classes() to build
    them for a tournament rather than instantiating these directly."""

    field = 'speakerscore__speakercriterionscore__score'
    preserve_sda_precision = False
    key_prefix = None  # must be set by subclasses
    name_format = None  # must be set by subclasses
    abbr_format = None  # must be set by subclasses

    # The criterion join gives one row per criterion per speech, which would
    # inflate other aggregations if combined into the shared query.
    combinable = False

    # Set by views dedicated to a single criterion, where the criterion's name
    # is already in the page title and would just repeat in every column.
    standalone = False

    def __init__(self, criterion):
        self.criterion = criterion
        self.key = self.build_key(criterion.seq)
        self.name = self.name_format % {'criterion': criterion.name}
        self.abbr = self.short_abbr if self.standalone else (
            self.abbr_format % {'criterion': criterion.name})

    @classmethod
    def build_key(cls, seq):
        return '%s%d' % (cls.key_prefix, seq)

    @classmethod
    def choice_label(cls):
        return (cls.name_format % {'criterion': cls.criterion_name}).capitalize()

    def get_annotation_filter(self, round):
        # The inherited filter restricts this to the substantive speeches, as
        # for the other speaker metrics. The criterion's own speech_type
        # doesn't narrow it further: a criterion is only ever scored on the
        # speeches it applies to, and one scored only on replies has no
        # standings of its own.
        return super().get_annotation_filter(round) & Q(
            speakerscore__speakercriterionscore__criterion=self.criterion)


class TotalCriterionScoreMetricAnnotator(BaseCriterionMetricAnnotator):
    """Metric annotator for total score on a single criterion."""
    key_prefix = "criterion_total_"
    name_format = _("total for %(criterion)s")
    abbr_format = _("%(criterion)s Total")
    short_abbr = _("Total")
    function = Sum


class AverageCriterionScoreMetricAnnotator(BaseCriterionMetricAnnotator):
    """Metric annotator for average score on a single criterion."""
    key_prefix = "criterion_avg_"
    name_format = _("average for %(criterion)s")
    abbr_format = _("%(criterion)s Avg")
    short_abbr = _("Avg")
    function = Avg

    def get_aggregation(self, round):
        score = F(self.field)
        if round.tournament.pref('adjudicator_weighting') == 'weighted-to-three':
            # Criterion scores are stored as weighted panel totals in SDA.
            # Normalize only the average, as the overall speaker average and
            # per-round criterion columns do. Total retains weighted points.
            # Panel sizes may vary.
            votes = TeamScore.objects.filter(
                ballot_submission_id=OuterRef('speakerscore__ballot_submission_id'),
                debate_team_id=OuterRef('speakerscore__debate_team_id'),
            ).values('votes_possible')[:1]
            divisor = Coalesce(NullIf(Subquery(votes), 0), Value(1))
            score = score / Cast(divisor, FloatField())
        return self.function(score, filter=self.get_annotation_filter(round))


def is_criterion_metric_key(key):
    """Whether `key` names a score criterion metric. The criteria themselves are
    per-tournament, so preference validation, which has no tournament to hand,
    checks the key's shape only; unavailable criteria raise a StandingsError
    when the standings are generated."""
    for base in (AverageCriterionScoreMetricAnnotator, TotalCriterionScoreMetricAnnotator):
        if key.startswith(base.key_prefix) and key[len(base.key_prefix):].isdigit():
            return True
    return False


def criterion_metric_annotator_classes(tournament, standalone_criterion=None):
    """Returns the metric annotator classes for the tournament's score criteria,
    keyed by metric key. Criteria scored only on replies are left out, since
    these metrics are over substantive speeches. Each binds its criterion, so that they can
    be used like the classes in SpeakerStandingsGenerator's static dict.

    `standalone_criterion`, if given, is the criterion whose page this is, and
    so whose metrics should be labelled without repeating its name."""
    classes = {}
    for criterion in tournament.substantive_score_criteria:
        for base in (AverageCriterionScoreMetricAnnotator, TotalCriterionScoreMetricAnnotator):
            key = base.build_key(criterion.seq)
            classes[key] = type(base.__name__, (base,), {
                '__init__': partialmethod(base.__init__, criterion),
                'key': key,
                'criterion_name': criterion.name,
                'standalone': criterion == standalone_criterion,
            })
    return classes


# ==============================================================================
# Standings generator
# ==============================================================================

class SpeakerStandingsGenerator(BaseStandingsGenerator):
    """Class for generating speaker standings. An instance is configured with
    metrics and rankings in the constructor, and an iterable of Speaker objects
    is passed to its `generate()` method to generate standings. Example:

        generator = TeamStandingsGenerator(('points', 'speaker_score'), ('rank',))
        standings = generator.generate(teams)

    The generate() method returns a TeamStandings object.
    """

    TIEBREAK_FUNCTIONS = BaseStandingsGenerator.TIEBREAK_FUNCTIONS.copy()
    TIEBREAK_FUNCTIONS["name"] = lambda x: x.sort(key=lambda y: y.speaker.name)
    TIEBREAK_FUNCTIONS["institution"] = lambda x: x.sort(key=lambda y: y.speaker.team.institution.name)

    QUERYSET_TIEBREAK_FIELDS = BaseStandingsGenerator.QUERYSET_TIEBREAK_FIELDS.copy()
    QUERYSET_TIEBREAK_FIELDS["name"] = 'name'
    QUERYSET_TIEBREAK_FIELDS["institution"] = 'team__institution__name'

    metric_annotator_classes = {
        "total"         : TotalSpeakerScoreMetricAnnotator,
        "average"       : AverageSpeakerScoreMetricAnnotator,
        "trimmed_mean"  : TrimmedMeanSpeakerScoreMetricAnnotator,
        "team_points"   : SpeakerTeamPointsMetricAnnotator,
        "stdev"         : StandardDeviationSpeakerScoreMetricAnnotator,
        "count"         : NumberOfSpeechesMetricAnnotator,
        "replies_sum"   : TotalReplyScoreMetricAnnotator,
        "replies_avg"   : AverageReplyScoreMetricAnnotator,
        "replies_stddev": StandardDeviationReplyScoreMetricAnnotator,
        "replies_count" : NumberOfRepliesMetricAnnotator,
        "srank"         : SpeakerScoreRankingsMetricAnnotator,
        "team_wins"     : SpeakerTeamWinsMetricAnnotator,
        "firsts"        : SpeakerFirstsMetricAnnotator,
        "seconds"       : SpeakerNumberOfSecondsMetricAnnotator,
        "thirds"        : SpeakerNumberOfThirdsMetricAnnotator,
        "num_adjs"      : NumberOfAdjudicatorsMetricAnnotator,
    }

    ranking_annotator_classes = {
        "rank"     : BasicRankAnnotator,
    }

    tournament_field = 'team__tournament'

    def __init__(self, metrics, rankings, extra_metrics=(), tournament=None,
            standalone_criterion=None, **options):
        # Score criteria are per-tournament rows, so their annotator classes
        # can't live in the class-level dict; build them per instance.
        if tournament is not None:
            self.metric_annotator_classes = {
                **self.metric_annotator_classes,
                **criterion_metric_annotator_classes(tournament, standalone_criterion),
            }
            unavailable = [m for m in (*metrics, *extra_metrics)
                if is_criterion_metric_key(m) and m not in self.metric_annotator_classes]
            if unavailable:
                raise StandingsError(_(
                    "The speaker standings reference unavailable score criteria: %(metrics)s. "
                    "Update the speaker standings precedence and extra metrics in Setup > Standings.",
                ) % {'metrics': ", ".join(dict.fromkeys(unavailable))})
        super().__init__(metrics, rankings, extra_metrics, **options)

    @classmethod
    def get_metric_choices(cls, ranked_only=True, for_extra=False, tournament=None):
        """Adds this tournament's score criteria to the standard choices."""
        choices = super().get_metric_choices(ranked_only=ranked_only, for_extra=for_extra)
        if tournament is None:
            return choices

        criterion_choices = [
            (key, annotator.choice_label())
            for key, annotator in criterion_metric_annotator_classes(tournament).items()
        ]
        criterion_choices.sort(key=lambda x: x[1])
        return choices + criterion_choices

import logging
from copy import copy
from decimal import Decimal

from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .forms import tournament_preference_form_builder

logger = logging.getLogger(__name__)


def _all_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield from _all_subclasses(subclass)
        yield subclass


def all_presets():
    yield from _all_subclasses(PreferencesPreset)


def presets_for_form():
    presets = all_presets()
    choices = []
    for index, preset in enumerate(presets):
        if preset.show_in_list:
            choices.append((preset.name, preset.name))

    choices.sort(key=lambda x: x[1]) # Sort by name
    return choices


public_presets_for_form = [
    (True, _('Enable Public Information')),
    (False, _('Disable Public Information')),
]


data_entry_presets_for_form = [
    (False, _('Disabled (tab staff only)')),
    ("private-urls", _('Use private URLs')),
    ("public", _('Use publicly accessible form')),
]


def get_preset_from_slug(slug):
    selected_presets = [x for x in all_presets() if slugify(x.__name__) == slug]
    if len(selected_presets) == 0:
        raise ValueError("Preset {!r} not found.".format(slug))
    elif len(selected_presets) > 1:
        logger.warning("Found more than one preset for %s", slug)
    return selected_presets[0]


class PreferencesPreset:
    show_in_list                               = False

    @classmethod
    def get_preferences(cls):
        for key in dir(cls):
            if '__' in key and not key.startswith('__'):
                yield key

    @classmethod
    def get_form(cls, tournament, **kwargs):
        form = tournament_preference_form_builder(tournament, [tuple(key.split('__', 1)[::-1]) for key in cls.get_preferences()])(**kwargs)
        for field in form:
            # Copying required to avoid blanks added to list fields
            field.initial = copy(getattr(cls, field.name))
            field.changed = tournament.preferences[field.name] != getattr(cls, field.name)
        return form

    @classmethod
    def save(cls, tournament):
        for pref in cls.get_preferences():
            logger.info(f"Setting {pref} to {getattr(cls, pref)}")
            tournament.preferences[pref] = getattr(cls, pref)

    @classmethod
    def configure_feedback_questions(cls, tournament):
        pass


class AustralsPreferences(PreferencesPreset):
    name         = _("Australs Rules")
    description  = _("3 vs 3 with replies, chosen motions, intermediate brackets, "
        "one-up-one-down. Compliant with AIDA rules.")
    show_in_list = True

    # Scoring
    scoring__score_min                         = Decimal('70') # Technically the speaks
    scoring__score_max                         = Decimal('80') # range is at the adj
    scoring__score_step                        = Decimal('1')  # core's discretion (it's
    scoring__reply_score_min                   = Decimal('35.0') # not in the constitution)
    scoring__reply_score_max                   = Decimal('40.0')
    scoring__reply_score_step                  = Decimal('0.5')
    scoring__maximum_margin                    = 0.0  # Rob Confirmed
    # Draws
    draw_rules__avoid_same_institution         = True
    draw_rules__avoid_team_history             = True
    draw_rules__draw_odd_bracket               = 'intermediate_bubble_up_down'
    draw_rules__draw_side_allocations          = 'balance'
    draw_rules__draw_pairing_method            = 'slide'
    draw_rules__draw_avoid_conflicts           = 'one_up_one_down'
    # Debate Rules
    debate_rules__teams_in_debate              = 2
    debate_rules__ballots_per_debate_prelim    = 'per-adj'
    debate_rules__ballots_per_debate_elim      = 'per-adj'
    debate_rules__substantive_speakers         = 3
    debate_rules__reply_scores_enabled         = True
    debate_rules__side_names                   = 'aff-neg'
    motions__motion_vetoes_enabled             = True
    motions__enable_motions                    = True
    # Standings Rules
    standings__standings_missed_debates        = 2  # TODO= check this
    standings__team_standings_precedence       = ['wins', 'speaks_sum']
    standings__speaker_standings_precedence    = ['average'] # constitutional
    standings__speaker_standings_extra_metrics = ['stdev', 'count']
    # UI Options
    ui_options__show_team_institutions         = False
    ui_options__show_adjudicator_institutions  = True


class BritishParliamentaryPreferences(PreferencesPreset):
    name         = _("British Parliamentary Rules")
    description  = _("2 vs 2 vs 2 vs 2. Compliant with WUDC rules.")
    show_in_list = True

    scoring__score_min                         = Decimal('50')
    scoring__score_max                         = Decimal('99')
    scoring__score_step                        = Decimal('1')
    scoring__maximum_margin                    = 0.0
    scoring__teamscore_includes_ghosts         = True  # WUDC 34.9.3.2
    # Debate Rules
    debate_rules__substantive_speakers         = 2
    debate_rules__teams_in_debate              = 4
    debate_rules__ballots_per_debate_prelim    = 'per-debate'
    debate_rules__ballots_per_debate_elim      = 'per-debate'
    debate_rules__speakers_in_ballots          = 'prelim'
    debate_rules__side_names                   = 'gov-opp'
    debate_rules__reply_scores_enabled         = False
    debate_rules__preparation_time             = 15
    motions__motion_vetoes_enabled             = False
    motions__enable_motions                    = False
    # Draw Rules
    draw_rules__avoid_same_institution         = False
    draw_rules__avoid_team_history             = False
    draw_rules__bp_pullup_distribution         = 'anywhere'
    draw_rules__bp_position_cost               = 'entropy'
    draw_rules__bp_renyi_order                 = 1.0
    draw_rules__bp_position_cost_exponent      = 4.0
    draw_rules__bp_assignment_method           = 'hungarian_preshuffled'
    # Standings Rules
    standings__standings_missed_debates        = -1 # Speakers always show
    standings__team_standings_precedence       = ['points', 'speaks_sum', 'firsts', 'seconds', 'draw_strength']
    standings__speaker_standings_precedence    = ['total'] # constitutional
    standings__speaker_standings_extra_metrics = ['average', 'stdev']
    # Feedback Rules
    feedback__adj_max_score                    = 10.0
    # UI Options
    ui_options__show_team_institutions         = False
    ui_options__show_adjudicator_institutions  = True
    # Email Sending - replace "wins" by "points"
    team_points_email_subject                  = "{{ TEAM }}'s current points after {{ ROUND }}: {{ POINTS }}"
    team_points_email_message                  = ("<p>Hi {{ USER }},</p>",
        "<p>Your team ({{ TEAM }}) currently has <strong>{{ POINTS }}</strong> points in the {{ TOURN }}.",
        "<p>Current Standings: {{ URL }}</p>")


class CanadianParliamentaryPreferences(PreferencesPreset):
    name         = _("Canadian Parliamentary Rules")
    show_in_list = True
    description  = _("2 vs 2 with replies (unscored) and POIs. May require "
        "additional configuration depending on regional variations.")
    # Scoring
    scoring__score_min                         = Decimal('50')
    scoring__score_max                         = Decimal('100')
    # Debate Rules
    debate_rules__reply_scores_enabled         = False # Not scored
    debate_rules__substantive_speakers         = 2
    debate_rules__side_names                   = 'gov-opp'
    debate_rules__ballots_per_debate_prelim    = 'per-debate'
    debate_rules__ballots_per_debate_elim      = 'per-debate'
    motions__motion_vetoes_enabled             = False
    motions__enable_motions                    = False
    # Draws
    draw_rules__avoid_same_institution         = False # TBC
    draw_rules__avoid_team_history             = False # TBC
    draw_rules__draw_odd_bracket               = 'pullup_top' # TBC
    draw_rules__draw_side_allocations          = 'balance'
    draw_rules__draw_pairing_method            = 'fold' # TBC
    draw_rules__draw_avoid_conflicts           = 'off'


class AustralianEastersPreferences(AustralsPreferences):
    name         = _("Australian Easters Rules")
    show_in_list = True
    description  = _("3 vs 3 without replies, set motions, novices, intermediate "
        "bubbles, one-up-one-down. Compliant with AIDA rules.")

    # Scoring
    scoring__score_min                         = Decimal('70')
    scoring__score_max                         = Decimal('80')
    scoring__maximum_margin                    = 15.0
    # Debate Rules
    debate_rules__reply_scores_enabled         = False
    motions__motion_vetoes_enabled             = True
    motions__enable_motions                    = True
    debate_rules__ballots_per_debate_prelim    = 'per-debate'
    debate_rules__ballots_per_debate_elim      = 'per-adj'
    # Standings Rules
    standings__speaker_standings_precedence    = ['average']  # constitutional


class NZEastersPreferences(AustralsPreferences):
    name         = _("2 vs 2 Impromptu")
    show_in_list = True
    description  = _("2 vs 2 with replies, chosen motions, chosen sides, and "
        "novice statuses.")

    # Scoring
    scoring__score_min                         = Decimal('60')
    scoring__score_max                         = Decimal('80')
    scoring__reply_score_min                   = Decimal('30.0')
    scoring__reply_score_max                   = Decimal('40.0')
    # Debate Rules
    debate_rules__reply_scores_enabled         = True
    motions__motion_vetoes_enabled             = True
    motions__enable_motions                    = True
    debate_rules__substantive_speakers         = 2
    # Standings
    standings__team_standings_precedence       = ['wins', 'wbw', 'speaks_sum', 'wbw', 'draw_strength', 'wbw']
    # Draw Rules
    draw_rules__draw_side_allocations          = 'manual-ballot'
    draw_rules__draw_odd_bracket               = 'intermediate'
    draw_rules__draw_pairing_method            = 'fold'
    draw_rules__draw_avoid_conflicts           = 'off'
    draw_rules__avoid_same_institution         = False # TODO: CHECK
    draw_rules__avoid_team_history             = False # TODO: CHECK


class JoyntPreferences(AustralsPreferences):
    name         = _("3 vs 3 Prepared")
    show_in_list = True
    description  = _("3 vs 3 with preallocated sides, publicly displayed sides "
        "and motions, and novice statuses.")

    # Scoring
    scoring__score_min                         = Decimal('60')
    scoring__score_max                         = Decimal('80')
    scoring__reply_score_min                   = Decimal('30.0')
    scoring__reply_score_max                   = Decimal('40.0')
    # Debate Rules
    debate_rules__reply_scores_enabled         = True
    motions__motion_vetoes_enabled             = False
    motions__enable_motions                    = False
    debate_rules__substantive_speakers         = 3
    # Draw Rules
    draw_rules__draw_side_allocations          = 'preallocated'
    draw_rules__draw_odd_bracket               = 'intermediate2'
    draw_rules__draw_pairing_method            = 'fold'
    draw_rules__draw_avoid_conflicts           = 'off'
    draw_rules__avoid_same_institution         = False
    draw_rules__avoid_team_history             = False
    # Standings
    standings__team_standings_precedence       = ['wins', 'wbw', 'speaks_sum', 'wbw', 'draw_strength', 'wbw']
    # Public Features
    public_features__public_side_allocations   = True


class UADCPreferences(AustralsPreferences):
    name         = _("UADC Rules")
    show_in_list = True
    description  = _("3 vs 3 with replies, chosen motions, and all adjudicators "
        "can receive feedback from teams.")

    # Rules source = https://docs.google.com/document/d/10AVKBhev_OFRtorWsu2VB9B5V1a2f20425HYkC5ztMM/edit
    # Scoring
    scoring__score_min                         = Decimal('69')  # From Rules Book
    scoring__score_max                         = Decimal('81')  # From Rules Book
    scoring__score_step                        = Decimal('1')
    scoring__reply_score_min                   = Decimal('34.5')  # Not specified; assuming half of substantive
    scoring__reply_score_max                   = Decimal('42.0')  # Not specified; assuming half of substantive
    scoring__reply_score_step                  = Decimal('0.5')
    scoring__maximum_margin                    = 0.0   # TODO= check this
    scoring__margin_includes_dissenters        = False  # From Rules 20.3.2
    # Draws
    draw_rules__avoid_same_institution         = False
    draw_rules__avoid_team_history             = True
    draw_rules__draw_odd_bracket               = 'pullup_top'  # From Rules 20.10
    draw_rules__draw_pullup_restriction        = 'least_to_date'  # From Rules 20.11
    draw_rules__draw_side_allocations          = 'balance'
    draw_rules__draw_pairing_method            = 'slide'  # From rules 20.9
    draw_rules__draw_avoid_conflicts           = 'one_up_one_down'  # From rules 10.6.4
    # Debate Rules
    debate_rules__substantive_speakers         = 3
    debate_rules__reply_scores_enabled         = True
    motions__motion_vetoes_enabled             = True
    debate_rules__side_names                   = 'gov-opp'
    # Standings Rules
    standings__team_standings_precedence       = ['wins', 'speaks_sum', 'margin_avg']
    # Feedback
    feedback__adj_min_score                    = 1.0   # Explicit in the rules
    feedback__adj_max_score                    = 10.0  # Explicit in the rules
    feedback__feedback_from_teams              = 'all-adjs' # Kinda a big deal
    # UI Options
    public_features__feedback_progress         = True  # Feedback is compulsory


class WSDCPreferences(AustralsPreferences):
    name         = _("WSDC Rules")
    show_in_list = True
    description  = _("3 vs 3 with replies, chosen motions, prop/opp side labels, "
        "and all adjudicators can receive feedback from teams.")

    # Rules source = https://www.wsdcdebating.org/_files/ugd/669183_399cb065fe31455b9371bd8dfdf7e0d1.pdf
    # Score (strictly specified in the rules)
    scoring__score_min                         = Decimal('60')
    scoring__score_max                         = Decimal('80')
    scoring__score_step                        = Decimal('0.5')
    scoring__reply_score_min                   = Decimal('30.0')
    scoring__reply_score_max                   = Decimal('40.0')
    scoring__reply_score_step                  = Decimal('0.5')
    scoring__margin_includes_dissenters        = True # Important
    # Debates
    motions__motion_vetoes_enabled             = False # Single motions per round
    motions__enable_motions                    = False
    debate_rules__side_names                   = 'prop-opp'
    # Draws (exact mechanism is up to the host)
    # Draw source = https://www.wsdcdebating.org/_files/ugd/669183_acd9f3bd3ab3482ebead22ae0da74fa7.pdf
    draw_rules__avoid_same_institution         = False
    draw_rules__avoid_team_history             = True # Rule 3.9
    draw_rules__draw_pairing_method            = 'fold' # Rule 3.8
    draw_rules__draw_odd_bracket               = 'pullup_top' # Rule 3.7
    draw_rules__max_times_per_side             = 5
    # Tabbycat currently does not support WSDC-style pull up and so not fully support WSDC-style draw creation.
    # Hence, this below setting is the closest that we can manage to achive.
    # TODO: Update when Tabbycat can support WSDC pull-up.
    draw_rules__draw_side_allocations          = 'balance'
    draw_rules__draw_avoid_conflicts           = 'graph_one'
    draw_rules__draw_pullup_restriction        = 'lowest_ds_wins'
    # Standings
    standings__team_standings_precedence       = ['wins', 'num_adjs', 'speaks_avg'] # Rule 3.2 (2023 version)
    standings__speaker_standings_precedence    = ['average']  # speakers sub in/out
    # UI Options
    ui_options__show_team_institutions         = False
    ui_options__show_adjudicator_institutions  = False


class SDLFormatPreferences(PreferencesPreset):
    name         = _("SDL Format")
    show_in_list = True
    description  = _("3 vs 3 with replies and cross-examinations, pre-allocated "
        "sides, private URL ballot entry, and SDL standings and draw rules.")

    # Score Rules
    scoring__score_min                         = Decimal('10')
    scoring__score_max                         = Decimal('30')
    scoring__score_step                        = Decimal('1')
    scoring__reply_score_min                   = Decimal('8')
    scoring__reply_score_max                   = Decimal('24')
    scoring__reply_score_step                  = Decimal('1')
    scoring__cross_score_min                   = Decimal('8')
    scoring__cross_score_max                   = Decimal('24')
    scoring__cross_score_step                  = Decimal('1')
    scoring__margin_includes_dissenters        = False
    scoring__teamscore_includes_ghosts         = True

    # Draw Rules
    draw_rules__adj_min_voting_score           = 1.0
    draw_rules__adj_conflict_penalty           = 1000000
    draw_rules__adj_history_penalty            = 10000
    draw_rules__preformed_panel_mismatch_penalty = 10000000
    draw_rules__team_institution_penalty       = 1
    draw_rules__team_history_penalty           = 9999999999999
    draw_rules__avoid_same_institution         = False
    draw_rules__avoid_team_history             = True
    draw_rules__pullup_debates_penalty         = 0
    draw_rules__side_penalty                   = 1000000000000000000
    draw_rules__pairing_penalty                = 10000000000000
    draw_rules__max_times_per_side             = 2
    draw_rules__draw_odd_bracket               = 'pullup_top'
    draw_rules__draw_side_allocations          = 'preallocated'
    draw_rules__draw_pairing_method            = 'fold'
    draw_rules__draw_avoid_conflicts           = 'one_up_one_down'
    draw_rules__draw_pullup_restriction        = 'none'
    draw_rules__draw_pullup_penalty            = 5
    draw_rules__bp_pullup_distribution         = 'anywhere'
    draw_rules__bp_position_cost               = 'entropy'
    draw_rules__bp_renyi_order                 = 1.0
    draw_rules__bp_position_cost_exponent      = 4.0
    draw_rules__bp_assignment_method           = 'hungarian_preshuffled'
    draw_rules__draw_skip_adj_checkins         = False
    draw_rules__no_panellist_position          = False
    draw_rules__no_trainee_position            = False
    draw_rules__bye_team_results               = 'average'
    draw_rules__bye_team_selection             = 'middle_odd_bracket'
    draw_rules__max_times_on_one_side          = 0

    # Feedback
    feedback__adj_min_score                    = 0.0
    feedback__adj_max_score                    = 3.0
    feedback__feedback_affects_adjudicator_scores = False
    feedback__feedback_paths                   = 'with-p-on-c'
    feedback__feedback_from_teams              = 'orallist'
    feedback__show_unexpected_feedback         = True
    feedback__show_unaccredited                = False

    # Debate Rules
    debate_rules__teams_in_debate              = 2
    debate_rules__ballots_per_debate_prelim    = 'per-adj'
    debate_rules__ballots_per_debate_elim      = 'per-adj'
    debate_rules__adjudicator_weighting        = 'weighted-to-three'
    debate_rules__winners_in_ballots           = 'high-points'
    debate_rules__speakers_in_ballots          = 'always'
    debate_rules__substantive_speakers         = 3
    debate_rules__reply_scores_enabled         = True
    debate_rules__cross_examinations_enabled   = True
    debate_rules__require_substantive_for_reply = True
    debate_rules__speaker_ranks                = 'none'
    debate_rules__preparation_time             = -1
    debate_rules__enable_forfeits              = True
    debate_rules__side_names                   = 'aff-neg'

    # Standings
    standings__standings_missed_debates        = 2
    standings__standings_missed_replies        = 2
    standings__team_standings_precedence       = ['wins', 'num_adjs', 'speaks_sum']
    standings__team_standings_extra_metrics    = []
    standings__speaker_standings_precedence    = ['average', 'trimmed_mean']
    standings__speaker_standings_extra_metrics = []

    # Tab Release / Public Features
    public_features__public_schedule           = False
    public_features__feedback_progress         = False
    public_features__public_breaking_adjs      = False
    public_features__public_break_metrics_to_show = -1
    public_features__public_breaking_teams     = False
    public_features__public_record             = True
    public_features__public_team_standings     = False
    public_features__public_motions            = False
    public_features__public_results            = False
    public_features__public_draw               = 'current'
    public_features__public_side_allocations   = False
    public_features__public_break_categories   = False
    public_features__public_checkins           = False
    public_features__public_diversity          = False
    public_features__public_institutions_list  = False
    public_features__public_participants       = True
    public_features__search_engine_indexing    = 'all'

    # Data Entry
    data_entry__ballots_hide_motions           = False
    data_entry__individual_ballots             = True
    data_entry__enable_postponements           = False
    data_entry__feedback_return_location       = 'TBA'
    data_entry__score_return_location          = 'TBA'
    data_entry__ballots_confirm_digits         = True
    data_entry__checkin_window_venues          = 2.0
    data_entry__checkin_window_people          = 12.0
    data_entry__public_checkins_submit         = False
    data_entry__assistant_access               = 'all_areas'
    data_entry__enable_blind_checks            = False
    data_entry__disable_ballot_confirms        = False
    data_entry__ballot_export_format           = 'off'
    data_entry__slider_ballot_ui               = True
    data_entry__participant_feedback           = 'private-urls'
    data_entry__participant_ballots            = 'private-urls'

    # UI Options
    ui_options__show_seed_in_importer          = 'off'
    ui_options__show_speakers_in_draw          = True
    ui_options__show_adjudicator_institutions  = True
    ui_options__show_team_institutions         = False
    ui_options__show_emoji                     = True
    ui_options__participant_code_names         = 'off'
    ui_options__team_code_names                = 'off'
    ui_options__show_splitting_adjudicators    = False

    # Motions
    motions__enable_motion_reuse               = True
    motions__public_motions_order              = 'reverse'
    motions__show_motions_in_results           = True
    motions__motion_vetoes_enabled             = False
    motions__enable_motions                    = False

    @classmethod
    def configure_feedback_questions(cls, tournament):
        from django.contrib.contenttypes.models import ContentType
        from django.db import transaction

        from adjfeedback.models import AdjudicatorFeedbackQuestion

        existing = AdjudicatorFeedbackQuestion.objects.filter(tournament=tournament)
        existing_references = set(existing.values_list('reference', flat=True))
        if existing_references and existing_references != {'agree', 'comments'}:
            logger.info("Skipping SDL feedback question setup for %s because custom questions already exist", tournament)
            return

        content_type = ContentType.objects.get(app_label="adjfeedback", model="adjudicatorfeedback")

        scale_help = "1 - Úplne nesúhlasím, 10 - Úplne súhlasím"
        questions = [
            {
                "seq": 1,
                "text": "Súhlasíme s rozhodnutím",
                "name": "Súhlas s rozhodnutím",
                "reference": "suhlasime_s_rozhodnutim",
                "from_team": True,
                "from_adj": False,
                "answer_type": AdjudicatorFeedbackQuestion.AnswerType.SINGLE_SELECT,
                "choices": ["Áno", "Nie"],
            },
            {
                "seq": 2,
                "text": "Debatu sme",
                "name": "Debatu sme",
                "reference": "debatu_sme",
                "from_team": True,
                "from_adj": False,
                "answer_type": AdjudicatorFeedbackQuestion.AnswerType.SINGLE_SELECT,
                "choices": ["Vyhrali", "Prehrali"],
            },
            {
                "seq": 3,
                "text": "Rozhodnutie bolo podané jasne a zrozumiteľne",
                "name": "Jasnosť rozhodnutia",
                "reference": "rozhodnutie_jasne",
                "from_team": True,
                "from_adj": False,
                "answer_type": AdjudicatorFeedbackQuestion.AnswerType.SINGLE_SELECT,
                "choices": [str(i) for i in range(1, 11)],
                "help_text": scale_help,
            },
            {
                "seq": 4,
                "text": "Spätná väzba bola prínosná",
                "name": "Prínos spätnej väzby",
                "reference": "spatna_vazba_prinosna",
                "from_team": True,
                "from_adj": False,
                "answer_type": AdjudicatorFeedbackQuestion.AnswerType.SINGLE_SELECT,
                "choices": [str(i) for i in range(1, 11)],
                "help_text": scale_help,
            },
            {
                "seq": 5,
                "text": "Komentáre k rozhodnutiu",
                "name": "Komentáre k rozhodnutiu",
                "reference": "komentare_k_rozhodnutiu",
                "from_team": True,
                "from_adj": False,
                "answer_type": AdjudicatorFeedbackQuestion.AnswerType.LONGTEXT,
            },
            {
                "seq": 6,
                "text": "Posudok",
                "name": "Posudok",
                "reference": "posudok",
                "from_team": False,
                "from_adj": True,
                "answer_type": AdjudicatorFeedbackQuestion.AnswerType.SINGLE_SELECT,
                "choices": ["Pozitívny", "Neutrálny", "Negatívny"],
            },
            {
                "seq": 7,
                "text": "Komentáre",
                "name": "Komentáre",
                "reference": "komentare_rozhodca",
                "from_team": False,
                "from_adj": True,
                "answer_type": AdjudicatorFeedbackQuestion.AnswerType.LONGTEXT,
                "required": False,
            },
        ]

        with transaction.atomic():
            existing.delete()

            for question_spec in questions:
                question = question_spec.copy()
                AdjudicatorFeedbackQuestion.objects.create(
                    tournament=tournament,
                    for_content_type=content_type,
                    required=question.pop("required", True),
                    min_value=question.pop("min_value", None),
                    max_value=question.pop("max_value", None),
                    choices=question.pop("choices", []),
                    help_text=question.pop("help_text", ""),
                    **question,
                )


class JDLFormatPreferences(SDLFormatPreferences):
    name         = _("JDL 2nd Category")
    description  = _("2 vs 2 with replies, no cross-examinations, pre-allocated "
        "sides, private URL ballot entry, and JDL-style standings and draw rules.")

    debate_rules__substantive_speakers         = 2
    debate_rules__cross_examinations_enabled   = False


class JDLFirstCategoryPreferences(JDLFormatPreferences):
    name         = _("JDL 1st Category")
    description  = _("One-speaker JDL format with one team per room, no opponent, "
        "pre-allocated affirmative/negative sides, and score-based standings.")

    scoring__margin_includes_dissenters        = True

    draw_rules__draw_side_allocations          = 'preallocated'
    draw_rules__bye_team_selection             = 'off'

    debate_rules__teams_in_debate              = 1
    debate_rules__solo_speech_format           = True
    debate_rules__winners_in_ballots           = 'none'
    debate_rules__substantive_speakers         = 1
    debate_rules__reply_scores_enabled         = False
    debate_rules__cross_examinations_enabled   = False
    debate_rules__require_substantive_for_reply = False
    debate_rules__side_names                   = 'aff-neg'

    data_entry__individual_ballots             = False
    data_entry__ballot_export_format           = 'jdl_first_category'

    standings__team_standings_precedence       = ['speaks_sum', 'num_adjs']
    standings__team_standings_extra_metrics    = []
    standings__speaker_standings_precedence    = ['average', 'trimmed_mean']
    standings__speaker_standings_extra_metrics = []


class NonLeagueTournamentsPreferences(SDLFormatPreferences):
    name         = _("Non-league tournaments (GJH Open, MDIK Open)")
    description  = _("SDL format without cross-examinations, used for non-league "
        "tournaments such as GJH Open and MDIK Open.")

    debate_rules__cross_examinations_enabled   = False


class APDAPreferences(PreferencesPreset):
    name = _("APDA Rules")
    show_in_list = True
    description = _("2 vs 2 with speech rankings and byes")

    scoring__score_min                         = Decimal('15')
    scoring__score_max                         = Decimal('40')
    motions__motion_vetoes_enabled             = False # Single motions per round
    motions__enable_motions                    = False
    draw_rules__draw_odd_bracket               = 'pullup_bottom'
    draw_rules__team_institution_penalty       = 1000
    draw_rules__team_history_penalty           = 100000
    draw_rules__draw_pairing_method            = 'fold'
    draw_rules__draw_pullup_restriction        = 'least_to_date'
    draw_rules__bye_team_results               = 'points'
    draw_rules__bye_team_selection             = 'lowest'
    draw_rules__draw_avoid_conflicts           = 'graph'
    draw_rules__pullup_debates_penalty         = 10000
    draw_rules__side_penalty                   = 100
    draw_rules__pairing_penalty                = 1
    debate_rules__ballots_per_debate_prelim    = 'per-debate'
    debate_rules__ballots_per_debate_elim      = 'per-debate'
    debate_rules__winners_in_ballots           = 'tied-points'
    debate_rules__speakers_in_ballots          = 'prelim'
    debate_rules__substantive_speakers         = 2
    debate_rules__side_names                   = 'gov-opp'
    debate_rules__reply_scores_enabled         = False
    debate_rules__speaker_ranks                = 'any'
    standings__speaker_standings_precedence    = ['average', 'srank', 'trimmed_mean']


class PublicSpeaking(PreferencesPreset):
    name = _("Public Speaking")
    show_in_list = True
    description = _("Arbitrary number of teams per room, one speech each, no team points")

    scoring__score_min                         = Decimal('50')
    scoring__score_max                         = Decimal('99')
    scoring__score_step                        = Decimal('1')
    scoring__maximum_margin                    = 0.0
    scoring__margin_includes_dissenters        = True  # Disables win/rank calculations
    # Debate Rules
    debate_rules__substantive_speakers         = 1
    debate_rules__teams_in_debate              = 6
    debate_rules__ballots_per_debate_prelim    = 'per-adj'
    debate_rules__ballots_per_debate_elim      = 'per-adj'
    debate_rules__speakers_in_ballots          = 'prelim'
    debate_rules__side_names                   = '1-2'
    debate_rules__reply_scores_enabled         = False
    motions__motion_vetoes_enabled             = False
    motions__enable_motions                    = False
    # Draw Rules
    draw_rules__avoid_same_institution         = False
    draw_rules__avoid_team_history             = False
    # Standings
    standings__team_standings_precedence       = ['speaks_avg']


class PublicInformation(PreferencesPreset):
    name         = _("Public Information Options")
    show_in_list = False
    description  = _("For tournaments hosted online: this sets it up so that "
        "people can access the draw and other generally useful information "
        "via the tab site.")

    public_features__public_draw               = 'current'
    public_features__public_break_categories   = True
    public_features__public_results            = True
    public_features__public_motions            = True
    public_features__public_team_standings     = True


class TabRelease(PreferencesPreset):
    name         = _("Tab Release Options")
    show_in_list = False
    description  = _("For when a tab is ready to be released. This will publicly "
        "display the results of all rounds, the team tab, the speaker tab, etc")

    tab_release__team_tab_released             = True
    tab_release__speaker_tab_released          = True
    tab_release__motion_tab_released           = True
    tab_release__ballots_released              = True
    tab_release__all_results_released          = True
    public_features__public_diversity          = True
    public_features__public_results            = True
    public_features__public_breaking_teams     = True
    public_features__public_breaking_adjs      = True
    # Disable
    public_features__public_checkins           = False
    public_features__public_team_standings     = False
    public_features__public_draw               = 'off'
    public_features__public_break_categories   = False


class PrivateURLs(PreferencesPreset):
    name = _("Use Private URLs")
    show_in_list = False
    description = _("Enables participant data entry through private URLs.")

    data_entry__participant_ballots            = 'private-urls'
    data_entry__participant_feedback           = 'private-urls'


class PublicForms(PreferencesPreset):
    name = _("Use Public Forms")
    show_in_list = False
    description = _("Enables participant data entry through public forms.")

    data_entry__participant_ballots            = 'public'
    data_entry__participant_feedback           = 'public'

import logging
from decimal import Decimal, ROUND_HALF_UP
from itertools import product
from typing import TYPE_CHECKING

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django import forms
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from draw.models import Debate, DebateTeam
from draw.types import DebateSide
from options.utils import use_team_code_names_data_entry
from participants.models import Speaker, Team
from participants.templatetags.team_name_for_data_entry import team_name_for_data_entry
from tournaments.utils import get_side_name

from .bye_scores import sync_forfeit_ballot
from .consumers import BallotResultConsumer, BallotStatusConsumer
from .result import (ConsensusDebateResult, ConsensusDebateResultWithScores,
                     DebateResultByAdjudicator, DebateResultByAdjudicatorWithScores)
from .utils import get_status_meta, side_and_position_names

if TYPE_CHECKING:
    from .models import BallotSubmission

logger = logging.getLogger(__name__)


class FormConstructionError(Exception):
    pass


# ==============================================================================
# Result/ballot custom fields
# ==============================================================================

class TournamentPasswordField(forms.CharField):

    def __init__(self, *args, **kwargs):
        if 'tournament' in kwargs:
            tournament = kwargs.pop('tournament')
            self.password = tournament.pref('public_password')
        else:
            raise TypeError("'tournament' is a required keyword argument")
        kwargs.setdefault('label', _("Tournament password"))
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if value != self.password:
            raise forms.ValidationError(_("That password isn't correct."))
        return value


class BaseScoreField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        """Takes an additional optional keyword argument: tournament,
        the Tournament used to configure the field."""

        tournament = kwargs.pop('tournament', None)
        if tournament:
            min_value  = tournament.pref(self.CONFIG_MIN_VALUE_FIELD)
            max_value  = tournament.pref(self.CONFIG_MAX_VALUE_FIELD)
            step_value = tournament.pref(self.CONFIG_STEP_VALUE_FIELD)
        else:
            min_value  = self.DEFAULT_MIN_VALUE
            max_value  = self.DEFAULT_MAX_VALUE
            step_value = self.DEFAULT_STEP_VALUE
        self.step_value = kwargs.get('step_value', step_value)

        kwargs.setdefault('min_value', min_value)
        kwargs.setdefault('max_value', max_value)
        kwargs.setdefault('step_size', self.step_value)

        super().__init__(*args, **kwargs)


class MotionModelChoiceField(forms.ModelChoiceField):
    to_field_name = 'motion_id'

    def label_from_instance(self, obj):
        return "%d. %s" % (obj.seq, obj.motion.text)


class SubstantiveScoreField(BaseScoreField):
    CONFIG_MIN_VALUE_FIELD  = 'score_min'
    CONFIG_MAX_VALUE_FIELD  = 'score_max'
    CONFIG_STEP_VALUE_FIELD = 'score_step'
    DEFAULT_MIN_VALUE = 68
    DEFAULT_MAX_VALUE = 82
    DEFAULT_STEP_VALUE = 1


class ReplyScoreField(BaseScoreField):
    CONFIG_MIN_VALUE_FIELD  = 'reply_score_min'
    CONFIG_MAX_VALUE_FIELD  = 'reply_score_max'
    CONFIG_STEP_VALUE_FIELD = 'reply_score_step'
    DEFAULT_MIN_VALUE = 34.0
    DEFAULT_MAX_VALUE = 41.0
    DEFAULT_STEP_VALUE = 0.5


class CrossTotalScoreField(BaseScoreField):
    CONFIG_MIN_VALUE_FIELD  = 'cross_score_min'
    CONFIG_MAX_VALUE_FIELD  = 'cross_score_max'
    CONFIG_STEP_VALUE_FIELD = 'cross_score_step'
    DEFAULT_MIN_VALUE = 2.0
    DEFAULT_MAX_VALUE = 6.0
    DEFAULT_STEP_VALUE = 0.5






def broadcast_results(ballotsub: 'BallotSubmission', debate: Debate):
    t = debate.round.tournament

    # 5. Notify the Latest Results consumer (for results/overview)
    if ballotsub.confirmed and debate.result_status == Debate.STATUS_CONFIRMED:
        group_name = BallotResultConsumer.group_prefix + "_" + t.slug
        async_to_sync(get_channel_layer().group_send)(group_name, {
            "type": "send_json",
            "data": ballotsub.serialize_like_actionlog,
        })

    # 6. Notify the Results Page/Ballots Status Graph
    group_name = BallotStatusConsumer.group_prefix + "_" + t.slug
    meta = get_status_meta(debate)
    async_to_sync(get_channel_layer().group_send)(group_name, {
        "type": "send_json",
        "data": {
            'status': debate.result_status,
            'icon': meta[0],
            'class': meta[1],
            'sort': meta[2],
            'ballot': ballotsub.serialize(t),
            'round': debate.round_id,
        },
    })


# ==============================================================================
# Result/ballot forms
# ==============================================================================

class BallotTextFeedbackForm(forms.Form):
    text = forms.CharField(
        label=_("Poznámky"),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': _("Pridaj poznámky, ktoré si tímy prečítajú v súkromnom zobrazení ballotu."),
        }),
    )

    def __init__(self, *args, initial_text=None, **kwargs):
        if initial_text is not None:
            initial = kwargs.pop('initial', {})
            initial['text'] = initial_text
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def save(self, ballot_submission: 'BallotSubmission', adjudicator=None, user=None):
        from .models import BallotTextFeedback

        text = self.cleaned_data['text'].strip()
        if not text:
            BallotTextFeedback.objects.filter(ballot_submission=ballot_submission).delete()
            return None

        defaults = {
            'text': text,
            'updated_by_adjudicator': adjudicator,
            'updated_by_user': user if getattr(user, 'is_authenticated', False) else None,
        }
        feedback, _ = BallotTextFeedback.objects.update_or_create(
            ballot_submission=ballot_submission, defaults=defaults)
        return feedback


class BaseResultForm(forms.Form):
    """Base class for forms that report results. Contains fields and methods
    common to absolutely everything (which isn't very much)."""

    discarded = forms.BooleanField(required=False)

    result_class = None

    def __init__(self, ballotsub, tabroom, password=False, *args, **kwargs):
        self.ballotsub = ballotsub

        self.debate = ballotsub.debate
        self.tournament = self.debate.round.tournament
        self.criteria = self.debate.round.tournament.scorecriterion_set.all().order_by('seq')
        self.crosses = self._load_crosses()
        self.crosses_enabled = (
            self.tournament.pref('teams_in_debate') == 2 and
            self.tournament.pref('cross_examinations_enabled')
        )
        if not self.crosses_enabled:
            self.crosses = []

        self.result = kwargs.pop('result', self.result_class(
            self.ballotsub,
            criteria=self.criteria,
            crosses=self.crosses,
            using_cross_examinations=self.crosses_enabled,
        ))
        self.filled = kwargs.pop('filled', False)
        self.allow_default_criteria_on_prefill = kwargs.pop('allow_default_criteria_on_prefill', False)
        super().__init__(*args, **kwargs)

        self.has_tournament_password = password and self.tournament.pref('public_use_password')
        self.tabroom = tabroom
        self.use_codes = use_team_code_names_data_entry(self.tournament, tabroom)

        status_choices = Debate.STATUS_CHOICES if self.tournament.pref('enable_postponements') else Debate.STATUS_CHOICES_RESTRICTED
        self.fields['debate_result_status'] = forms.ChoiceField(choices=status_choices)
        self.fields['confirmed'] = forms.BooleanField(required=False, disabled=ballotsub.single_adj)

        self.initial.update({
            'debate_result_status': self.debate.result_status,
            'confirmed': self.ballotsub.confirmed,
            'discarded': self.ballotsub.discarded,
        })

        if self.has_tournament_password:
            self.fields['password'] = TournamentPasswordField(tournament=self.tournament)

    def _load_crosses(self):
        return list(self.tournament.crossexamination_set.order_by('seq'))

    def _side_name(self, side):
        return get_side_name(self.tournament, side, 'full')

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('discarded') and cleaned_data.get('confirmed'):
            for field in ('discarded', 'confirmed'):
                self.add_error(field, forms.ValidationError(
                    _("The ballot set can't be both discarded and confirmed."),
                    code='discard_confirm',
                ))

        data_confirmed = cleaned_data.get('debate_result_status') == Debate.STATUS_CONFIRMED and not cleaned_data.get('confirmed')
        if data_confirmed and self.debate.confirmed_ballot is None:
            self.add_error('debate_result_status', forms.ValidationError(
                _("The debate status can't be confirmed unless one of the ballot sets is confirmed."),
                code='status_confirm',
            ))

        return cleaned_data

    def save(self):

        # 1. Unconfirm the other, if necessary
        if self.cleaned_data['confirmed']:
            if self.debate.confirmed_ballot != self.ballotsub and self.debate.confirmed_ballot is not None:
                self.debate.confirmed_ballot.confirmed = False
                self.debate.confirmed_ballot.save()

        # 2. Save ballot submission so that we can create related objects
        if self.ballotsub.id is None:
            self.ballotsub.save()

        # 3. Save the specifics of the ballot
        self.save_ballot()

        # 4. Save ballot and result status
        self.ballotsub.discarded = self.cleaned_data['discarded']
        self.ballotsub.confirmed = self.cleaned_data['confirmed']
        self.ballotsub.save()

        self.debate.result_status = self.cleaned_data['debate_result_status']
        self.debate.save()

        # Need to provide a timestamp immediately for BallotStatusConsumer
        # as it will broadcast before the view finishes assigning one
        if self.ballotsub.confirmed:
            self.ballotsub.confirm_timestamp = timezone.now()

        broadcast_results(self.ballotsub, self.debate)

        return self.ballotsub

    def save_ballot(self):
        raise NotImplementedError


class BaseBallotSetForm(BaseResultForm):
    """Form for data entry for a single ballot set. Responsible for presenting
    the part that looks like a ballot, i.e. speaker names and scores for each
    adjudicator. Not responsible for controls that submit the form or anything
    like that.

    There are lots of fields that are conditionally displayed according to user
    preference. Most of these (for example, motions) are simply the presence or
    absence thereof, and it is easiest to govern these using if-else switches.
    For more involved customisations, like there is a ballot per adjudicator
    (voting) or a single ballot for the debate (consensus), we use subclasses.
    """

    def __init__(self, ballotsub, *args, **kwargs):
        self.vetos = kwargs.pop('vetos', None)
        super().__init__(ballotsub, *args, **kwargs)

        self.adjudicators = list(self.debate.adjudicators.voting())
        self.motions = self.debate.round.roundmotion_set.order_by('seq').select_related('motion')

        self.sides = sorted([dt.side for dt in self.debate.debateteam_set.all()])
        self.positions = self.tournament.positions
        self.last_substantive_position = self.tournament.last_substantive_position  # also used in template
        self.reply_position = self.tournament.reply_position  # also used in template

        self.get_preferences_options()
        self.criteria_by_position = self._build_criteria_by_position()

        self.create_fields()
        self.set_tab_indices()
        self.initial.update(self.initial_data())

    def get_preferences_options(self):
        self.using_motions = self.tournament.pref('enable_motions')
        self.using_vetoes = self.tournament.pref('motion_vetoes_enabled')
        self.using_replies = self.tournament.pref('reply_scores_enabled')
        self.using_declared_winner = self.tournament.pref('winners_in_ballots') != 'none'
        self.declared_winner = self.tournament.pref('winners_in_ballots')
        self.bypassing_checks = self.tournament.pref('disable_ballot_confirms') and not self.ballotsub.single_adj
        self.max_margin = self.tournament.pref('maximum_margin')
        self.choosing_sides = (self.tournament.pref('draw_side_allocations') == 'manual-ballot' and
                               self.tournament.pref('teams_in_debate') == 2)
        self.using_speaker_ranks = self.tournament.pref('speaker_ranks') != 'none'
        self.using_cross_examinations = self.has_scores and self.crosses_enabled

    def _build_criteria_by_position(self):
        criteria = list(self.criteria)
        return {
            pos: [
                criterion for criterion in criteria
                if criterion.applies_to_position(pos, self.reply_position, self.using_replies)
            ]
            for pos in self.positions
        }

    def criteria_for_position(self, pos):
        return self.criteria_by_position.get(pos, [])

    # --------------------------------------------------------------------------
    # Field names and field convenience functions
    # --------------------------------------------------------------------------

    @staticmethod
    def _fieldname_motion_veto(side):
        return '%(side)d_motion_veto' % {'side': side}

    # --------------------------------------------------------------------------
    # Form set-up
    # --------------------------------------------------------------------------

    def create_fields(self):
        """Dynamically generate fields for this ballot:
         - choose_sides,         if sides need to be chosen by the user
         - motion,               if there is more than one motion
         - <side>_motion_veto,   if motion vetoes are being noted, one for each team
         - <side>_speaker_s#,    one for each speaker
         - <side>_srank_s#,      if speech ranks are enabled
         - <side>_ghost_s#,      whether score should be a duplicate
        """

        # 1. Choose sides field
        if self.choosing_sides:  # false in BP regardless of choosing sides setting
            teams = self.debate.teams
            assert len(teams) == 2
            side_choices = [
                (None, _("---------")),
                *[(str(teams[i].id) + "," + str(teams[(i+1) % 2].id),
                    _("%(aff_team)s affirmed, %(neg_team)s negated") % {
                        'aff_team': team_name_for_data_entry(teams[i], self.use_codes),
                        'neg_team': team_name_for_data_entry(teams[(i+1) % 2], self.use_codes),
                }) for i in range(2)],
            ]
            self.fields['choose_sides'] = forms.TypedChoiceField(
                choices=side_choices,
                coerce=lambda x: tuple(Team.objects.get(id=int(v)) for v in x.split(",")),
            )
            for team in self.debate.teams:
                self.fields['team_%d' % team.id] = forms.ModelChoiceField(queryset=team.speakers, required=False)

        # 2. Motion fields
        if self.using_motions:
            self.fields['motion'] = MotionModelChoiceField(queryset=self.motions,
                required=True)

        if self.using_vetoes:
            for side in self.sides:
                self.fields[self._fieldname_motion_veto(side)] = MotionModelChoiceField(
                    label=_("%(side)s's motion veto") % {'side': get_side_name(self.tournament, side, 'full').title()},
                    queryset=self.motions, required=False,
                )

        # 3. Speaker fields
        self.create_participant_fields()

    def create_declared_winner_dropdown(self):
        """This method creates a drop-down with a list of the teams in the debate"""
        teams = [(s, _("%(team)s (%(side)s)") % {
            'team': team_name_for_data_entry(self.debate.get_team(s), self.use_codes), 'side': get_side_name(self.tournament, s, 'full')}) for s in self.sides]
        return forms.TypedChoiceField(
            label=_("Winner"), required=True, empty_value=None,
            choices=[(None, _("---------"))] + teams,
        )

    def initial_data(self):
        """Generates dictionary of initial form data."""

        initial = {}

        # When bypassing confirmations we just pre-check
        if self.bypassing_checks:
            initial['confirmed'] = True
            # For new ballots default to confirmed status
            if self.debate.result_status == Debate.STATUS_NONE:
                initial['debate_result_status'] = Debate.STATUS_CONFIRMED

        # If sides are already confirmed, initialise the sides choice field
        if self.choosing_sides and self.ballotsub.debate.sides_confirmed:
            try:
                initial['choose_sides'] = str(self.debate.teams[DebateSide.AFF].id) + "," + str(self.debate.teams[DebateSide.NEG].id)
            except DebateTeam.DoesNotExist:
                pass

        # Generally, initialise the motion to what is currently in the database.
        # But if there is only one motion and no motion is currently stored in
        # the database for this round, then default to the only motion there is.
        if self.using_motions:
            if not self.ballotsub.motion and self.motions.count() == 1:
                initial['motion'] = self.motions.get()
            else:
                initial['motion'] = self.ballotsub.roundmotion

        if self.ballotsub.id is not None or self.filled:
            if self.using_vetoes:
                for side in self.sides:
                    if self.vetos is None:
                        dtmp = self.ballotsub.debateteammotionpreference_set.filter(
                                debate_team__side=side, preference=3).first()
                    else:
                        dtmp = self.vetos.get(side)
                    if dtmp:
                        initial[self._fieldname_motion_veto(side)] = dtmp.roundmotion

            initial.update(self.initial_from_result(self.result))

        return initial

    def set_tab_indices(self):
        """Sets all the tab indices in the form."""
        # make a list for field names, then set them all at the end
        order = list()

        if 'choose_sides' in self.fields:
            order.append('choose_sides')

        if self.motions.count() > 1:
            order.append('motion')
            order.extend(self._fieldname_motion_veto(side) for side in self.sides)

        order.extend(self.list_participant_fields())
        order.extend(self.list_score_fields())

        if 'password' in self.fields:
            order.append('password')

        order.extend(['confirmed', 'discarded', 'debate_result_status'])

        if self.motions.count() <= 1:
            order.append('motion')
            order.extend(self._fieldname_motion_veto(side) for side in self.sides)

        # now, set
        for i, name in enumerate(order, start=3): # Start at 3 to account for front-end only fields
            try:
                self.fields[name].widget.attrs['tabindex'] = i
            except KeyError as e:
                logger.debug("Skipping tab index for field not found: %s", e)

        self.nexttabindex = i + 1  # for other UI elements in the tempate

    # --------------------------------------------------------------------------
    # Saving
    # --------------------------------------------------------------------------

    def save_ballot(self):
        forfeit_side = self._selected_forfeit_side() if hasattr(self, '_selected_forfeit_side') else None

        # 4. Save the sides
        if self.choosing_sides:
            self.result.set_sides(*self.cleaned_data['choose_sides'])

        # 5. Save motions
        if self.using_motions and self.cleaned_data.get('motion'):
            self.ballotsub.motion = self.cleaned_data['motion'].motion
        elif self.motions.count() == 1:
            self.ballotsub.motion = self.motions.get().motion

        if self.using_vetoes:
            for side in self.sides:
                motion_veto = self.cleaned_data.get(self._fieldname_motion_veto(side))
                debate_team = self.debate.get_dt(side)
                if motion_veto:
                    self.ballotsub.debateteammotionpreference_set.update_or_create(
                        debate_team=debate_team, preference=3,
                        defaults=dict(motion=motion_veto.motion))
                else:
                    self.ballotsub.debateteammotionpreference_set.filter(
                        debate_team=debate_team, preference=3).delete()

        # 6. Save participant fields
        self.save_participant_fields(self.result)

        self.result.save()
        if forfeit_side is not None:
            sync_forfeit_ballot(self.ballotsub, forfeit_side)

    # --------------------------------------------------------------------------
    # Template access methods
    # --------------------------------------------------------------------------

    def motion_veto_fields(self):
        """Generator to allow easy iteration through the motion veto fields."""
        for side in self.sides:
            yield self[self._fieldname_motion_veto(side)]


class ScoresMixin:

    has_scores = True

    # --------------------------------------------------------------------------
    # Field names and field convenience functions
    # --------------------------------------------------------------------------

    @staticmethod
    def _fieldname_speaker(side, pos):
        return '%(side)d_speaker_s%(pos)d' % {'side': side, 'pos': pos}

    @staticmethod
    def _fieldname_ghost(side, pos):
        return '%(side)d_ghost_s%(pos)d' % {'side': side, 'pos': pos}

    @staticmethod
    def _fieldname_forfeit(side):
        return '%(side)d_forfeit' % {'side': side}

    # --------------------------------------------------------------------------
    # Form set-up
    # --------------------------------------------------------------------------

    def _has_forfeit_fields(self):
        return len(self.sides) == 2

    def _selected_forfeit_side(self):
        if not self._has_forfeit_fields():
            return None
        for side in self.sides:
            if self.cleaned_data.get(self._fieldname_forfeit(side), False):
                return side
        return None

    def create_participant_fields(self):
        if self._has_forfeit_fields():
            for side in self.sides:
                self.fields[self._fieldname_forfeit(side)] = forms.BooleanField(required=False)

        for side, pos in product(self.sides, self.positions):

            # 3(a). Speaker identity
            if self.choosing_sides:
                queryset = Speaker.objects.filter(team__in=self.debate.teams)
            else:
                queryset = self.debate.get_team(side).speakers

            self.fields[self._fieldname_speaker(side, pos)] = forms.ModelChoiceField(
                queryset=queryset, required=False)
            if len(queryset) == 1:
                self.fields[self._fieldname_speaker(side, pos)].initial = queryset[0]

            # 3(b). Ghost fields
            self.fields[self._fieldname_ghost(side, pos)] = forms.BooleanField(required=False,
                label=_("Mark as a duplicate speech"), label_suffix="")

        self.create_score_fields()

    def list_participant_fields(self):
        order = []
        for side, pos in product(self.sides, self.positions):
            order.append(self._fieldname_speaker(side, pos))
        return order

    def list_score_fields(self):
        """Should be overridden by subclasses; the default implementation
        returns an empty list."""
        return []

    def initial_from_result(self, result):
        """Generates the initial from data that uses the DebateResult for the
        debate. Making this its own function allows subclasses to extend this so
        that it can use the same DebateResult as the super class."""
        initial = {}
        if not result.is_voting and all(result.teamscore_field_score(side) is None for side in self.sides) and result.get_winner():
            forfeiter = next(iter(set(self.sides) - result.get_winner()))
            initial[self._fieldname_forfeit(forfeiter)] = True
            return initial

        for side, pos in product(self.sides, self.positions):
            initial[self._fieldname_speaker(side, pos)] = result.get_speaker(side, pos)
            initial[self._fieldname_ghost(side, pos)] = result.get_ghost(side, pos)
        return initial

    # --------------------------------------------------------------------------
    # Validation methods
    # --------------------------------------------------------------------------

    def clean(self):
        cleaned_data = super().clean()

        self.clean_speakers(cleaned_data)
        self.clean_scoresheet(cleaned_data)

        return cleaned_data

    def clean_speakers(self, cleaned_data):
        """Checks that the speaker selections are valid."""

        # Pull team info again, in case it's changed since the form was loaded.
        if self.choosing_sides:
            teams = cleaned_data.get('choose_sides', [None] * len(self.sides))
        else:
            teams = [self.debate.get_team(side) for side in self.sides]
        if None in teams:
            logger.warning("Team identities not found")

        if count := [cleaned_data.get(self._fieldname_forfeit(side), False) for side in self.sides].count(True):
            if count > 1:
                self.add_error(None, forms.ValidationError(_("Only one team can forfeit"), code='multi_forfeit'))
            return

        for side, team in zip(self.sides, teams):

            speaker_positions = dict()
            for pos in range(1, self.last_substantive_position + 1):
                speaker = cleaned_data.get(self._fieldname_speaker(side, pos))
                if speaker is None:
                    self.add_error(
                        self._fieldname_speaker(side, pos),
                        forms.ValidationError(_("This field is required."), code="required"),
                    )
                    continue

                # The speaker must be on the relevant team.
                if team is not None and speaker not in team.speakers:
                    self.add_error(self._fieldname_speaker(side, pos), forms.ValidationError(
                        _("The speaker %(speaker)s doesn't appear to be on team %(team)s."),
                        params={'speaker': speaker.get_public_name(self.tournament), 'team': team_name_for_data_entry(team, self.use_codes)},
                        code='speaker_wrongteam'),
                    )

                # Don't count this speaker if the speech is marked as a ghost
                if not cleaned_data.get(self._fieldname_ghost(side, pos)):
                    speaker_positions.setdefault(speaker, []).append(pos)

            # The substantive speakers must be unique.
            for speaker, positions in speaker_positions.items():
                if len(positions) > 1:
                    # Translators: count is always at least 2
                    message = ngettext(
                        "%(speaker)s appears to have given %(count)d substantive speech.",  # never used, needed for i18n
                        "%(speaker)s appears to have given %(count)d substantive speeches.",
                        len(positions),
                    )
                    params = {'speaker': speaker.get_public_name(self.tournament), 'count': len(positions)}
                    for pos in positions:
                        self.add_error(self._fieldname_speaker(side, pos), forms.ValidationError(
                            message, params=params, code='speaker_repeat'))

            # Check reply speaker only if not marked as a ghost
            if self.using_replies and not cleaned_data.get(self._fieldname_ghost(side, self.reply_position)):
                reply_speaker = cleaned_data.get(self._fieldname_speaker(side, self.reply_position))
                last_speaker = cleaned_data.get(self._fieldname_speaker(side, self.last_substantive_position))

                # The last speaker can't give the reply.
                if reply_speaker == last_speaker and reply_speaker is not None:
                    self.add_error(self._fieldname_speaker(side, self.reply_position), forms.ValidationError(
                        _("The last substantive speaker and reply speaker can't be the same."),
                        code='reply_speaker_consecutive',
                    ))

                # The reply speaker must have given a substantive speech.
                if self.tournament.pref('require_substantive_for_reply') and len(speaker_positions.get(reply_speaker, [])) == 0:
                    self.add_error(self._fieldname_speaker(side, self.reply_position), forms.ValidationError(
                        _("The reply speaker for this team did not give a substantive speech."),
                        code='reply_speaker_not_repeat',
                    ))

    def clean_scoresheet(self, cleaned_data):
        """Cleans the speaker score fields.
        Must be implemented by subclasses."""
        raise NotImplementedError

    @staticmethod
    def _decimal_or_zero(value):
        if value in (None, ""):
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @classmethod
    def _weighted_total(cls, entries):
        total = Decimal("0")
        for score, weight in entries:
            total += cls._decimal_or_zero(score) * cls._decimal_or_zero(weight)
        return total

    @staticmethod
    def _is_whole_number(value):
        decimal_value = ScoresMixin._decimal_or_zero(value)
        return decimal_value == decimal_value.to_integral_value()

    def _add_non_integer_total_error(self, field_name):
        self.add_error(field_name, forms.ValidationError(
            _("The total score for this block must be a whole number."),
            code='whole_number_total',
        ))

    def _default_criterion_initial(self, min_score, max_score, step):
        if not self.tournament.pref('slider_ballot_ui'):
            return None
        if self.ballotsub.id is not None:
            return None
        if self.filled and not self.allow_default_criteria_on_prefill:
            return None

        min_score = Decimal(str(min_score))
        max_score = Decimal(str(max_score))
        step = Decimal(str(step))
        midpoint = (min_score + max_score) / Decimal("2")
        if step <= 0:
            return midpoint

        steps = ((midpoint - min_score) / step).to_integral_value(rounding=ROUND_HALF_UP)
        initial = min_score + (steps * step)
        return min(max(initial, min_score), max_score)

    # --------------------------------------------------------------------------
    # Saving
    # --------------------------------------------------------------------------

    def save_participant_fields(self, result):
        self.ballotsub.forfeit = False
        forfeit_side = self._selected_forfeit_side()
        if forfeit_side is not None:
            self.ballotsub.forfeit = True
            result = ConsensusDebateResult(self.ballotsub, criteria=self.criteria)
            result.set_winners(set(self.sides) - {forfeit_side})

            self.result = result
            return

        for side, pos in product(self.sides, self.positions):
            speaker = self.cleaned_data[self._fieldname_speaker(side, pos)]
            result.set_speaker(side, pos, speaker)
            is_ghost = self.cleaned_data[self._fieldname_ghost(side, pos)]
            result.set_ghost(side, pos, is_ghost)

        self.populate_result_with_scores(result)

    def populate_result_with_scores(self, result):
        """Should populate `result` with speaker scores in-place, using the data
        in `self.cleaned_data`. Must be implemented by subclasses."""
        raise NotImplementedError

    # --------------------------------------------------------------------------
    # Template access methods
    # --------------------------------------------------------------------------

    def fake_speaker_selects(self):
        for team in self.debate.teams:
            yield self['team_%d' % team.id]

    def scoresheet(
        self,
        fieldname_score_func,
        fieldname_srank_func=None,
        fieldname_criterion_func=None,
        fieldname_cross_score_func=None,
        fieldname_cross_total_func=None,
    ):
        """Returns a list of dictionaries for a single scoresheet, to allow for
        easy iteration of the form. The function `fieldname_score_func` should
        take two arguments `(side, pos)`. This function is called by the
        `.scoresheets()` methods of both subclasses."""
        teams = []
        for side, (side_name, pos_names) in zip(self.sides, side_and_position_names(self.tournament, self.sides)):
            side_dict = {
                "side_code": side,
                "side_name": side_name,
                "team": self.debate.get_team(side),
                "speakers": [],
                "forfeit": (self[self._fieldname_forfeit(side)]
                        if self._has_forfeit_fields()
                        else None),
            }
            inserted_cross_group = False
            for pos, pos_name in zip(self.positions, pos_names):
                if (
                    self.using_cross_examinations and
                    fieldname_cross_total_func is not None and
                    not inserted_cross_group and
                    self.reply_position is not None and
                    pos == self.reply_position
                ):
                    side_dict["speakers"].append(
                        self._cross_group_for_side(
                            side,
                            fieldname_cross_score_func,
                            fieldname_cross_total_func,
                        ),
                    )
                    inserted_cross_group = True

                spk_dict = {
                    "pos": pos,
                    "name": pos_name,
                    "speaker": self[self._fieldname_speaker(side, pos)],
                    "ghost": self[self._fieldname_ghost(side, pos)],
                    "score": self[fieldname_score_func(side, pos)],
                    "criteria": [(criterion, self[fieldname_criterion_func(side, pos, criterion)]) for criterion in self.criteria_for_position(pos)] if fieldname_criterion_func else [],
                }
                if fieldname_srank_func:
                    spk_dict["srank"] = self[fieldname_srank_func(side, pos)]
                side_dict["speakers"].append(spk_dict)

            if self.using_cross_examinations and fieldname_cross_total_func is not None and not inserted_cross_group:
                side_dict["speakers"].append(
                    self._cross_group_for_side(
                        side,
                        fieldname_cross_score_func,
                        fieldname_cross_total_func,
                    ),
                )

            teams.append(side_dict)
        return teams


    def _cross_group_for_side(self, side, fieldname_cross_score_func, fieldname_cross_total_func):
        return {
            "is_cross_group": True,
            "name": _("Cross-examinations"),
            "crosses": [
                {
                    "name": cross.name,
                    "field": self[fieldname_cross_score_func(side, cross)],
                }
                for cross in self.crosses
            ] if fieldname_cross_score_func else [],
            "total": self[fieldname_cross_total_func(side)],
        }

class SingleBallotSetForm(ScoresMixin, BaseBallotSetForm):
    """Presents one ballot for the debate. Used for consensus adjudications."""


    result_class = ConsensusDebateResultWithScores

    @staticmethod
    def _fieldname_score(side, pos):
        return '%(side)d_score_s%(pos)d' % {'side': side, 'pos': pos}

    @staticmethod
    def _fieldname_srank(side, pos):
        return '%(side)d_srank_s%(pos)d' % {'side': side, 'pos': pos}

    @staticmethod
    def _fieldname_declared_winner():
        return 'declared_winner'

    @staticmethod
    def _fieldname_criterion_score(side, pos, criterion):
        return '%(side)s_criterion_s%(pos)d_c%(criterion)d' % {'side': side, 'pos': pos, 'criterion': criterion.id}

    @staticmethod
    def _fieldname_cross_score(side, cross):
        return '%(side)d_cross_x%(cross)d' % {'side': side, 'cross': cross.id}

    @staticmethod
    def _fieldname_cross_total(side):
        return '%(side)d_cross_total' % {'side': side}

    def create_score_fields(self):
        """Adds the speaker score fields:
         - <side>_score_s#,  one for each score
        """
        for side, pos in product(self.sides, self.positions):
            scorefield = ReplyScoreField if (pos == self.reply_position) else SubstantiveScoreField
            position_criteria = self.criteria_for_position(pos)
            if position_criteria:
                self.fields[self._fieldname_score(side, pos)] = forms.DecimalField(
                    required=False,
                    widget=forms.NumberInput(attrs={'class': 'number', 'readonly': True}),
                )
            else:
                self.fields[self._fieldname_score(side, pos)] = scorefield(
                    widget=forms.NumberInput(attrs={'class': 'number'}),
                    tournament=self.tournament,
                    required=False,
                )
            for criterion in position_criteria:
                criterion_initial = self._default_criterion_initial(
                    criterion.min_score, criterion.max_score, criterion.step)
                criterion_kwargs = {
                    'min_value': Decimal(str(criterion.min_score)),
                    'max_value': Decimal(str(criterion.max_score)),
                    'step_size': Decimal(str(criterion.step)),
                    'required': False,
                    'widget': forms.NumberInput(attrs={'class': 'number', 'weight': criterion.weight, 'data-required': str(criterion.required).lower()}),
                }
                if criterion_initial is not None:
                    criterion_kwargs['initial'] = criterion_initial
                self.fields[self._fieldname_criterion_score(side, pos, criterion)] = forms.DecimalField(**criterion_kwargs)
            if self.using_speaker_ranks:
                nspeeches = len(self.sides) * len(self.positions)
                self.fields[self._fieldname_srank(side, pos)] = forms.IntegerField(required=False, min_value=1, max_value=nspeeches, step_size=1)

        if self.using_cross_examinations:
            for side in self.sides:
                if self.crosses:
                    self.fields[self._fieldname_cross_total(side)] = forms.DecimalField(
                        required=False,
                        widget=forms.NumberInput(attrs={
                            'class': 'number total',
                            'readonly': True,
                        }),
                    )
                else:
                    self.fields[self._fieldname_cross_total(side)] = CrossTotalScoreField(
                        widget=forms.NumberInput(attrs={
                            'class': 'number total',
                        }),
                        tournament=self.tournament,
                        required=False,
                    )
                for cross in self.crosses:
                    criterion_initial = self._default_criterion_initial(
                        cross.min_score, cross.max_score, cross.step)
                    cross_kwargs = {
                        'min_value': Decimal(str(cross.min_score)),
                        'max_value': Decimal(str(cross.max_score)),
                        'step_size': Decimal(str(cross.step)),
                        'required': False,
                        'widget': forms.NumberInput(attrs={'class': 'number cross-criterion', 'weight': cross.weight, 'data-required': str(cross.required).lower()}),
                    }
                    if criterion_initial is not None:
                        cross_kwargs['initial'] = criterion_initial
                    self.fields[self._fieldname_cross_score(side, cross)] = forms.DecimalField(**cross_kwargs)

        if self.using_declared_winner:
            self.fields[self._fieldname_declared_winner()] = self.create_declared_winner_dropdown()

    def initial_from_result(self, result):
        initial = super().initial_from_result(result)

        if self.ballotsub.forfeit:
            return initial

        for side, pos in product(self.sides, self.positions):
            score = result.get_score(side, pos)
            if score is not None:
                initial[self._fieldname_score(side, pos)] = score
            if self.using_speaker_ranks:
                rank = result.get_speaker_rank(side, pos)
                if rank is not None:
                    initial[self._fieldname_srank(side, pos)] = rank
            for criterion in self.criteria_for_position(pos):
                criterion_score = result.get_criterion_score(side, pos, criterion)
                if criterion_score is not None:
                    initial[self._fieldname_criterion_score(side, pos, criterion)] = criterion_score

        if self.using_cross_examinations:
            for side in self.sides:
                cross_total = result.get_cross_total(side)
                if cross_total is not None:
                    initial[self._fieldname_cross_total(side)] = cross_total
                for cross in self.crosses:
                    cross_score = result.get_cross_score(side, cross)
                    if cross_score is not None:
                        initial[self._fieldname_cross_score(side, cross)] = cross_score

        if self.using_declared_winner:
            winning_side = result.winning_side()
            if winning_side is not None:
                initial[self._fieldname_declared_winner()] = winning_side

        return initial

    def list_score_fields(self):
        """Lists all the score fields. Called by super().set_tab_indices()."""
        order = []
        for side, pos in product(self.sides, self.positions):
            order.append(self._fieldname_srank(side, pos))
            order.append(self._fieldname_score(side, pos))

        if self.using_cross_examinations:
            for side in self.sides:
                for cross in self.crosses:
                    order.append(self._fieldname_cross_score(side, cross))
                order.append(self._fieldname_cross_total(side))

        if self.using_declared_winner:
            order.append(self._fieldname_declared_winner())
        return order

    # --------------------------------------------------------------------------
    # Validation and save methods
    # --------------------------------------------------------------------------

    def clean_scoresheet(self, cleaned_data):
        if any(cleaned_data.get(self._fieldname_forfeit(side), False) for side in self.sides):
            return

        should_skip = False
        for side, pos in product(self.sides, self.positions):
            score_fieldname = self._fieldname_score(side, pos)
            score = cleaned_data.get(score_fieldname)
            position_criteria = self.criteria_for_position(pos)

            if score is None and len(position_criteria) == 0:
                self.add_error(score_fieldname, forms.ValidationError(
                    _("This field is required."),
                    code='required',
                ))
                should_skip = True
            elif score is not None and len(position_criteria) == 0 and not self._is_whole_number(score):
                self._add_non_integer_total_error(score_fieldname)
                should_skip = True

            for criterion in position_criteria:
                criterion_score = cleaned_data.get(self._fieldname_criterion_score(side, pos, criterion))
                if criterion_score is None and criterion.required:
                    self.add_error(
                        self._fieldname_criterion_score(side, pos, criterion),
                        forms.ValidationError(_("This field is required."), code='required'),
                    )
                    should_skip = True

        if self.using_cross_examinations:
            for side in self.sides:
                cross_total_fieldname = self._fieldname_cross_total(side)
                if self.crosses:
                    for cross in self.crosses:
                        cross_score = cleaned_data.get(self._fieldname_cross_score(side, cross))
                        if cross_score is None and cross.required:
                            self.add_error(self._fieldname_cross_score(side, cross), forms.ValidationError(
                                _("This field is required."),
                                code='required',
                            ))
                            should_skip = True
                else:
                    cross_total = cleaned_data.get(cross_total_fieldname)
                    if cross_total is None:
                        self.add_error(cross_total_fieldname, forms.ValidationError(
                            _("This field is required."),
                            code='required',
                        ))
                        should_skip = True
                    elif not self._is_whole_number(cross_total):
                        self._add_non_integer_total_error(cross_total_fieldname)
                        should_skip = True

        if should_skip:
            return

        try:
            side_totals = {}
            for side in self.sides:
                team_total = Decimal("0")
                for pos in self.positions:
                    score_fieldname = self._fieldname_score(side, pos)
                    position_criteria = self.criteria_for_position(pos)
                    if position_criteria:
                        position_total = self._weighted_total(
                            (cleaned_data.get(self._fieldname_criterion_score(side, pos, criterion)), criterion.weight)
                            for criterion in position_criteria
                        )
                        cleaned_data[score_fieldname] = position_total
                        if not self._is_whole_number(position_total):
                            self._add_non_integer_total_error(score_fieldname)
                            should_skip = True
                        team_total += position_total
                    else:
                        team_total += self._decimal_or_zero(cleaned_data.get(score_fieldname))

                if self.using_cross_examinations:
                    cross_total_fieldname = self._fieldname_cross_total(side)
                    if self.crosses:
                        cross_total = self._weighted_total(
                            (cleaned_data.get(self._fieldname_cross_score(side, cross)), cross.weight)
                            for cross in self.crosses
                        )
                        cleaned_data[cross_total_fieldname] = cross_total
                        if not self._is_whole_number(cross_total):
                            self._add_non_integer_total_error(cross_total_fieldname)
                            should_skip = True
                        team_total += cross_total
                    else:
                        team_total += self._decimal_or_zero(cleaned_data.get(cross_total_fieldname))
                side_totals[side] = team_total
            totals = list(side_totals.values())

        except KeyError as e:
            logger.warning("Field %s not found", str(e))
            return

        if should_skip:
            return

        if len(totals) == 2:
            # Check that no teams had the same total
            if totals[0] == totals[1] and self.declared_winner in ['none', 'high-points']:
                self.add_error(None, forms.ValidationError(
                    _("The total scores for the teams are the same (i.e. a draw)."),
                    code='draw',
                ))
            elif self.declared_winner in ['high-points', 'tied-points']:
                max_teams = [side for side, total in side_totals.items() if total == max(totals)]

                if int(cleaned_data.get(self._fieldname_declared_winner())) not in max_teams:
                    self.add_error(None, forms.ValidationError(
                        _("The declared winner does not correspond to the team with the highest score."),
                        code='wrong_winner',
                    ))

        elif len(totals) > 2:
            for total in set(totals):
                sides = [s for s, t in zip(self.sides, totals) if t == total]
                if len(sides) > 1:
                    self.add_error(None, forms.ValidationError(
                        _("The total scores for the following teams are the same: %(teams)s"),
                        params={'teams': ", ".join(self._side_name(side) for side in sides)},
                        code='tied_score',
                    ))

        # Check that the margin did not exceed the maximum permissible.
        if len(totals) == 2 and self.max_margin:
            margin = abs(totals[0] - totals[1])
            if margin > self.max_margin:
                self.add_error(None, forms.ValidationError(
                    _("The margin (%(margin).1f) exceeds the maximum allowable margin (%(max_margin).1f)."),
                    params={'margin': float(margin), 'max_margin': self.max_margin}, code='max_margin',
                ))

        if self.using_speaker_ranks:
            ranks = set()
            rank_scores = []
            for side, pos in product(self.sides, self.positions):
                rank = cleaned_data[self._fieldname_srank(side, pos)]
                if rank is None:
                    self.add_error(self._fieldname_srank(side, pos), forms.ValidationError(_("This field is required."), code='required'))
                    continue
                ranks.add(rank)
                rank_scores.append((rank, self._decimal_or_zero(cleaned_data[self._fieldname_score(side, pos)])))

            if len(ranks) < len(self.sides) * len(self.positions):
                self.add_error(None, forms.ValidationError(_("Ranks cannot be tied."), code='ranks_tied'))

            if self.tournament.pref('speaker_ranks') == 'high-points' and (
                sorted(rank_scores, key=lambda s: (-s[1], s[0])) != sorted(rank_scores, key=lambda s: (s[0], -s[1]))
            ):
                self.add_error(None, forms.ValidationError(_("Ranks must correspond to speaker scores"), code='ranks_high'))

    def populate_result_with_scores(self, result):
        for side, pos in product(self.sides, self.positions):
            score = self.cleaned_data[self._fieldname_score(side, pos)]
            for criterion in self.criteria_for_position(pos):
                result.set_criterion_score(side, pos, criterion, self.cleaned_data[self._fieldname_criterion_score(side, pos, criterion)])
            if len(self.criteria_for_position(pos)) == 0:
                result.set_score(side, pos, score)

            if self.using_speaker_ranks:
                result.set_speaker_rank(side, pos, self.cleaned_data[self._fieldname_srank(side, pos)])

        if self.using_cross_examinations:
            for side in self.sides:
                if self.crosses:
                    for cross in self.crosses:
                        result.set_cross_score(side, cross, self.cleaned_data[self._fieldname_cross_score(side, cross)])
                else:
                    result.set_cross_total(side, self.cleaned_data[self._fieldname_cross_total(side)])

        if self.declared_winner not in ['none', 'high-points']:
            result.set_winners({int(self.cleaned_data[self._fieldname_declared_winner()])})

    # --------------------------------------------------------------------------
    # Template access methods
    # --------------------------------------------------------------------------

    def scoresheets(self):
        """Generates a sequence of nested dicts that allows for easy iteration
        through the form. Used in the ballot_set.html.html template."""
        sheets = [{
            "teams": self.scoresheet(
                self._fieldname_score,
                self._fieldname_srank if self.using_speaker_ranks else None,
                fieldname_criterion_func=lambda side, pos, criterion: self._fieldname_criterion_score(side, pos, criterion),
                fieldname_cross_score_func=lambda side, cross: self._fieldname_cross_score(side, cross),
                fieldname_cross_total_func=lambda side: self._fieldname_cross_total(side),
            ),
        }]

        if self.using_declared_winner:
            sheets[0]['declared_winner'] = self[self._fieldname_declared_winner()]
        return sheets


class PerAdjudicatorBallotSetForm(ScoresMixin, BaseBallotSetForm):
    """Presents one ballot per voting adjudicator. Used for voting
    adjudications."""

    result_class = DebateResultByAdjudicatorWithScores

    @staticmethod
    def _fieldname_score(adj, side, pos):
        return '%(side)d_score_a%(adj)d_s%(pos)d' % {'adj': adj.id, 'side': side, 'pos': pos}

    @staticmethod
    def _fieldname_declared_winner(adj):
        return 'declared_winner_a%(adj)d' % {'adj': adj.id}

    @staticmethod
    def _fieldname_criterion_score(adj, side, pos, criterion):
        return '%(side)s_criterion_a%(adj)d_s%(pos)d_c%(criterion)d' % {'adj': adj.id, 'side': side, 'pos': pos, 'criterion': criterion.id}

    @staticmethod
    def _fieldname_cross_score(adj, side, cross):
        return '%(side)d_cross_a%(adj)d_x%(cross)d' % {'adj': adj.id, 'side': side, 'cross': cross.id}

    @staticmethod
    def _fieldname_cross_total(adj, side):
        return '%(side)d_cross_a%(adj)d_total' % {'adj': adj.id, 'side': side}

    def create_score_fields(self):
        """Adds the speaker score fields:
         - <side>_score_a#_s#,  one for each score
        """
        for side, pos in product(self.sides, self.positions):
            scorefield = ReplyScoreField if (pos == self.reply_position) else SubstantiveScoreField
            position_criteria = self.criteria_for_position(pos)
            for adj in self.adjudicators:
                if position_criteria:
                    self.fields[self._fieldname_score(adj, side, pos)] = forms.DecimalField(
                        required=False,
                        widget=forms.NumberInput(attrs={'class': 'number', 'readonly': True}),
                    )
                else:
                    self.fields[self._fieldname_score(adj, side, pos)] = scorefield(
                        widget=forms.NumberInput(attrs={'class': 'number'}),
                        tournament=self.tournament,
                        required=False,
                    )
                for criterion in position_criteria:
                    criterion_initial = self._default_criterion_initial(
                        criterion.min_score, criterion.max_score, criterion.step)
                    criterion_kwargs = {
                        'min_value': Decimal(str(criterion.min_score)),
                        'max_value': Decimal(str(criterion.max_score)),
                        'step_size': Decimal(str(criterion.step)),
                        'required': False,
                        'widget': forms.NumberInput(attrs={'class': 'number', 'weight': criterion.weight, 'data-required': str(criterion.required).lower()}),
                    }
                    if criterion_initial is not None:
                        criterion_kwargs['initial'] = criterion_initial
                    self.fields[self._fieldname_criterion_score(adj, side, pos, criterion)] = forms.DecimalField(**criterion_kwargs)

        if self.using_cross_examinations:
            for adj in self.adjudicators:
                for side in self.sides:
                    if self.crosses:
                        self.fields[self._fieldname_cross_total(adj, side)] = forms.DecimalField(
                            required=False,
                            widget=forms.NumberInput(attrs={
                                'class': 'number total',
                                'readonly': True,
                            }),
                        )
                    else:
                        self.fields[self._fieldname_cross_total(adj, side)] = CrossTotalScoreField(
                            widget=forms.NumberInput(attrs={
                                'class': 'number total',
                            }),
                            tournament=self.tournament,
                            required=False,
                        )
                    for cross in self.crosses:
                        criterion_initial = self._default_criterion_initial(
                            cross.min_score, cross.max_score, cross.step)
                        cross_kwargs = {
                            'min_value': Decimal(str(cross.min_score)),
                            'max_value': Decimal(str(cross.max_score)),
                            'step_size': Decimal(str(cross.step)),
                            'required': False,
                            'widget': forms.NumberInput(attrs={'class': 'number cross-criterion', 'weight': cross.weight, 'data-required': str(cross.required).lower()}),
                        }
                        if criterion_initial is not None:
                            cross_kwargs['initial'] = criterion_initial
                        self.fields[self._fieldname_cross_score(adj, side, cross)] = forms.DecimalField(**cross_kwargs)

        if self.using_declared_winner:
            for adj in self.adjudicators:
                self.fields[self._fieldname_declared_winner(adj)] = self.create_declared_winner_dropdown()

    def initial_from_result(self, result):
        initial = super().initial_from_result(result)

        if self.ballotsub.forfeit:
            return initial

        for adj in self.adjudicators:
            for side, pos in product(self.sides, self.positions):
                score = result.get_score(adj, side, pos)
                if score is not None:
                    initial[self._fieldname_score(adj, side, pos)] = score
                for criterion in self.criteria_for_position(pos):
                    criterion_score = result.get_criterion_score(adj, side, pos, criterion)
                    if criterion_score is not None:
                        initial[self._fieldname_criterion_score(adj, side, pos, criterion)] = criterion_score

            if self.using_cross_examinations:
                for side in self.sides:
                    cross_total = result.get_cross_total(adj, side)
                    if cross_total is not None:
                        initial[self._fieldname_cross_total(adj, side)] = cross_total
                    for cross in self.crosses:
                        cross_score = result.get_cross_score(adj, side, cross)
                        if cross_score is not None:
                            initial[self._fieldname_cross_score(adj, side, cross)] = cross_score

            if self.using_declared_winner:
                winner = result.get_winner(adj)
                if winner is not None:
                    initial[self._fieldname_declared_winner(adj)] = winner

        return initial

    def list_score_fields(self):
        """Lists all the score fields. Called by super().set_tab_indices()."""
        order = []
        for adj in self.adjudicators:
            for side, pos in product(self.sides, self.positions):
                order.append(self._fieldname_score(adj, side, pos))

            if self.using_cross_examinations:
                for side in self.sides:
                    for cross in self.crosses:
                        order.append(self._fieldname_cross_score(adj, side, cross))
                    order.append(self._fieldname_cross_total(adj, side))

            if self.using_declared_winner:
                order.append(self._fieldname_declared_winner(adj))
        return order

    # --------------------------------------------------------------------------
    # Validation and save methods
    # --------------------------------------------------------------------------

    def clean_scoresheet(self, cleaned_data):
        if any(cleaned_data.get(self._fieldname_forfeit(side), False) for side in self.sides):
            return

        for adj in self.adjudicators:
            should_skip = False
            for side, pos in product(self.sides, self.positions):
                score_fieldname = self._fieldname_score(adj, side, pos)
                score = cleaned_data.get(score_fieldname)
                position_criteria = self.criteria_for_position(pos)

                if score is None and len(position_criteria) == 0:
                    self.add_error(score_fieldname, forms.ValidationError(
                        _("This field is required."),
                        code='required',
                    ))
                    should_skip = True
                elif score is not None and len(position_criteria) == 0 and not self._is_whole_number(score):
                    self._add_non_integer_total_error(score_fieldname)
                    should_skip = True

                for criterion in position_criteria:
                    criterion_score = cleaned_data.get(self._fieldname_criterion_score(adj, side, pos, criterion))
                    if criterion_score is None and criterion.required:
                        self.add_error(
                            self._fieldname_criterion_score(adj, side, pos, criterion),
                            forms.ValidationError(_("This field is required."), code='required'),
                        )
                        should_skip = True

            if self.using_cross_examinations:
                for side in self.sides:
                    cross_total_fieldname = self._fieldname_cross_total(adj, side)
                    if self.crosses:
                        for cross in self.crosses:
                            cross_score = cleaned_data.get(self._fieldname_cross_score(adj, side, cross))
                            if cross_score is None and cross.required:
                                self.add_error(self._fieldname_cross_score(adj, side, cross), forms.ValidationError(
                                    _("This field is required."),
                                    code='required',
                                ))
                                should_skip = True
                    else:
                        cross_total = cleaned_data.get(cross_total_fieldname)
                        if cross_total is None:
                            self.add_error(cross_total_fieldname, forms.ValidationError(
                                _("This field is required."),
                                code='required',
                            ))
                            should_skip = True
                        elif not self._is_whole_number(cross_total):
                            self._add_non_integer_total_error(cross_total_fieldname)
                            should_skip = True

            if should_skip:
                continue

            try:
                side_totals = {}
                for side in self.sides:
                    team_total = Decimal("0")
                    for pos in self.positions:
                        score_fieldname = self._fieldname_score(adj, side, pos)
                        position_criteria = self.criteria_for_position(pos)
                        if position_criteria:
                            position_total = self._weighted_total(
                                (cleaned_data.get(self._fieldname_criterion_score(adj, side, pos, criterion)), criterion.weight)
                                for criterion in position_criteria
                            )
                            cleaned_data[score_fieldname] = position_total
                            if not self._is_whole_number(position_total):
                                self._add_non_integer_total_error(score_fieldname)
                                should_skip = True
                            team_total += position_total
                        else:
                            team_total += self._decimal_or_zero(cleaned_data.get(score_fieldname))
                    if self.using_cross_examinations:
                        cross_total_fieldname = self._fieldname_cross_total(adj, side)
                        if self.crosses:
                            cross_total = self._weighted_total(
                                (cleaned_data.get(self._fieldname_cross_score(adj, side, cross)), cross.weight)
                                for cross in self.crosses
                            )
                            cleaned_data[cross_total_fieldname] = cross_total
                            if not self._is_whole_number(cross_total):
                                self._add_non_integer_total_error(cross_total_fieldname)
                                should_skip = True
                            team_total += cross_total
                        else:
                            team_total += self._decimal_or_zero(cleaned_data.get(cross_total_fieldname))
                    side_totals[side] = team_total
                totals = list(side_totals.values())

            except KeyError as e:
                logger.warning("Field %s not found", str(e))
                continue

            if should_skip:
                continue

            if len(totals) == 2:
                # Check that it was not a draw.
                if totals[0] == totals[1] and self.declared_winner in ['none', 'high-points']:
                    self.add_error(None, forms.ValidationError(
                        _("The total scores for the teams are the same (i.e. a draw) for adjudicator %(adjudicator)s."),
                        params={'adjudicator': adj.get_public_name(self.tournament)}, code='draw',
                    ))
                elif self.declared_winner in ['high-points', 'tied-points']:
                    max_teams = [side for side, total in side_totals.items() if total == max(totals)]

                    if int(cleaned_data.get(self._fieldname_declared_winner(adj))) not in max_teams:
                        self.add_error(None, forms.ValidationError(
                            _("The declared winner does not correspond to the team with the highest score for adjudicator %(adjudicator)s."),
                            params={'adjudicator': adj.get_public_name(self.tournament)}, code='wrong_winner',
                        ))

            # Check that the margin did not exceed the maximum permissible.
            if len(totals) == 2 and self.max_margin:
                margin = abs(totals[0] - totals[1])
                self.add_error(None, forms.ValidationError(
                    _("The margin (%(margin).1f) in the ballot of adjudicator %(adjudicator)s exceeds the maximum allowable margin (%(max_margin).1f)."),
                    params={'adjudicator': adj.get_public_name(self.tournament), 'margin': float(margin), 'max_margin': self.max_margin}, code='max_margin',
                ))

    def populate_result_with_scores(self, result):
        for adj in self.adjudicators:
            for side, pos in product(self.sides, self.positions):
                score = self.cleaned_data[self._fieldname_score(adj, side, pos)]
                for criterion in self.criteria_for_position(pos):
                    result.set_criterion_score(adj, side, pos, criterion, self.cleaned_data[self._fieldname_criterion_score(adj, side, pos, criterion)] or 0)
                if len(self.criteria_for_position(pos)) == 0:
                    result.set_score(adj, side, pos, score)

            if self.using_cross_examinations:
                for side in self.sides:
                    if self.crosses:
                        for cross in self.crosses:
                            result.set_cross_score(adj, side, cross, self.cleaned_data[self._fieldname_cross_score(adj, side, cross)])
                    else:
                        result.set_cross_total(adj, side, self.cleaned_data[self._fieldname_cross_total(adj, side)])

            if self.declared_winner not in ['none', 'high-points']:
                result.set_winners(adj, {int(self.cleaned_data.get(self._fieldname_declared_winner(adj)))})

    # --------------------------------------------------------------------------
    # Template access methods
    # --------------------------------------------------------------------------

    def scoresheets(self):
        """Generates a sequence of nested dicts that allows for easy iteration
        through the form. Used in the ballot_set.html template."""
        for adj in self.adjudicators:
            sheet_dict = {
                "adjudicator": adj,
                "teams": self.scoresheet(
                    lambda side, pos: self._fieldname_score(adj, side, pos),
                    fieldname_criterion_func=lambda side, pos, criterion: self._fieldname_criterion_score(adj, side, pos, criterion),
                    fieldname_cross_score_func=lambda side, cross: self._fieldname_cross_score(adj, side, cross),
                    fieldname_cross_total_func=lambda side: self._fieldname_cross_total(adj, side),
                ),
            }
            if self.using_declared_winner:
                sheet_dict['declared_winner'] = self[self._fieldname_declared_winner(adj)]
            yield sheet_dict


class TeamsMixin:
    """Provides a multiple-select (checkbox) of the teams for scoreless ballots."""

    has_scores = False

    def create_participant_fields(self):
        self.create_score_fields()

    def create_team_selector(self):
        # 3(a). List of teams in multiple-select
        side_choices = [(side, _("%(team)s (%(side)s)") % {
            'team': team_name_for_data_entry(self.debate.get_team(side), self.use_codes),
            'side': self._side_name(side)}) for side in self.sides]
        return forms.MultipleChoiceField(choices=side_choices,
                widget=forms.CheckboxSelectMultiple)

    def initial_from_result(self, result):
        return {}

    def clean(self):
        cleaned_data = super().clean()

        if 'motion' not in cleaned_data:
            if self.motions.count() == 1:
                cleaned_data['motion'] = self.motions.get().motion
            else: # Motions not enabled
                cleaned_data['motion'] = None

        if not self.debate.sides_confirmed:
            self.add_error(None, forms.ValidationError(
                _("Sides for this debate are not confirmed. You can't save a result "
                  "for this debate until the sides have been confirmed in the draw."),
                code='sides_unconfirmed',
            ))

        return cleaned_data

    def save_participant_fields(self, result):
        self.populate_result_with_wins(result)

    def list_participant_fields(self):
        return []


class SingleEliminationBallotSetForm(TeamsMixin, BaseBallotSetForm):

    result_class = ConsensusDebateResult

    @staticmethod
    def _fieldname_advancing():
        return 'advancing'

    def create_score_fields(self):
        """Adds the speaker score fields:
         - <side>_score_s#,  one for each score
        """
        self.fields[self._fieldname_advancing()] = self.create_team_selector()

    def list_score_fields(self):
        return [self._fieldname_advancing()]

    def initial_from_result(self, result):
        initial = super().initial_from_result(result)
        initial[self._fieldname_advancing()] = list(result.get_winner())
        return initial

    def clean(self):
        cleaned_data = super().clean()

        num_advancing = len(self.sides) // 2 if not self.debate.round.is_last else 1
        if self._fieldname_advancing() in cleaned_data and len(cleaned_data[self._fieldname_advancing()]) != num_advancing:
            self.add_error(self._fieldname_advancing(), forms.ValidationError(
                ngettext(
                    "There must be exactly %(n)d team advancing.",
                    "There must be exactly %(n)d teams advancing.",
                    num_advancing,
                ) % {'n': num_advancing},
                code='num_advancing',
            ))

        return cleaned_data

    def populate_result_with_wins(self, result):
        result.set_winners(set(int(adv) for adv in self.cleaned_data[self._fieldname_advancing()]))

    def scoresheets(self):
        return [{'advancing': self[self._fieldname_advancing()]}]


class PerAdjudicatorEliminationBallotSetForm(TeamsMixin, BaseBallotSetForm):

    result_class = DebateResultByAdjudicator

    @staticmethod
    def _fieldname_advancing(adj):
        return 'advancing_a%(adj)d' % {'adj': adj.id}

    def create_score_fields(self):
        for adj in self.adjudicators:
            self.fields[self._fieldname_advancing(adj)] = self.create_team_selector()

    def list_score_fields(self):
        return [self._fieldname_advancing(adj) for adj in self.adjudicators]

    def initial_from_result(self, result):
        initial = super().initial_from_result(result)
        for adj in self.adjudicators:
            initial[self._fieldname_advancing(adj)] = [result.get_winner(adj)]
        return initial

    def clean(self):
        cleaned_data = super().clean()

        for adj in self.adjudicators:
            if self._fieldname_advancing(adj) in cleaned_data and len(cleaned_data[self._fieldname_advancing(adj)]) != 1:
                self.add_error(self._fieldname_advancing(adj), forms.ValidationError(
                    _("There must be exactly 1 team advancing."),
                    code='num_advancing',
                ))

    def populate_result_with_wins(self, result):
        for adj in self.adjudicators:
            result.set_winners(adj, set(int(adv) for adv in self.cleaned_data[self._fieldname_advancing(adj)]))

    def scoresheets(self):
        for adj in self.adjudicators:
            yield {'adjudicator': adj, 'advancing': self[self._fieldname_advancing(adj)]}

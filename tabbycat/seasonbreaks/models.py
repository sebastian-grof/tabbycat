from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from utils.models import UniqueConstraint


class BreaksPermission(models.TextChoices):
    VIEW = 'view.breaks', _("view global breaks")
    EDIT = 'edit.breaks', _("edit global breaks")
    MANAGE_ACCESS = 'manage.breaks_access', _("manage global breaks access")


class GlobalBreaksPermission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, verbose_name=_("user"))
    permission = models.CharField(max_length=50, choices=BreaksPermission.choices, verbose_name=_("permission"))

    class Meta:
        constraints = [UniqueConstraint(fields=['user', 'permission'])]
        verbose_name = _("global breaks permission")
        verbose_name_plural = _("global breaks permissions")

    def __str__(self):
        return "%s: %s" % (self.user, self.permission)


class BreakSeason(models.Model):
    class League(models.TextChoices):
        SDL = 'SDL', _("Slovak Debate League")
        JDL = 'JDL', _("Junior Debate League")

    name = models.CharField(max_length=100, verbose_name=_("name"))
    slug = models.SlugField(unique=True, verbose_name=_("slug"))
    league = models.CharField(max_length=3, choices=League.choices, verbose_name=_("league"))
    regional_slots = models.PositiveSmallIntegerField(default=0, verbose_name=_("regional final slots"))
    invited_teams = models.PositiveSmallIntegerField(default=0, verbose_name=_("invited teams"))
    active = models.BooleanField(default=True, verbose_name=_("active"))
    public = models.BooleanField(default=False, verbose_name=_("show on public Breaks page"))
    public_published_at = models.DateTimeField(blank=True, null=True, verbose_name=_("public snapshot published at"))
    public_snapshot = models.JSONField(blank=True, null=True, verbose_name=_("public snapshot"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))

    class Meta:
        ordering = ['-active', '-created_at', 'name']
        verbose_name = _("break season")
        verbose_name_plural = _("break seasons")

    def __str__(self):
        return self.name

    @property
    def effective_regional_slots(self):
        return self.regional_slots + (1 if self.invited_teams % 2 else 0)


class BreakRegion(models.Model):
    season = models.ForeignKey(BreakSeason, models.CASCADE, related_name='regions', verbose_name=_("season"))
    name = models.CharField(max_length=100, verbose_name=_("name"))
    seq = models.PositiveSmallIntegerField(default=0, verbose_name=_("sequence"))
    source_region = models.ForeignKey('participants.Region', models.SET_NULL, blank=True, null=True,
        verbose_name=_("source region"))

    class Meta:
        constraints = [UniqueConstraint(fields=['season', 'name'])]
        ordering = ['season', 'seq', 'name']
        verbose_name = _("break region")
        verbose_name_plural = _("break regions")

    def __str__(self):
        return "%s: %s" % (self.season, self.name)


class BreakTournament(models.Model):
    season = models.ForeignKey(BreakSeason, models.CASCADE, related_name='break_tournaments', verbose_name=_("season"))
    tournament = models.ForeignKey('tournaments.Tournament', models.CASCADE, related_name='break_tournaments',
        verbose_name=_("tournament"))
    region = models.ForeignKey(BreakRegion, models.PROTECT, related_name='break_tournaments', verbose_name=_("region"))
    seq = models.PositiveSmallIntegerField(default=0, verbose_name=_("sequence"))
    counts_for_break = models.BooleanField(default=True, verbose_name=_("counts for team and speaker break"),
        help_text=_("If unchecked, this tournament only counts toward adjudicator statistics."))
    frozen_at = models.DateTimeField(blank=True, null=True, verbose_name=_("frozen at"))

    class Meta:
        constraints = [
            UniqueConstraint(fields=['season', 'tournament']),
        ]
        ordering = ['season', 'seq', 'tournament__seq', 'tournament__name']
        verbose_name = _("break tournament")
        verbose_name_plural = _("break tournaments")

    def __str__(self):
        return "%s / %s" % (self.season, self.tournament)

    def mark_frozen(self):
        self.frozen_at = timezone.now()
        self.save(update_fields=['frozen_at'])


class BreakTeam(models.Model):
    season = models.ForeignKey(BreakSeason, models.CASCADE, related_name='teams', verbose_name=_("season"))
    name = models.CharField(max_length=150, verbose_name=_("name"))
    institution = models.ForeignKey('participants.Institution', models.SET_NULL, blank=True, null=True,
        verbose_name=_("institution"))
    region = models.ForeignKey(BreakRegion, models.SET_NULL, blank=True, null=True, related_name='teams',
        verbose_name=_("home region"))

    class Meta:
        constraints = [UniqueConstraint(fields=['season', 'name'])]
        ordering = ['season', 'name']
        verbose_name = _("season break team")
        verbose_name_plural = _("season break teams")

    def __str__(self):
        return self.name


class BreakTeamLink(models.Model):
    season = models.ForeignKey(BreakSeason, models.CASCADE, related_name='team_links', verbose_name=_("season"))
    break_team = models.ForeignKey(BreakTeam, models.CASCADE, related_name='links', verbose_name=_("season team"))
    team = models.ForeignKey('participants.Team', models.CASCADE, related_name='break_links', verbose_name=_("team"))

    class Meta:
        constraints = [UniqueConstraint(fields=['season', 'team'])]
        verbose_name = _("break team link")
        verbose_name_plural = _("break team links")

    def __str__(self):
        return "%s -> %s" % (self.team, self.break_team)


class BreakSpeaker(models.Model):
    season = models.ForeignKey(BreakSeason, models.CASCADE, related_name='speakers', verbose_name=_("season"))
    name = models.CharField(max_length=100, verbose_name=_("name"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("email"))

    class Meta:
        ordering = ['season', 'name']
        verbose_name = _("season break speaker")
        verbose_name_plural = _("season break speakers")

    def __str__(self):
        return self.name


class BreakSpeakerLink(models.Model):
    season = models.ForeignKey(BreakSeason, models.CASCADE, related_name='speaker_links', verbose_name=_("season"))
    break_speaker = models.ForeignKey(BreakSpeaker, models.CASCADE, related_name='links', verbose_name=_("season speaker"))
    speaker = models.ForeignKey('participants.Speaker', models.CASCADE, related_name='break_links',
        verbose_name=_("speaker"))

    class Meta:
        constraints = [UniqueConstraint(fields=['season', 'speaker'])]
        verbose_name = _("break speaker link")
        verbose_name_plural = _("break speaker links")

    def __str__(self):
        return "%s -> %s" % (self.speaker, self.break_speaker)


class BreakTeamTournamentResult(models.Model):
    break_tournament = models.ForeignKey(BreakTournament, models.CASCADE, related_name='team_results',
        verbose_name=_("break tournament"))
    break_team = models.ForeignKey(BreakTeam, models.CASCADE, related_name='tournament_results',
        verbose_name=_("season team"))
    wins = models.FloatField(default=0, verbose_name=_("wins"))
    ballots = models.FloatField(default=0, verbose_name=_("ballots"))
    speaker_score = models.FloatField(default=0, verbose_name=_("speaker score"))
    rounds_debated = models.PositiveSmallIntegerField(default=0, verbose_name=_("rounds debated"))
    majority_debated = models.BooleanField(default=False, verbose_name=_("debated majority of rounds"))

    class Meta:
        constraints = [UniqueConstraint(fields=['break_tournament', 'break_team'])]
        ordering = ['break_tournament', '-wins', '-ballots', '-speaker_score']
        verbose_name = _("break team tournament result")
        verbose_name_plural = _("break team tournament results")

    def __str__(self):
        return "%s in %s" % (self.break_team, self.break_tournament)


class BreakSpeakerTournamentParticipation(models.Model):
    break_tournament = models.ForeignKey(BreakTournament, models.CASCADE, related_name='speaker_participations',
        verbose_name=_("break tournament"))
    break_speaker = models.ForeignKey(BreakSpeaker, models.CASCADE, related_name='tournament_participations',
        verbose_name=_("season speaker"))
    break_team = models.ForeignKey(BreakTeam, models.CASCADE, related_name='speaker_participations',
        verbose_name=_("season team"))
    speeches = models.PositiveSmallIntegerField(default=0, verbose_name=_("speeches"))
    rounds = models.PositiveSmallIntegerField(default=0, verbose_name=_("rounds"))

    class Meta:
        constraints = [UniqueConstraint(fields=['break_tournament', 'break_speaker', 'break_team'])]
        ordering = ['break_tournament', 'break_team', 'break_speaker']
        verbose_name = _("break speaker tournament participation")
        verbose_name_plural = _("break speaker tournament participations")

    def __str__(self):
        return "%s for %s in %s" % (self.break_speaker, self.break_team, self.break_tournament)


class BreakAdjudicator(models.Model):
    season = models.ForeignKey(BreakSeason, models.CASCADE, related_name='adjudicators', verbose_name=_("season"))
    name = models.CharField(max_length=100, verbose_name=_("name"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("email"))
    institution = models.ForeignKey('participants.Institution', models.SET_NULL, blank=True, null=True,
        verbose_name=_("institution"))

    class Meta:
        ordering = ['season', 'name']
        verbose_name = _("season break adjudicator")
        verbose_name_plural = _("season break adjudicators")

    def __str__(self):
        return self.name


class BreakAdjudicatorLink(models.Model):
    season = models.ForeignKey(BreakSeason, models.CASCADE, related_name='adjudicator_links',
        verbose_name=_("season"))
    break_adjudicator = models.ForeignKey(BreakAdjudicator, models.CASCADE, related_name='links',
        verbose_name=_("season adjudicator"))
    adjudicator = models.ForeignKey('participants.Adjudicator', models.CASCADE, related_name='break_links',
        verbose_name=_("adjudicator"))

    class Meta:
        constraints = [UniqueConstraint(fields=['season', 'adjudicator'])]
        verbose_name = _("break adjudicator link")
        verbose_name_plural = _("break adjudicator links")

    def __str__(self):
        return "%s -> %s" % (self.adjudicator, self.break_adjudicator)


class BreakAdjudicatorTournamentStats(models.Model):
    break_tournament = models.ForeignKey(BreakTournament, models.CASCADE, related_name='adjudicator_stats',
        verbose_name=_("break tournament"))
    break_adjudicator = models.ForeignKey(BreakAdjudicator, models.CASCADE, related_name='tournament_stats',
        verbose_name=_("season adjudicator"))
    chair_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("chairs"))
    panellist_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("panellists"))
    trainee_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("trainees"))
    total_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("total"))

    class Meta:
        constraints = [UniqueConstraint(fields=['break_tournament', 'break_adjudicator'])]
        ordering = ['break_tournament', 'break_adjudicator']
        verbose_name = _("break adjudicator tournament stats")
        verbose_name_plural = _("break adjudicator tournament stats")

    def __str__(self):
        return "%s in %s" % (self.break_adjudicator, self.break_tournament)

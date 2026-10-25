from unittest.mock import patch

from django.test import TestCase

from draw.models import DebateTeam
from options.models import TournamentPreferenceModel

from .test_forms import BallotSetFormTestMixin


class TournamentDeletionSignalTests(BallotSetFormTestMixin, TestCase):
    def assert_cascade_does_not_refresh(self, queryset):
        self.ballotsub.save()
        # DebateTeam protects teams; remove those links as tournament deletion
        # workflows do, leaving the ballot to be deleted by the cascade.
        DebateTeam.objects.filter(debate=self.debate).delete()
        tournament_id = self.tournament.pk
        with patch('results.signals._refresh_auto_ballots') as refresh, patch('results.signals.refresh_bye_ballots') as byes:
            target = type(self.tournament).objects.filter(pk=tournament_id) if queryset else self.tournament
            target.delete()
        refresh.assert_not_called()
        byes.assert_not_called()
        self.assertFalse(TournamentPreferenceModel.objects.filter(instance_id=tournament_id).exists())

    def test_model_cascade_does_not_recreate_preferences(self):
        self.assert_cascade_does_not_refresh(queryset=False)

    def test_queryset_cascade_does_not_recreate_preferences(self):
        self.assert_cascade_does_not_refresh(queryset=True)

    def test_deleting_a_single_ballot_still_refreshes_other_automatic_results(self):
        self.ballotsub.save()
        with patch('results.signals._refresh_auto_ballots') as refresh:
            self.ballotsub.delete()
        refresh.assert_called_once_with(self.tournament, trigger_debate_is_bye=False)

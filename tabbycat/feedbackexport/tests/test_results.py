"""Results snapshot export (POST /api/v1/results/, contract v1).

The fixture is a small two-team tournament: four teams of three speakers, two
preliminary rounds and a final, one speaker category, one anonymous speaker, a
reply speech, a ghost (iron-person) speech, score criteria, cross-examinations
and one unconfirmed ballot that must never be exported.

Set RESULTS_EXAMPLE_PATH to regenerate the example payload in the docs, e.g.

    RESULTS_EXAMPLE_PATH=../docs/features/dr-results-payload-example.json \\
        python manage.py test -t . feedbackexport.tests.test_results
"""
import gzip
import io
import json
import os
import urllib.error
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils import timezone

from adjallocation.models import DebateAdjudicator
from breakqual.models import BreakCategory, BreakingTeam
from draw.models import Debate, DebateTeam
from feedbackexport.jobs import configuration, control_job, create_job, worker_tick
from feedbackexport.models import ExportJob, ResultsExportEvent
from feedbackexport.services import (
    build_results_payload, encode_request_body, queue_results_export, results_content_hash,
    RESULTS_GZIP_THRESHOLD, send_results_event,
)
from motions.models import Motion, RoundMotion
from participants.models import Adjudicator, Institution, Region, Speaker, SpeakerCategory, Team
from results.models import (
    BallotSubmission, CrossExamination, CrossExaminationScore, ScoreCriterion, SpeakerCriterionScore,
    SpeakerScore, TeamScore,
)
from seasonbreaks.models import BreakLeague, BreakRegion, BreakSeason, BreakTeam, BreakTeamLink, BreakTournament
from tournaments.models import Round, Tournament

from .test_feedbackexport import FakeHTTPResponse

RESULTS_SETTINGS = {
    'RESULTS_EXPORT_ENABLED': True, 'RESULTS_EXPORT_ENDPOINT': 'https://dr.example.test/api/v1/results/',
    'RESULTS_EXPORT_TOKEN': 'results-secret',
    'FEEDBACK_EXPORT_ENABLED': True, 'FEEDBACK_EXPORT_ENDPOINT': 'https://dr.example.test/feedback',
    'ADJUDICATOR_STATS_EXPORT_ENABLED': True, 'ADJUDICATOR_STATS_EXPORT_ENDPOINT': 'https://dr.example.test/activity',
}
EXAMPLE_PATH = Path(__file__).resolve().parents[3] / 'docs' / 'features' / 'dr-results-payload-example.json'
PRIVATE_KEYS = {'phone', 'gender', 'pronoun', 'pronouns', 'url_key', 'url', 'urls', 'private_url', 'ip', 'ip_address'}


def walk_keys(value, path=''):
    """Every key path in a JSON value, with list items collapsed to []."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield path + '.' + key, key
            yield from walk_keys(item, path + '.' + key)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item, path + '[]')


class ResultsFixtureMixin:
    """A finished two-team tournament with every result feature the contract covers."""

    def setUp(self):
        t = self.tournament = Tournament.objects.create(name='Results Open', short_name='RO', slug='results-open')
        t.preferences['debate_rules__teams_in_debate'] = 2
        t.preferences['debate_rules__substantive_speakers'] = 3
        t.preferences['debate_rules__reply_scores_enabled'] = True
        t.preferences['debate_rules__cross_examinations_enabled'] = True
        t.preferences['standings__team_standings_precedence'] = ['wins', 'speaks_sum']
        t.preferences['standings__team_standings_extra_metrics'] = ['margin_sum']
        t.preferences['standings__speaker_standings_precedence'] = ['total']
        t.preferences['standings__speaker_standings_extra_metrics'] = ['average', 'count']

        region = Region.objects.create(name='Západ')
        self.inst_a = Institution.objects.create(name='Gymnázium Alfa', code='Alfa', region=region)
        self.inst_b = Institution.objects.create(name='Gymnázium Beta', code='Beta')
        Institution.objects.create(name='Unrelated school', code='Nope')  # must not be exported

        self.open = BreakCategory.objects.create(tournament=t, name='Open', slug='open', seq=1, break_size=2,
                                                 is_general=True, priority=1)
        self.novice = SpeakerCategory.objects.create(tournament=t, name='Novice', slug='novice', seq=1)

        self.teams = {}
        self.speakers = {}
        for letter, institution in zip('ABCD', [self.inst_a, self.inst_a, self.inst_b, self.inst_b]):
            team = Team.objects.create(tournament=t, institution=institution, reference=letter,
                                       short_reference=letter, use_institution_prefix=True,
                                       code_name='Code %s' % letter)
            team.break_categories.add(self.open)
            self.teams[letter] = team
            for number in (1, 2, 3):
                self.speakers[letter + str(number)] = Speaker.objects.create(
                    team=team, name='Speaker %s%d' % (letter, number),
                    email='%s%d@example.test' % (letter.lower(), number) if number == 1 else None,
                    phone='+421900000000', gender='F', pronoun='she', url_key='key%s%d' % (letter.lower(), number),
                )
        self.speakers['A2'].anonymous = True
        self.speakers['A2'].save()
        self.speakers['B3'].categories.add(self.novice)
        self.speakers['C1'].categories.add(self.novice)

        self.chair = Adjudicator.objects.create(tournament=t, name='Chair Judge', email='chair@example.test',
                                                institution=self.inst_b, independent=True, phone='+421911111111',
                                                url_key='chairkey', gender='M')
        self.panellist = Adjudicator.objects.create(tournament=t, name='Panel Judge', institution=self.inst_a)
        self.trainee = Adjudicator.objects.create(tournament=t, name='Trainee Judge', trainee=True)
        self.shared = Adjudicator.objects.create(tournament=None, name='Shared Judge', adj_core=True)

        self.criterion = ScoreCriterion.objects.create(tournament=t, name='Obsah', seq=1, weight=1,
                                                       min_score=0, max_score=40, step=1)
        self.cx = CrossExamination.objects.create(tournament=t, seq=1, name='Krížové otázky')

        starts = datetime(2026, 11, 21, 8, 0, tzinfo=dt_timezone.utc)
        self.r1 = Round.objects.create(tournament=t, seq=1, name='Kolo 1', abbreviation='K1',
                                       draw_type=Round.DrawType.RANDOM, starts_at=starts)
        self.r2 = Round.objects.create(tournament=t, seq=2, name='Kolo 2', abbreviation='K2',
                                       draw_type=Round.DrawType.POWERPAIRED, silent=True)
        self.final = Round.objects.create(tournament=t, seq=3, name='Finále', abbreviation='F',
                                          stage=Round.Stage.ELIMINATION, draw_type=Round.DrawType.ELIMINATION,
                                          break_category=self.open, starts_at=starts.replace(day=22))
        self.motions = {}
        for round_ in (self.r1, self.r2, self.final):
            motion = Motion.objects.create(tournament=t, reference='Motion %s' % round_.abbreviation,
                                           text='This House would %s' % round_.name, info_slide='Info %s' % round_.seq)
            RoundMotion.objects.create(round=round_, motion=motion, seq=1)
            self.motions[round_.seq] = motion

        # Round 1: A beats B (2-1 panel, with replies); C beats D (D1 gives a ghost speech).
        self.d1 = self.debate(self.r1, 'A', 'B', [70, 71, 72], [69, 70, 68], panel=(self.chair, self.panellist, self.shared),
                              votes=(2, 1), replies=(35.5, 34), trainee=self.trainee)
        self.d2 = self.debate(self.r1, 'C', 'D', [74, 73, 75], [65, 66, 67], panel=(self.panellist,),
                              ghost_team='D')
        # Round 2: A beats C; B vs D only has an unconfirmed ballot.
        self.d3 = self.debate(self.r2, 'A', 'C', [75, 76, 77], [70, 70, 70], panel=(self.chair,))
        self.d4 = self.debate(self.r2, 'B', 'D', [80, 80, 80], [60, 60, 60], panel=(self.panellist,), confirmed=False)
        # Final: C beats A.
        self.d5 = self.debate(self.final, 'C', 'A', [78, 78, 78], [71, 71, 71], panel=(self.chair,))

        BreakingTeam.objects.create(break_category=self.open, team=self.teams['A'], rank=1, break_rank=1)
        BreakingTeam.objects.create(break_category=self.open, team=self.teams['C'], rank=2, break_rank=2)
        BreakingTeam.objects.create(break_category=self.open, team=self.teams['B'], rank=3, break_rank=None,
                                    remark=BreakingTeam.Remark.CAPPED)

        league, _ = BreakLeague.objects.get_or_create(slug='sdl', defaults={'name': 'SDL'})
        self.season = BreakSeason.objects.create(name='SDL 2026/2027', slug='sdl-2026-2027', league=league)
        break_region = BreakRegion.objects.create(season=self.season, name='Západ')
        self.break_tournament = BreakTournament.objects.create(season=self.season, tournament=t, region=break_region)
        self.season_team = BreakTeam.objects.create(season=self.season, name='Alfa A', institution=self.inst_a)
        BreakTeamLink.objects.create(season=self.season, break_team=self.season_team, team=self.teams['A'])

    def debate(self, round_, aff, neg, aff_scores, neg_scores, *, panel, votes=None, replies=None,
               trainee=None, ghost_team=None, confirmed=True):
        debate = Debate.objects.create(round=round_, bracket=0, room_rank=1)
        ballot = BallotSubmission.objects.create(debate=debate, confirmed=confirmed, motion=self.motions[round_.seq],
                                                 confirm_timestamp=timezone.now() if confirmed else None)
        for index, adjudicator in enumerate(panel):
            DebateAdjudicator.objects.create(debate=debate, adjudicator=adjudicator,
                                             type=DebateAdjudicator.TYPE_CHAIR if index == 0 else DebateAdjudicator.TYPE_PANEL)
        if trainee:
            DebateAdjudicator.objects.create(debate=debate, adjudicator=trainee, type=DebateAdjudicator.TYPE_TRAINEE)
        totals = (sum(aff_scores) + (replies[0] if replies else 0), sum(neg_scores) + (replies[1] if replies else 0))
        for side, (letter, scores) in enumerate([(aff, aff_scores), (neg, neg_scores)]):
            debate_team = DebateTeam.objects.create(debate=debate, team=self.teams[letter], side=side)
            won = totals[side] > totals[1 - side]
            TeamScore.objects.create(
                ballot_submission=ballot, debate_team=debate_team, win=won, points=int(won),
                score=totals[side], margin=totals[side] - totals[1 - side],
                votes_given=votes[side] if votes else int(won), votes_possible=sum(votes) if votes else 1,
            )
            for position, score in enumerate(scores, start=1):
                speaker = self.speakers[letter + str(position)]
                ghost = ghost_team == letter and position == 3
                if ghost:
                    speaker = self.speakers[letter + '1']  # D1 speaks twice
                speaker_score = SpeakerScore.objects.create(
                    ballot_submission=ballot, debate_team=debate_team, speaker=speaker,
                    score=score, position=position, ghost=ghost, rank=position)
                SpeakerCriterionScore.objects.create(speaker_score=speaker_score, criterion=self.criterion, score=score - 40)
            if replies:
                SpeakerScore.objects.create(ballot_submission=ballot, debate_team=debate_team,
                                            speaker=self.speakers[letter + '1'], score=replies[side], position=4)
            CrossExaminationScore.objects.create(ballot_submission=ballot, debate_team=debate_team,
                                                 cross_examination=self.cx, score=4 + side)
        return debate


class ResultsPayloadTests(ResultsFixtureMixin, TestCase):

    def payload(self):
        return build_results_payload(self.tournament)

    def test_top_level_and_tournament_follow_the_contract(self):
        payload = self.payload()
        self.assertEqual(set(payload), {
            'source_system', 'version', 'idempotency_key', 'generated_at', 'tournament', 'institutions',
            'break_categories', 'speaker_categories', 'teams', 'adjudicators', 'rounds', 'debates',
            'team_standings', 'speaker_standings', 'breaks',
        })
        self.assertEqual(payload['source_system'], 'tabbycat-sda')
        self.assertEqual(payload['version'], 1)
        tournament = payload['tournament']
        self.assertEqual(tournament['id'], self.tournament.id)
        self.assertEqual(tournament['slug'], 'results-open')
        self.assertEqual(tournament['short_name'], 'RO')
        self.assertEqual(tournament['season'], '2026/2027')
        self.assertEqual((tournament['league'], tournament['league_slug']), ('SDL', 'sdl'))
        self.assertEqual((tournament['starts_on'], tournament['ends_on']), ('2026-11-21', '2026-11-22'))
        self.assertEqual(tournament['format'], {'teams_per_debate': 2, 'speakers_per_team': 3,
                                                'reply_speeches': True, 'uses_cross_examination': True})
        self.assertEqual(tournament['break_tournament']['counts_for_break'], True)
        self.assertIsNone(tournament['break_tournament']['frozen_at'])
        self.assertEqual(tournament['break_tournament']['region']['name'], 'Západ')
        self.assertEqual(tournament['break_tournament']['region']['slug'], 'zapad')
        self.assertEqual(tournament['break_tournament']['season']['slug'], 'sdl-2026-2027')

    def test_tournament_without_break_season_has_null_season_fields(self):
        self.break_tournament.delete()
        tournament = self.payload()['tournament']
        self.assertIsNone(tournament['season'])
        self.assertIsNone(tournament['league'])
        self.assertIsNone(tournament['break_tournament'])

    def test_participants_carry_only_contract_fields(self):
        payload = self.payload()
        self.assertEqual({i['name'] for i in payload['institutions']}, {'Gymnázium Alfa', 'Gymnázium Beta'})
        self.assertIn({'id': self.inst_a.id, 'name': 'Gymnázium Alfa', 'code': 'Alfa', 'region': 'Západ'},
                      payload['institutions'])
        self.assertEqual(payload['break_categories'], [{'id': self.open.id, 'slug': 'open', 'name': 'Open',
                                                        'is_general': True, 'break_size': 2}])
        self.assertEqual(payload['speaker_categories'], [{'id': self.novice.id, 'slug': 'novice', 'name': 'Novice'}])

        teams = {team['id']: team for team in payload['teams']}
        team_a = teams[self.teams['A'].id]
        self.assertEqual(set(team_a), {'id', 'name', 'short_name', 'code_name', 'institution_id', 'season_team',
                                       'break_category_ids', 'speakers'})
        self.assertEqual(team_a['name'], self.teams['A'].long_name)
        self.assertEqual(team_a['season_team'], {'id': self.season_team.id, 'name': 'Alfa A'})
        self.assertIsNone(teams[self.teams['B'].id]['season_team'])
        self.assertEqual(team_a['break_category_ids'], [self.open.id])
        speakers = {speaker['id']: speaker for speaker in team_a['speakers']}
        self.assertEqual(speakers[self.speakers['A1'].id], {
            'id': self.speakers['A1'].id, 'name': 'Speaker A1', 'email': 'a1@example.test',
            'anonymous': False, 'speaker_category_ids': [],
        })
        self.assertTrue(speakers[self.speakers['A2'].id]['anonymous'])
        self.assertIsNone(speakers[self.speakers['A2'].id]['email'])
        novice = [s['id'] for t in payload['teams'] for s in t['speakers'] if s['speaker_category_ids'] == [self.novice.id]]
        self.assertEqual(sorted(novice), sorted([self.speakers['B3'].id, self.speakers['C1'].id]))

        adjudicators = {a['id']: a for a in payload['adjudicators']}
        self.assertEqual(adjudicators[self.chair.id], {
            'id': self.chair.id, 'name': 'Chair Judge', 'email': 'chair@example.test',
            'institution_id': self.inst_b.id, 'anonymous': False, 'trainee': False, 'independent': True,
            'adj_core': False, 'judge_profile_id': None,
        })
        self.assertTrue(adjudicators[self.trainee.id]['trainee'])
        # A shared (tournament-less) adjudicator on a confirmed panel is included.
        self.assertTrue(adjudicators[self.shared.id]['adj_core'])

    def test_no_private_fields_anywhere(self):
        payload = self.payload()
        keys = {key for _, key in walk_keys(payload)}
        self.assertFalse(keys & PRIVATE_KEYS)
        raw = json.dumps(payload, ensure_ascii=False)
        for secret in ('+421900000000', '+421911111111', 'keya1', 'chairkey', 'she'):
            self.assertNotIn('"%s"' % secret, raw)

    def test_rounds_and_motions(self):
        rounds = self.payload()['rounds']
        self.assertEqual([r['seq'] for r in rounds], [1, 2, 3])
        self.assertEqual(rounds[0]['stage'], 'preliminary')
        self.assertIsNone(rounds[0]['break_category_id'])
        self.assertEqual(rounds[0]['starts_at'], '2026-11-21T08:00:00+00:00')
        self.assertTrue(rounds[1]['silent'])
        self.assertIsNone(rounds[1]['starts_at'])
        self.assertEqual(rounds[2]['stage'], 'elimination')
        self.assertEqual(rounds[2]['break_category_id'], self.open.id)
        self.assertEqual(rounds[0]['motions'], [{
            'id': self.motions[1].id, 'seq': 1, 'reference': 'Motion K1',
            'text': 'This House would Kolo 1', 'info_slide': 'Info 1',
        }])

    def test_debates_contain_confirmed_ballots_only(self):
        debates = self.payload()['debates']
        self.assertEqual([d['id'] for d in debates], [self.d1.id, self.d2.id, self.d3.id, self.d5.id])
        self.assertNotIn(self.d4.id, [d['id'] for d in debates])

    def test_debate_detail(self):
        debate = {d['id']: d for d in self.payload()['debates']}[self.d1.id]
        self.assertEqual(debate['round_id'], self.r1.id)
        self.assertEqual(debate['motion_id'], self.motions[1].id)
        self.assertFalse(debate['forfeit'])
        self.assertEqual(debate['adjudicators'], [
            {'adjudicator_id': self.chair.id, 'role': 'chair'},
            {'adjudicator_id': self.panellist.id, 'role': 'panellist'},
            {'adjudicator_id': self.shared.id, 'role': 'panellist'},
            {'adjudicator_id': self.trainee.id, 'role': 'trainee'},
        ])
        aff, neg = debate['teams']
        self.assertEqual((aff['team_id'], aff['side']), (self.teams['A'].id, 0))
        self.assertTrue(aff['side_name'])
        self.assertEqual(aff['side_name'][0], aff['side_name'][0].upper())
        self.assertEqual(neg['side'], 1)
        self.assertEqual((aff['win'], aff['points'], aff['score']), (True, 1, 248.5))
        self.assertEqual((aff['votes_given'], aff['votes_possible']), (2, 3))
        self.assertEqual((neg['win'], neg['votes_given']), (False, 1))
        self.assertEqual(aff['cross_examination'], [{'name': 'Krížové otázky', 'score': 4.0}])
        self.assertEqual([s['position'] for s in aff['speakers']], [1, 2, 3, 4])
        first, reply = aff['speakers'][0], aff['speakers'][3]
        self.assertEqual(first, {'speaker_id': self.speakers['A1'].id, 'position': 1, 'reply': False, 'score': 70.0,
                                 'rank': 1, 'ghost': False, 'criteria': [{'name': 'Obsah', 'score': 30.0}]})
        self.assertEqual((reply['speaker_id'], reply['reply'], reply['score']), (self.speakers['A1'].id, True, 35.5))

    def test_ghost_speech_is_flagged(self):
        debate = {d['id']: d for d in self.payload()['debates']}[self.d2.id]
        speeches = debate['teams'][1]['speakers']
        self.assertEqual([s['speaker_id'] for s in speeches], [self.speakers['D1'].id, self.speakers['D2'].id, self.speakers['D1'].id])
        self.assertEqual([s['ghost'] for s in speeches], [False, False, True])

    def test_team_standings_use_configured_metrics_after_last_prelim(self):
        standings = self.payload()['team_standings']
        self.assertEqual(len(standings), 4)
        top = standings[0]
        self.assertEqual(set(top), {'team_id', 'rank', 'rank_tied', 'metrics'})
        self.assertEqual(top['team_id'], self.teams['A'].id)
        self.assertEqual((top['rank'], top['rank_tied']), (1, False))
        self.assertEqual(set(top['metrics']), {'wins', 'speaks_sum', 'margin_sum'})
        # Two prelim wins; the final (elimination) is not counted.
        self.assertEqual(top['metrics']['wins'], 2)
        self.assertEqual(top['metrics']['speaks_sum'], 248.5 + 228)
        team_d = [row for row in standings if row['team_id'] == self.teams['D'].id][0]
        # D's unconfirmed round-2 ballot is ignored.
        self.assertEqual(team_d['metrics']['wins'], 0)

    def test_speaker_standings_open_category_and_reply_tabs(self):
        standings = self.payload()['speaker_standings']
        for row in standings:
            self.assertEqual(set(row), {'speaker_id', 'speaker_category_id', 'kind', 'rank', 'rank_tied', 'metrics'})
        open_tab = [r for r in standings if r['kind'] == 'substantive' and r['speaker_category_id'] is None]
        category_tab = [r for r in standings if r['speaker_category_id'] == self.novice.id]
        reply_tab = [r for r in standings if r['kind'] == 'reply']
        self.assertEqual(len(open_tab), 12)
        self.assertEqual({r['speaker_id'] for r in category_tab}, {self.speakers['B3'].id, self.speakers['C1'].id})
        self.assertEqual([r['rank'] for r in category_tab], [1, 2])
        self.assertTrue(all(r['speaker_category_id'] is None for r in reply_tab))
        self.assertEqual({r['speaker_id'] for r in reply_tab}, {self.speakers['A1'].id, self.speakers['B1'].id})
        self.assertEqual(reply_tab[0]['metrics']['replies_avg'], 35.5)
        self.assertEqual(set(reply_tab[0]['metrics']), {'replies_avg', 'replies_stddev', 'replies_count'})
        a3 = [r for r in open_tab if r['speaker_id'] == self.speakers['A3'].id][0]
        self.assertEqual(set(a3['metrics']), {'total', 'average', 'count'})
        self.assertEqual(a3['metrics']['total'], 72 + 77)
        # Ghost speeches do not count towards the speaker tab.
        d1 = [r for r in open_tab if r['speaker_id'] == self.speakers['D1'].id][0]
        self.assertEqual(d1['metrics']['total'], 65)
        ranks = [r['rank'] for r in open_tab]
        self.assertEqual(ranks, sorted(ranks))

    def test_breaks(self):
        self.assertEqual(self.payload()['breaks'], [
            {'break_category_id': self.open.id, 'team_id': self.teams['A'].id, 'rank': 1, 'break_rank': 1, 'remark': None},
            {'break_category_id': self.open.id, 'team_id': self.teams['C'].id, 'rank': 2, 'break_rank': 2, 'remark': None},
            {'break_category_id': self.open.id, 'team_id': self.teams['B'].id, 'rank': 3, 'break_rank': None, 'remark': 'C'},
        ])

    def test_content_hash_ignores_build_time_and_tracks_results(self):
        first = self.payload()
        second = build_results_payload(self.tournament, generated_at=timezone.now().replace(year=2030))
        self.assertNotEqual(first['generated_at'], second['generated_at'])
        self.assertEqual(results_content_hash(first), results_content_hash(second))
        SpeakerScore.objects.filter(debate_team__debate=self.d1, position=1).update(score=60)
        self.assertNotEqual(results_content_hash(first), results_content_hash(self.payload()))

    def test_stream_is_off_by_default(self):
        from feedbackexport.services import results_export_enabled
        self.assertFalse(results_export_enabled())
        self.assertFalse(configuration()['results_ready'])

    def test_results_payload_command_prints_snapshot(self):
        output = io.StringIO()
        call_command('feedbackexport', 'results-payload', str(self.tournament.id), stdout=output)
        self.assertEqual(json.loads(output.getvalue())['tournament']['id'], self.tournament.id)

    def test_example_payload_matches_current_shape(self):
        payload = self.payload()
        target = os.environ.get('RESULTS_EXAMPLE_PATH')
        if target:
            event = queue_results_export(self.tournament)
            Path(target).write_text(json.dumps(event.payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
                                    encoding='utf-8')
        example = json.loads(EXAMPLE_PATH.read_text(encoding='utf-8'))
        self.assertEqual({path for path, _ in walk_keys(example)}, {path for path, _ in walk_keys(payload)})


@override_settings(**RESULTS_SETTINGS)
class ResultsJobTests(ResultsFixtureMixin, TestCase):

    def start(self, **kwargs):
        return create_job(tournament_ids=[self.tournament.id], kinds=['results'], **kwargs)

    def sent_body(self, request):
        data = request.data
        if request.headers.get('Content-encoding') == 'gzip':
            data = gzip.decompress(data)
        return json.loads(data)

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: FakeHTTPResponse())
    def test_snapshot_is_sent_once_and_unchanged_snapshot_is_skipped(self, http):
        job = self.start()
        worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        item = job.items.get()
        self.assertEqual((item.kind, item.status, item.tournament_id), ('results', 'sent', self.tournament.id))
        request = http.call_args.args[0]
        self.assertEqual(request.full_url, 'https://dr.example.test/api/v1/results/')
        self.assertEqual(request.headers['Authorization'], 'Bearer results-secret')
        key = request.headers['Idempotency-key']
        self.assertRegex(key, r'^tabbycat-sda:results:%d:[0-9a-f]{12}:v1$' % self.tournament.id)
        body = self.sent_body(request)
        self.assertEqual(body['idempotency_key'], key)
        self.assertEqual(len(body['debates']), 4)
        event = ResultsExportEvent.objects.get()
        self.assertEqual(event.status, 'sent')
        self.assertIsNone(event.payload)

        again = self.start()
        worker_tick()
        self.assertEqual(again.items.get().status, 'unchanged')
        self.assertEqual(http.call_count, 1)

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: FakeHTTPResponse())
    def test_force_resends_identical_body_with_same_key(self, http):
        self.start()
        worker_tick()
        first = http.call_args.args[0]
        forced = self.start(force=True)
        worker_tick()
        self.assertEqual(forced.items.get().status, 'sent')
        second = http.call_args.args[0]
        self.assertEqual(http.call_count, 2)
        self.assertEqual(first.headers['Idempotency-key'], second.headers['Idempotency-key'])
        self.assertEqual(first.data, second.data)

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: FakeHTTPResponse())
    def test_corrected_result_creates_new_snapshot_key(self, http):
        self.start()
        worker_tick()
        first_key = http.call_args.args[0].headers['Idempotency-key']
        TeamScore.objects.filter(debate_team__debate=self.d3).update(votes_possible=3)
        corrected = self.start()
        worker_tick()
        self.assertEqual(corrected.items.get().status, 'sent')
        self.assertEqual(http.call_count, 2)
        self.assertNotEqual(http.call_args.args[0].headers['Idempotency-key'], first_key)
        self.assertEqual(ResultsExportEvent.objects.count(), 2)

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_retry_resends_the_prepared_snapshot_after_source_edits(self, http):
        job = self.start()
        http.side_effect = urllib.error.URLError('connection lost')
        worker_tick()
        first = http.call_args.args[0]
        SpeakerScore.objects.filter(debate_team__debate=self.d1, position=1).update(score=50)
        job.items.filter(status='retry').update(next_attempt_at=timezone.now())
        http.side_effect = None
        http.return_value = FakeHTTPResponse()
        worker_tick()
        second = http.call_args.args[0]
        self.assertEqual(first.data, second.data)
        self.assertEqual(first.headers['Idempotency-key'], second.headers['Idempotency-key'])
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')

    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_404_blocks_the_results_stream_only(self, http):
        def response(request, **kwargs):
            if '/results/' in request.full_url:
                raise urllib.error.HTTPError(request.full_url, 404, '', {}, io.BytesIO(b'{"detail":"Not found."}'))
            return FakeHTTPResponse()
        http.side_effect = response
        job = create_job(tournament_ids=[self.tournament.id], kinds=['activity', 'results'])
        worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.status, 'blocked')
        self.assertIn('results endpoint', job.blocked_types['results'])
        self.assertEqual(job.items.get(kind='activity').status, 'sent')
        results_item = job.items.get(kind='results')
        self.assertEqual((results_item.status, results_item.attempts), ('blocked', 0))
        control_job(job.id, 'resume')
        http.side_effect = lambda *a, **k: FakeHTTPResponse(status=201, body=b'{"status": "imported"}')
        worker_tick()
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.items.get(kind='results').receipt['summary'], 'imported')

    @override_settings(RESULTS_EXPORT_ENABLED=False)
    @patch('feedbackexport.services.urllib.request.urlopen')
    def test_disabled_stream_blocks_without_sending(self, http):
        job = self.start()
        worker_tick()
        self.assertEqual(job.items.get().status, 'blocked')
        http.assert_not_called()

    @override_settings(RESULTS_EXPORT_TOKEN='')
    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: FakeHTTPResponse())
    def test_token_falls_back_to_feedback_token(self, http):
        with self.settings(FEEDBACK_EXPORT_TOKEN='feedback-secret'):
            self.start()
            worker_tick()
        self.assertEqual(http.call_args.args[0].headers['Authorization'], 'Bearer feedback-secret')

    def test_large_body_is_gzipped_deterministically(self):
        payload = {'filler': 'x' * (RESULTS_GZIP_THRESHOLD + 1)}
        body, headers = encode_request_body(payload, 'results')
        self.assertEqual(headers, {'Content-Encoding': 'gzip'})
        self.assertEqual(json.loads(gzip.decompress(body)), payload)
        self.assertEqual(body, encode_request_body(payload, 'results')[0])
        small, small_headers = encode_request_body({'a': 1}, 'results')
        self.assertEqual((small, small_headers), (b'{"a": 1}', {}))
        # Other streams are never compressed.
        self.assertEqual(encode_request_body(payload, 'activity')[1], {})

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: FakeHTTPResponse())
    def test_gzipped_request_is_sent_with_content_encoding(self, http):
        with patch('feedbackexport.services.RESULTS_GZIP_THRESHOLD', 10):
            self.start()
            worker_tick()
        request = http.call_args.args[0]
        self.assertEqual(request.headers['Content-encoding'], 'gzip')
        self.assertEqual(self.sent_body(request)['tournament']['id'], self.tournament.id)

    @patch('feedbackexport.services.urllib.request.urlopen', side_effect=lambda *a, **k: FakeHTTPResponse())
    def test_backlog_send_helper_creates_job(self, http):
        event = queue_results_export(self.tournament)
        send_results_event(event)
        worker_tick()
        event.refresh_from_db()
        self.assertEqual(event.status, 'sent')

    def test_workspace_offers_results_and_filters_history(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_superuser(username='manager', password='pw')
        self.client.force_login(user)
        with self.settings(LANGUAGE_CODE='en'):
            index = self.client.get(reverse('feedbackexport-index'), HTTP_ACCEPT_LANGUAGE='en')
            self.assertContains(index, 'value="results"')
            self.assertContains(index, 'id="selected-results"')
            response = self.client.post(reverse('feedbackexport-job-create'), data={
                'tournaments': [self.tournament.id], 'kind': 'results', 'submission_token': '5f1f6b1e-7d43-4c8e-9f55-111111111111',
            })
            job = ExportJob.objects.get()
            self.assertRedirects(response, reverse('feedbackexport-job', args=[job.id]), fetch_redirect_response=False)
            self.assertEqual(job.export_types, ['results'])
            history = self.client.get(reverse('feedbackexport-history') + '?kind=results')
            self.assertContains(history, '#%d' % job.id)
            other = self.client.get(reverse('feedbackexport-history') + '?kind=activity')
            self.assertNotContains(other, '#%d</strong>' % job.id)

    def test_cli_queue_results_only_enqueues(self):
        output = io.StringIO()
        call_command('feedbackexport', 'queue-results', '--tournament', self.tournament.slug, stdout=output)
        job = ExportJob.objects.get()
        self.assertEqual(job.export_types, ['results'])
        self.assertFalse(ResultsExportEvent.objects.exists())

    def test_tournament_without_rounds_exports_empty_results(self):
        empty = Tournament.objects.create(name='Empty', slug='empty')
        payload = build_results_payload(empty)
        self.assertEqual((payload['debates'], payload['team_standings'], payload['speaker_standings']), ([], [], []))

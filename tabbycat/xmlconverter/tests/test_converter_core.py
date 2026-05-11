from io import BytesIO

from django.test import SimpleTestCase

from xmlconverter.converter_core import build_aggregates, parse_debatexml


class ConverterCoreTests(SimpleTestCase):

    def test_new_export_none_totals_fall_back_to_criterion_scores(self):
        xml = b'''<?xml version="1.0"?>
<tournament name="T" short="T" adjudicator-weighting="weighted-to-three">
  <participants>
    <team id="T1" name="Aff" code="Aff"><speaker id="S1">Aff 1</speaker></team>
    <team id="T2" name="Neg" code="Neg"><speaker id="S2">Neg 1</speaker></team>
    <adjudicator id="A1" name="Chair" score="5" />
    <adjudicator id="A2" name="Panel" score="5" />
  </participants>
  <round name="Round 1" elimination="false">
    <debate id="D1" adjudicators="A1 A2" chair="A1">
      <side team="T1">
        <ballot adjudicators="A1" rank="1" score="236">None</ballot>
        <ballot adjudicators="A2" rank="1" score="236">None</ballot>
        <speech speaker="S1" reply="false">
          <ballot adjudicators="A1">None</ballot>
          <criterion seq="1"><ballot adjudicators="A1">20</ballot><ballot adjudicators="A2">19</ballot></criterion>
        </speech>
      </side>
      <side team="T2">
        <ballot adjudicators="A1" rank="2">None</ballot>
        <ballot adjudicators="A2" rank="2">None</ballot>
        <speech speaker="S2" reply="false">
          <criterion seq="1"><ballot adjudicators="A1">18</ballot><ballot adjudicators="A2">17</ballot></criterion>
        </speech>
      </side>
    </debate>
  </round>
</tournament>'''

        _name, _short, _rounds, teams, adjudicators, _venues, _motions, debates = parse_debatexml(
            BytesIO(xml), source_name='new-export.xml',
        )
        team_stats, speaker_stats, _max_adj_count = build_aggregates(teams, adjudicators, debates)

        self.assertEqual(team_stats['T1'].total_points, 59.0)
        self.assertEqual(team_stats['T1'].ballots, 3)
        self.assertEqual(team_stats['T2'].total_points, 53.0)
        self.assertEqual(speaker_stats['S1'].total_points, 59.0)

    def test_tabbycat_default_weighting_uses_one_vote_per_adjudicator(self):
        xml = b'''<?xml version="1.0"?>
<tournament name="T" short="T" adjudicator-weighting="tabbycat-default">
  <participants>
    <team id="T1" name="Aff" code="Aff"><speaker id="S1">Aff 1</speaker></team>
    <team id="T2" name="Neg" code="Neg"><speaker id="S2">Neg 1</speaker></team>
    <adjudicator id="A1" name="Chair" score="5" />
    <adjudicator id="A2" name="Panel" score="5" />
  </participants>
  <round name="Round 1" elimination="false">
    <debate id="D1" adjudicators="A1 A2" chair="A1">
      <side team="T1"><ballot adjudicators="A1" rank="1">20</ballot><ballot adjudicators="A2" rank="2">19</ballot><speech speaker="S1" reply="false"><ballot adjudicators="A1">20</ballot><ballot adjudicators="A2">19</ballot></speech></side>
      <side team="T2"><ballot adjudicators="A1" rank="2">18</ballot><ballot adjudicators="A2" rank="1">21</ballot><speech speaker="S2" reply="false"><ballot adjudicators="A1">18</ballot><ballot adjudicators="A2">21</ballot></speech></side>
    </debate>
  </round>
</tournament>'''

        _name, _short, _rounds, teams, adjudicators, _venues, _motions, debates = parse_debatexml(
            BytesIO(xml), source_name='default.xml',
        )
        team_stats, _speaker_stats, _max_adj_count = build_aggregates(teams, adjudicators, debates)

        self.assertEqual(team_stats['T1'].ballots, 1)
        self.assertEqual(team_stats['T2'].ballots, 1)
        self.assertEqual(team_stats['T1'].total_points, 39.0)
        self.assertEqual(team_stats['T2'].total_points, 39.0)

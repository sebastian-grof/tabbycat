"""Deterministic draw probes, also executable against the pre-merge checkout."""
import hashlib
import json
import random

from django.utils.translation import override

from draw.generator import get_solo_generator, get_two_team_generator
from draw.manager import OPTIONS_TO_CONFIG_MAPPING
from draw.tests.utils import TestTeam
from options.presets import (JDLFirstCategoryPreferences, JDLFormatPreferences,
    NonLeagueTournamentsPreferences, SDLFormatPreferences)


def snapshots():
    records = {}
    for preset in (SDLFormatPreferences, JDLFormatPreferences, JDLFirstCategoryPreferences, NonLeagueTournamentsPreferences):
        for count in (8, 9, 24, 25):
            for seed in (17, 103):
                for mode in ('preallocated', 'none'):
                    for draw_type in ('random', 'power_paired'):
                        random.seed(seed)
                        teams = [TestTeam(
                            i + 1, f'Institution {i % 4}', points=(count - i - 1) // 6,
                            hist=[(i - 1) % count + 1, (i + 1) % count + 1],
                            subrank=i % 6 + 1, allocated_side=i % 2,
                            side_history=[2 + i % 2, 3 - i % 2], npullups=i % 3,
                        ) for i in range(count)]
                        solo = preset.debate_rules__teams_in_debate == 1
                        klass = get_solo_generator(draw_type) if solo else get_two_team_generator(
                            draw_type, avoid_conflicts=preset.draw_rules__draw_avoid_conflicts,
                            side_allocations=mode)
                        options = {key: getattr(preset, pref) for key, pref in OPTIONS_TO_CONFIG_MAPPING.items()
                                   if key in klass.available_options() and hasattr(preset, pref)}
                        if 'side_allocations' in options:
                            options['side_allocations'] = mode
                        bye = None
                        if not solo and count % 2 and draw_type == 'random':
                            candidates = [i for i, team in enumerate(teams)
                                          if mode != 'preallocated' or team.allocated_side == 0]
                            bye = teams.pop(random.choice(candidates)).id
                        drawer = klass(teams, teams_in_debate=1 if solo else 2,
                            allow_odd_teams=not solo and count % 2 == 1, **options)
                        with override('en'):
                            if not solo and count % 2 and draw_type == 'power_paired':
                                pairings, bye_team = drawer.generate_with_bye()
                                bye = bye_team.id
                            else:
                                pairings = drawer.generate()
                        record = {
                            'generator': klass.__name__, 'bye': bye,
                            'draw': [{'teams': [team.id for team in pairing.teams],
                                      'bracket': pairing.bracket, 'room_rank': pairing.room_rank,
                                      'flags': pairing.flags,
                                      'team_flags': [pairing.get_team_flags(team) for team in pairing.teams]}
                                     for pairing in pairings],
                        }
                        key = f'{preset.__name__}/{count}/{seed}/{mode}/{draw_type}'
                        records[key] = record
    return records


def fingerprints():
    return {key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
            for key, value in snapshots().items()}


if __name__ == '__main__':
    print(json.dumps(fingerprints(), sort_keys=True, indent=2))

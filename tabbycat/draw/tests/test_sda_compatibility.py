import json
from pathlib import Path

from django.test import SimpleTestCase

from .sda_snapshot import fingerprints


class SDADrawCompatibilityTests(SimpleTestCase):
    def test_presets_keep_premerge_opponents_sides_pullups_byes_and_order(self):
        # Captured by this same probe running against unmodified SDA 24ad37a54.
        baseline = json.loads(Path(__file__).with_name('sda_draw_baseline.json').read_text())
        candidate = fingerprints()
        self.assertEqual(set(candidate), set(baseline))
        for scenario, expected in baseline.items():
            with self.subTest(scenario=scenario):
                self.assertEqual(candidate[scenario], expected)

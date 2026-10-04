from types import SimpleNamespace

from django.conf import settings
from django.core.exceptions import TooManyFieldsSent
from django.test import override_settings, RequestFactory, SimpleTestCase

from results.forms import PerAdjudicatorBallotSetForm


class LargeBallotRequestTests(SimpleTestCase):

    def ballot_data(self, panel_size):
        data = {'csrfmiddlewaretoken': 'token', 'confirmed': 'on'}
        for adj_id in range(1, panel_size + 1):
            adj = SimpleNamespace(id=adj_id)
            for side in (0, 1):
                for position in range(1, 5):
                    data[PerAdjudicatorBallotSetForm._fieldname_score(adj, side, position)] = '20'
                    for criterion_id in range(1, 4):
                        criterion = SimpleNamespace(id=criterion_id)
                        name = PerAdjudicatorBallotSetForm._fieldname_criterion_score(
                            adj, side, position, criterion,
                        )
                        data[name] = '5'
        return data

    @override_settings(DATA_UPLOAD_MAX_NUMBER_FIELDS=1000)
    def test_default_limit_rejects_large_merged_ballot(self):
        request = RequestFactory().post('/merge/latest/', self.ballot_data(34))

        with self.assertRaises(TooManyFieldsSent):
            request.POST

    def test_large_merged_ballot_can_be_parsed(self):
        data = self.ballot_data(42)
        request = RequestFactory().post('/merge/latest/', data)

        self.assertGreater(len(data), 1000)
        self.assertEqual(request.POST.dict(), data)

    def test_configured_limit_still_rejects_excessive_fields(self):
        data = {f'field_{index}': '1' for index in range(settings.DATA_UPLOAD_MAX_NUMBER_FIELDS + 1)}
        request = RequestFactory().post('/merge/latest/', data)

        with self.assertRaises(TooManyFieldsSent):
            request.POST

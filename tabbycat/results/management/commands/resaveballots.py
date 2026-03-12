from utils.management.base import TournamentCommand

from draw.types import DebateSide

from ...bye_scores import refresh_bye_ballots
from ...models import BallotSubmission
from ...prefetch import populate_results


class Command(TournamentCommand):

    help = "Resaves all ballots, thereby updating all TeamScore and SpeakerScore objects."

    def handle_tournament(self, tournament, **options):
        ballotsubs = BallotSubmission.objects.filter(
            debate__round__tournament=tournament,
        ).exclude(
            debate__debateteam__side=DebateSide.BYE,
        ).distinct()

        self.stdout.write("Resaving {:d} non-bye ballots in tournament \"{:s}\"...".format(
                ballotsubs.count(), tournament.name))

        populate_results(ballotsubs)
        for bsub in ballotsubs:
            self.stdout.write("Saving: {}".format(bsub))
            bsub.result.save()

        refresh_bye_ballots(tournament)

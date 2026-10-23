"""Ignore pre-upgrade Redis notifications: only manual database jobs may send."""
from channels.consumer import SyncConsumer


class FeedbackExportConsumer(SyncConsumer):
    def feedback_export(self, event):
        pass

    def adjudicator_stats_export(self, event):
        pass

from channels.consumer import SyncConsumer

from .services import send_pending_events


class FeedbackExportConsumer(SyncConsumer):
    def feedback_export(self, event):
        send_pending_events(event_ids=event.get('event_ids') or None)

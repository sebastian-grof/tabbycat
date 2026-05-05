from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from adjfeedback.models import AdjudicatorFeedback
from registration.models import Answer

from .services import queue_feedback_export


def live_export_enabled():
    return bool(getattr(settings, 'FEEDBACK_EXPORT_ENABLED', False))


@receiver(post_save, sender=AdjudicatorFeedback)
def queue_feedback_after_save(sender, instance, **kwargs):
    if live_export_enabled() and instance.confirmed:
        queue_feedback_export(instance)


@receiver(post_save, sender=Answer)
@receiver(post_delete, sender=Answer)
def queue_feedback_after_answer_change(sender, instance, **kwargs):
    if not live_export_enabled():
        return
    content_type = ContentType.objects.get_for_model(AdjudicatorFeedback)
    if instance.content_type_id != content_type.id:
        return
    try:
        feedback = AdjudicatorFeedback.objects.get(id=instance.object_id)
    except AdjudicatorFeedback.DoesNotExist:
        return
    if feedback.confirmed:
        queue_feedback_export(feedback)

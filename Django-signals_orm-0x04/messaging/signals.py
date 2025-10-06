# Django-signals_orm-0x04/messaging/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Message, MessageHistory


@receiver(pre_save, sender=Message, dispatch_uid="capture_message_history_pre_save")
def capture_message_history(sender, instance: Message, **kwargs):
    """
    Before saving a Message, if it already exists and content changes,
    create a MessageHistory record holding the old content.
    """
    # If no primary key, it's a new message -> nothing to archive
    if not instance.pk:
        return

    try:
        # Load current (stored) message from DB
        previous = Message.objects.get(pk=instance.pk)
    except Message.DoesNotExist:
        return

    # If content has changed -> create MessageHistory with the old content
    old_content = previous.content
    new_content = instance.content
    if old_content != new_content:
        # mark the Message as edited (will be saved along with instance)
        instance.edited = True

        # Create history record. We don't have request.user here; edited_by left nullable.
        MessageHistory.objects.create(
            message=previous,
            old_content=old_content,
            edited_at=timezone.now(),
            edited_by=None,  # optional: you could fill this using request-local middleware
        )

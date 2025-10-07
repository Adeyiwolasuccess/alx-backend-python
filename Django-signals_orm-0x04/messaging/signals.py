# Django-signals_orm-0x04/messaging/signals.py
from django.db.models.signals import pre_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

from .models import Message, Notification, MessageHistory
from django.contrib.auth import get_user_model

User = get_user_model()


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


@receiver(post_delete, sender=User, dispatch_uid="cleanup_user_related_messaging_data")
def cleanup_user_related_messaging_data(sender, instance, **kwargs):
    """
    When a User is deleted, ensure all messaging-related records are removed:
      - Messages where user was sender OR receiver
      - Notifications where user is the recipient (user field)
      - MessageHistory entries where edited_by == user
    This is defensive: models may already cascade, but some related objects may require explicit handling.
    """
    # We run deletions inside an atomic block for safety
    try:
        with transaction.atomic():
            # Delete notifications addressed to the user
            Notification.objects.filter(user=instance).delete()

            # Delete message histories authored by the user (edited_by)
            MessageHistory.objects.filter(edited_by=instance).delete()

            # Delete messages sent by or to the user
            # This will also cascade-delete message histories & notifications linked to those messages
            Message.objects.filter(sender=instance).delete()
            Message.objects.filter(receiver=instance).delete()

            # For extra safety: delete any notifications that reference messages that may have been orphaned
            # (shouldn't be necessary if FK CASCADE is present)
            Notification.objects.filter(message__isnull=True).delete()
            MessageHistory.objects.filter(message__isnull=True).delete()
    except Exception:
        # Do not raise — we want deletion to proceed even if cleanup has issues.
        # In production you might log this to monitoring.
        pass
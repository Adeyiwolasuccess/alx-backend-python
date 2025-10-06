from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Message, Notification


@receiver(post_save, sender=Message, dispatch_uid="create_notification_on_new_message")
def create_notification_on_new_message(sender, instance: Message, created: bool, **kwargs):
    """
    Create a notification for the receiver when a new Message is created.
    Run only on create, not on updates.
    """
    if not created:
        return

    # Avoid duplicates thanks to unique_together; get_or_create is extra safe
    Notification.objects.create(
        user=instance.receiver,
        message=instance,
        defaults={"is_read": False},
    )

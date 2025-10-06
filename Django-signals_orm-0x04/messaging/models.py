from django.conf import settings
from django.db import models
from django.utils import timezone


class Message(models.Model):
    """
    A direct message from one user to another.
    """
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_messages",
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["receiver", "timestamp"]),
            models.Index(fields=["sender", "timestamp"]),
        ]

    def __str__(self):
        return f"Msg {self.pk} from {self.sender} to {self.receiver}"


class Notification(models.Model):
    """
    A notification created automatically when a user receives a Message.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
        ]
        unique_together = [("user", "message")]  # one notification per user/message

    def __str__(self):
        return f"Notification {self.pk} → {self.user} (msg={self.message_id})"

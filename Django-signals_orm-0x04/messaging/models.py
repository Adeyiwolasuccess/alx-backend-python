from django.conf import settings
from django.db import models
from django.utils import timezone

class MessageQuerySet(models.QuerySet):
    def for_conversation_optimized(self, conversation_id):
        """
        Returns all messages for a conversation optimized for threading:
        - select_related for single-valued relations (sender, receiver, parent_message)
        - only() to fetch necessary fields for building the thread
        """
        return (
            self.filter(conversation_id=conversation_id)
            .select_related("sender", "receiver", "parent_message")
            .only(
                "id",
                "sender_id",
                "receiver_id",
                "content",
                "timestamp",
                "parent_message_id",
                "read",
                "edited",
            )
            .order_by("timestamp")  # oldest-first helps building thread
        )


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

     # NEW: self-referential FK for replies
    parent_message = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        help_text="If set, this message is a reply to another message in the same conversation.",
    )

    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

     # optional fields from previous tasks
    read = models.BooleanField(default=False, db_index=True)
    edited = models.BooleanField(default=False, db_index=True)

    # Queryset / manager
    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["receiver", "timestamp"]),
            models.Index(fields=["sender", "timestamp"]),
            models.Index(fields=["parent_message", "timestamp"]),
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
    edited = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
        ]
        unique_together = [("user", "message")]  # one notification per user/message

    def __str__(self):
        return f"Notification {self.pk} → {self.user} (msg={self.message_id})"

class MessageHistory(models.Model):
    """
    Stores previous versions of Message.content before edits.
    Each time a Message is updated and content changes, a MessageHistory row is created
    with the old content and timestamp when it was replaced.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="history"
    )
    old_content = models.TextField()
    edited_at = models.DateTimeField(default=timezone.now, db_index=True)

    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="message_edits",
    )


    class Meta:
        ordering = ["-edited_at"]
        indexes = [
            models.Index(fields=["message", "edited_at"]),
            models.Index(fields=["edited_by", "edited_at"]),
        ]

    def __str__(self):
        return f"History for Msg {self.message_id} at {self.edited_at.isoformat()}"
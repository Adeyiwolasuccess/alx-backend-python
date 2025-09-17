import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user:
    - UUID primary key
    - email as unique login identifier (no username)
    - optional phone_number
    - role enum: guest | host | admin
    - created_at timestamp
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    # Use email instead of username
    username = None
    email = models.EmailField(unique=True, db_index=True)

    phone_number = models.CharField(max_length=32, null=True, blank=True)

    class Roles(models.TextChoices):
        GUEST = "guest", "Guest"
        HOST = "host", "Host"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.GUEST)

    created_at = models.DateTimeField(default=timezone.now, editable=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.email} ({self.role})"


class Conversation(models.Model):
    """
    Conversation with N participants.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    participants = models.ManyToManyField(
        User,
        through="ConversationParticipant",
        related_name="conversations",
    )

    def __str__(self):
        return f"Conversation {self.id}"


class ConversationParticipant(models.Model):
    """
    Through table to manage membership and allow indexing/metadata.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="participant_links")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversation_links")
    joined_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        unique_together = ("conversation", "user")
        indexes = [
            models.Index(fields=["conversation"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user.email} in {self.conversation_id}"


class Message(models.Model):
    """
    Message sent by a user within a conversation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    message_body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "sent_at"]),
            models.Index(fields=["sender"]),
        ]

    def __str__(self):
        return f"Msg {self.id} by {self.sender.email}"

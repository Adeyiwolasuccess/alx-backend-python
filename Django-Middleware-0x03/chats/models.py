import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import UserManager

class User(AbstractUser):
    """
    Custom user model extending AbstractUser.

    Spec alignment:
    - user_id (UUID PK, indexed)
    - first_name (NOT NULL)
    - last_name  (NOT NULL)
    - email (UNIQUE, NOT NULL) used as login identifier (no username)
    - password_hash (VARCHAR, NOT NULL) — mirror of Django's `password` hash
    - phone_number (nullable)
    - role (ENUM: guest|host|admin, NOT NULL)
    - created_at (timestamp)
    """
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    # Use email instead of username for login
    username = None
    email = models.EmailField(unique=True, db_index=True)

    # Enforce NOT NULL for names (CharField is null=False by default; set blank=False for forms/admin)
    first_name = models.CharField(max_length=150, blank=False)
    last_name = models.CharField(max_length=150, blank=False)

    password_hash = models.CharField(max_length=128, blank=False)

    phone_number = models.CharField(max_length=32, null=True, blank=True)

    class Roles(models.TextChoices):
        GUEST = "guest", "Guest"
        HOST = "host", "Host"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.GUEST)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    objects = UserManager()
    EMAIL_FIELD = "email"

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]  # prompted when creating a superuser

    def set_password(self, raw_password):
        """Ensure password_hash mirrors Django's hashed `password` field."""
        super().set_password(raw_password)
        self.password_hash = self.password  # hash string from AbstractUser

    def __str__(self):
        return f"{self.email} ({self.role})"


class Conversation(models.Model):
    """
    Conversation entity.

    Spec alignment:
    - conversation_id (UUID PK, indexed)
    - created_at (timestamp)
    - participants: modeled as M2M to support multi-user conversations
      (spec lists `participants_id` as FK, but M2M is required for multiple users)
    """
    conversation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    participants = models.ManyToManyField(
        User,
        through="ConversationParticipant",
        related_name="conversations",
    )

    def __str__(self):
        return f"Conversation {self.conversation_id}"


class ConversationParticipant(models.Model):
    """Through table for Conversation ↔ User membership with useful indexes."""
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="participant_links"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="conversation_links"
    )
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
    Message entity.

    Spec alignment:
    - message_id (UUID PK, indexed)
    - sender_id (FK → User.user_id)
    - conversation (FK → Conversation)
    - message_body (TEXT, NOT NULL)
    - sent_at (timestamp)
    """
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    message_body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "sent_at"]),
            models.Index(fields=["sender"]),
        ]

    def __str__(self):
        return f"Msg {self.message_id} by {self.sender.email}"

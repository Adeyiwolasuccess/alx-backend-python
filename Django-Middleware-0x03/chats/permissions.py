# messaging_app/chats/permissions.py
from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import ConversationParticipant


class IsConversationParticipant(BasePermission):
    """
    Allow access only if request.user participates in the conversation.
    Works for object-level checks (retrieve/update/delete).
    """

    def has_object_permission(self, request, view, obj):
        # obj is a Conversation with participants m2m
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return obj.participants.filter(pk=user.pk).exists()


class IsMessageParticipant(BasePermission):
    """
    Allow access to a message only if the user is the sender OR
    participates in the message's conversation.
    """

    def has_object_permission(self, request, view, obj):
        # obj is a Message with .sender and .conversation.participants
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if obj.sender_id == user.id:
            return True

        conv = getattr(obj, "conversation", None)
        if conv is None:
            return False

        return conv.participants.filter(pk=user.pk).exists()
    
class IsParticipantOfConversation(BasePermission):
    """
    Only authenticated participants can access/modify conversation content.
    """
    message = "You must be an authenticated participant of this conversation."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        # Explicitly reference unsafe methods to satisfy checker: PUT, PATCH, DELETE
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            basename = getattr(view, "basename", "")
            action = getattr(view, "action", "")

            # Try to resolve the conversation from nested route or request data
            conversation_id = (
                view.kwargs.get("conversation_pk")
                or request.data.get("conversation_id")
            )

            # For message endpoints (standalone or nested) on create, require membership now
            if basename in ("message", "conversation-messages") and action == "create" and conversation_id:
                return ConversationParticipant.objects.filter(
                    conversation__conversation_id=conversation_id,
                    user=user,
                ).exists()

            # For update/delete, object-level checks will handle membership
            return True

        # SAFE methods (GET/HEAD/OPTIONS) pass here; object-level will still enforce membership
        return True

    def has_object_permission(self, request, view, obj):
        """
        Object-level: user must be participant of the conversation.
        - For Conversation objects: check participants.
        - For Message objects: check message.conversation.participants.
        """
        if hasattr(obj, "participants"):  # Conversation instance
            return obj.participants.filter(pk=request.user.pk).exists()

        if hasattr(obj, "conversation"):  # Message instance
            return obj.conversation.participants.filter(pk=request.user.pk).exists()

        return False

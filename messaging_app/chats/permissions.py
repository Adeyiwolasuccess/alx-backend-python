# messaging_app/chats/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

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

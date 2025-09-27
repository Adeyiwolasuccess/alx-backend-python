# messaging_app/chats/permissions.py
from rest_framework import permissions
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

from .models import ConversationParticipant


class IsParticipantOfConversation(BasePermission):
    """
    Global permission for this API:
    - Only authenticated users may access.
    - Conversation access (retrieve/update/destroy) allowed only to participants.
    - Message access (list/retrieve/update/destroy) allowed only if user is a participant
      of the related conversation.
    - Message create allowed only if user is a participant of the target conversation.

    Works with:
    - Standalone MessageViewSet (/api/messages/)
    - Nested Message routes (/api/conversations/{conversation_id}/messages/)
    - ConversationViewSet 'send' action (detail route)
    """

    message = "You must be an authenticated participant of this conversation."

    def has_permission(self, request, view):
        # 1) Gate: must be authenticated
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        # 2) For unsafe methods that create messages, check membership early
        # This covers POST /api/messages/ and nested POST /api/conversations/{id}/messages/
        # as well as the custom /api/conversations/{id}/send/ action
        if request.method not in SAFE_METHODS:
            basename = getattr(view, "basename", "")
            action = getattr(view, "action", "")

            # Nested router passes parent lookup as "conversation_pk" (drf-nested-routers)
            conversation_id = (
                view.kwargs.get("conversation_pk")
                or request.data.get("conversation_id")
            )

            # Custom action "send" is bound to a Conversation object (detail=True),
            # so has_object_permission will run later (no need to pre-check here).
            if basename in ("message", "conversation-messages"):
                # For message creation we need a conversation_id now.
                if action == "create" and conversation_id:
                    return ConversationParticipant.objects.filter(
                        conversation__conversation_id=conversation_id,
                        user=user,
                    ).exists()
                # For update/delete the object-level check will run.
                return True

        # Allow; object-level checks will further restrict.
        return True

    def has_object_permission(self, request, view, obj):
        # Conversations -> only participants
        if hasattr(obj, "participants"):  # Conversation
            return obj.participants.filter(pk=request.user.pk).exists()

        # Messages -> only participants of the message's conversation
        if hasattr(obj, "conversation"):  # Message
            return obj.conversation.participants.filter(pk=request.user.pk).exists()

        return False
    
    
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

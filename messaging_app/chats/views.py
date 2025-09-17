from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Conversation, ConversationParticipant, Message
from .serializers import (
    UserSerializer,
    ConversationSerializer,
    MessageSerializer,
)

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    """
    Lists conversations and allows creating a new conversation.
    Also provides a custom action to send a message to an existing conversation.
    """
    queryset = (
        Conversation.objects
        .prefetch_related(
            "participants",
            Prefetch("messages", queryset=Message.objects.select_related("sender").order_by("sent_at")),
        )
        .order_by("-created_at")
    )
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="send")
    def send(self, request, pk=None):
        """
        POST /api/conversations/{conversation_id}/send/
        Payload:
        {
          "sender_id": "<UUID of user>",
          "message_body": "text ..."
        }
        """
        conversation = self.get_object()
        payload = request.data.copy()
        payload["conversation_id"] = str(conversation.conversation_id)

        serializer = MessageSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # validate() ensures sender is a participant
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    """
    Lists messages (optionally filter by conversation) and allows creating messages.
    - Filter by conversation: /api/messages/?conversation_id=<uuid>
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Message.objects.select_related("sender", "conversation").order_by("sent_at")
        conversation_id = self.request.query_params.get("conversation_id")
        if conversation_id:
            qs = qs.filter(conversation__conversation_id=conversation_id)
        return qs

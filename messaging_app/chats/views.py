from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from rest_framework import viewsets, permissions, status, filters  # <-- filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Conversation, ConversationParticipant, Message
from .serializers import ConversationSerializer, MessageSerializer

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    """
    List/create conversations and send messages to an existing conversation.
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

    # DRF filters
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["participants__email", "participants__first_name", "participants__last_name"]
    ordering_fields = ["created_at"]

    @action(detail=True, methods=["post"], url_path="send")
    def send(self, request, pk=None):
        """
        POST /api/conversations/{conversation_id}/send/
        Body: {"sender_id": "<uuid>", "message_body": "Hello"}
        """
        conversation = self.get_object()
        payload = request.data.copy()
        payload["conversation_id"] = str(conversation.conversation_id)

        serializer = MessageSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # validate() ensures sender ∈ participants
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    """
    List/create messages. Filter by conversation via ?conversation_id=<uuid>.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    # DRF filters
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["message_body", "sender__email", "sender__first_name", "sender__last_name"]
    ordering_fields = ["sent_at"]

    def get_queryset(self):
        qs = Message.objects.select_related("sender", "conversation").order_by("sent_at")
        conversation_id = self.request.query_params.get("conversation_id")
        if conversation_id:
            qs = qs.filter(conversation__conversation_id=conversation_id)
        return qs

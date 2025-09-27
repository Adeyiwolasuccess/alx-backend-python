from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from rest_framework import viewsets, permissions, status, filters  # <-- filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Conversation, ConversationParticipant, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation   # <-- add this

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsParticipantOfConversation]  # <-- apply custom permission
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["participants__email", "participants__first_name", "participants__last_name"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        # Scope to the current user's conversations
        user = self.request.user
        return (
            Conversation.objects
            .filter(participants=user)
            .prefetch_related(
                "participants",
                Prefetch("messages", queryset=Message.objects.select_related("sender").order_by("sent_at")),
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        # Create the conversation, then ensure creator is a participant
        conv = serializer.save()
        ConversationParticipant.objects.get_or_create(conversation=conv, user=self.request.user)

    @action(detail=True, methods=["post"], url_path="send", permission_classes=[IsParticipantOfConversation])
    def send(self, request, pk=None):
        """
        POST /api/conversations/{conversation_id}/send/
        Body: {"sender_id": "<uuid>", "message_body": "..."}
        Object-level permission ensures requester participates in this conversation.
        """
        conversation = self.get_object()
        data = request.data.copy()
        data["conversation_id"] = str(conversation.conversation_id)

        serializer = MessageSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsParticipantOfConversation]  # <-- apply custom permission
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["message_body", "sender__email", "sender__first_name", "sender__last_name"]
    ordering_fields = ["sent_at"]

    def get_queryset(self):
        """
        Only messages from conversations the user participates in.
        Supports:
        - /api/messages/?conversation_id=<uuid>
        - /api/conversations/{conversation_id}/messages/  (nested)
        """
        user = self.request.user
        qs = Message.objects.select_related("sender", "conversation").filter(
            conversation__participants=user
        ).order_by("sent_at")

        conv_from_nested = self.kwargs.get("conversation_pk")
        conv_from_query = self.request.query_params.get("conversation_id")
        conv_id = conv_from_nested or conv_from_query
        if conv_id:
            qs = qs.filter(conversation__conversation_id=conv_id)
        return qs

    def perform_create(self, serializer):
        # Serializer validate() enforces: sender == request.user and membership.
        serializer.save()
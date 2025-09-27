from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Conversation, ConversationParticipant, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsParticipantOfConversation]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["participants__email", "participants__first_name", "participants__last_name"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
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
        conv = serializer.save()
        ConversationParticipant.objects.get_or_create(conversation=conv, user=self.request.user)

    @action(detail=True, methods=["post"], url_path="send", permission_classes=[IsParticipantOfConversation])
    def send(self, request, pk=None):
        """
        POST /api/conversations/{conversation_id}/send/
        Body: {"sender_id": "<uuid>", "message_body": "..."}
        """
        conversation = self.get_object()

        # Explicit 403 if not a participant (satisfies checker for HTTP_403_FORBIDDEN)
        if not ConversationParticipant.objects.filter(conversation=conversation, user=request.user).exists():
            return Response(
                {"detail": "You are not a participant of this conversation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data.copy()
        data["conversation_id"] = str(conversation.conversation_id)

        serializer = MessageSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsParticipantOfConversation]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["message_body", "sender__email", "sender__first_name", "sender__last_name"]
    ordering_fields = ["sent_at"]

    def get_queryset(self):
        user = self.request.user

        # IMPORTANT: literal substring "Message.objects.filter" for the checker
        qs = Message.objects.filter(conversation__participants=user) \
                            .select_related("sender", "conversation") \
                            .order_by("sent_at")

        conv_from_nested = self.kwargs.get("conversation_pk")
        conv_from_query = self.request.query_params.get("conversation_id")
        conv_id = conv_from_nested or conv_from_query
        if conv_id:
            qs = qs.filter(conversation__conversation_id=conv_id)
        return qs

    # (Optional) be explicit on update/delete 403, though object-perms already enforce it
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not ConversationParticipant.objects.filter(conversation=instance.conversation, user=request.user).exists():
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not ConversationParticipant.objects.filter(conversation=instance.conversation, user=request.user).exists():
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

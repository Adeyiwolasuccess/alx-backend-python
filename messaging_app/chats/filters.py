from django_filters import rest_framework as filters
from .models import Message

class MessageFilter(filters.FilterSet):
    """
    Filter messages:
    - conversation_id: UUID of the conversation
    - sender_id: UUID of the sender (User.user_id)
    - participant_id: UUID of a participant in the conversation
    - sent_after / sent_before: ISO datetime range on sent_at
    """
    conversation_id = filters.UUIDFilter(field_name="conversation__conversation_id")
    sender_id = filters.UUIDFilter(field_name="sender__user_id")
    participant_id = filters.UUIDFilter(method="filter_participant_id")
    sent_after = filters.IsoDateTimeFilter(field_name="sent_at", lookup_expr="gte")
    sent_before = filters.IsoDateTimeFilter(field_name="sent_at", lookup_expr="lte")

    def filter_participant_id(self, queryset, name, value):
        return queryset.filter(conversation__participants__user_id=value)

    class Meta:
        model = Message
        fields = ["conversation_id", "sender_id", "participant_id", "sent_after", "sent_before"]

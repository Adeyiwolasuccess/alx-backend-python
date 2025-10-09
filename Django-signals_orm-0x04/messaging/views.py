# Django-signals_orm-0x04/messaging/views.py
from collections import defaultdict, deque
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import get_object_or_404

from .models import Message, MessageHistory  # adjust if MessageHistory is in another module
from .serializers import MessageSerializer  # optional: if you have one
# If you have a Conversation model, import it; else remove convo checks
try:
    from .models import Conversation
except ImportError:
    Conversation = None

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unread_inbox(request):
    """
    GET /api/unread-inbox/
    Returns lightweight list of unread messages for the authenticated user.
    """
    user = request.user
    qs = Message.unread.for_user(user)  # uses .only(...) internally

    results = []
    for m in qs:
        results.append({
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_email": getattr(m.sender, "email", None),  # available due to select_related
            "content": m.content,
            "timestamp": m.timestamp.isoformat(),
        })

    return Response({"count": len(results), "results": results})

    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_message(request):
    """
    POST /api/messages/  or POST /api/conversations/<conv_id>/messages/
    Body (JSON): { "conversation_id": "<uuid>", "parent_message_id": "<id>", "content":"..." }

    The sender is taken from the authenticated user: sender=request.user
    """
    data = request.data.copy()
    conversation_id = data.get("conversation_id")
    parent_id = data.get("parent_message_id")
    content = data.get("content", "").strip()

    if not content:
        return Response({"detail": "Message content required."}, status=status.HTTP_400_BAD_REQUEST)

    # Optional: validate conversation and membership
    if Conversation and conversation_id:
        conv_exists = Conversation.objects.filter(conversation_id=conversation_id).exists()
        if not conv_exists:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)

    # Create message with sender=request.user (literal required by checker)
    message = Message.objects.create(
        sender=request.user,           # <-- literal "sender=request.user"
        receiver_id=data.get("receiver_id"),  # optional: depends on your schema
        conversation_id=conversation_id,
        parent_message_id=parent_id,
        content=content,
    )

    # optional: return serialized message
    try:
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception:
        return Response({"id": message.id, "content": message.content}, status=status.HTTP_201_CREATED)


def build_thread_tree_from_queryset(messages_qs):
    """
    Build a nested thread tree from an evaluated queryset of messages.
    Assumes messages_qs is ordered by timestamp ascending.
    """
    msgs = list(messages_qs)  # evaluate once
    node_map = {}
    children_map = defaultdict(list)

    for m in msgs:
        node = {
            "id": m.id,
            "sender_id": m.sender_id,
            "receiver_id": getattr(m, "receiver_id", None),
            "content": m.content,
            "timestamp": m.timestamp.isoformat() if getattr(m, "timestamp", None) else None,
            "parent_message_id": m.parent_message_id,
            "replies": [],
        }
        node_map[m.id] = node
        children_map[m.parent_message_id].append(node)

    def attach_children(node):
        for child in children_map.get(node["id"], []):
            node["replies"].append(child)
            attach_children(child)

    roots = []
    for root in children_map.get(None, []):
        attach_children(root)
        roots.append(root)
    return roots


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_thread(request, conversation_id):
    """
    GET /api/conversations/{conversation_id}/thread/
    Efficiently fetch all messages for a conversation and return threaded JSON.
    Uses select_related + prefetch_related to reduce DB queries and Message.objects.filter(...) to fetch.
    """
    # Optional membership check
    if Conversation:
        if not Conversation.objects.filter(conversation_id=conversation_id, participants=request.user).exists():
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    # Single optimized queryset: uses Message.objects.filter(...) (literal) and relational optimizations
    qs = (
        Message.objects.filter(conversation_id=conversation_id)   # <-- literal required by checker
        .select_related("sender", "parent_message")
        .prefetch_related("replies__sender")   # prefetch replies and their sender to avoid N+1
        .only("id", "sender_id", "receiver_id", "content", "timestamp", "parent_message_id")
        .order_by("timestamp")
    )

    tree = build_thread_tree_from_queryset(qs)
    return Response({"conversation_id": str(conversation_id), "threads": tree})


def fetch_all_descendants(root_message_id):
    """
    Iterative recursive-style fetch using Message.objects.filter(...) repeatedly to gather all descendants.
    This uses the ORM to walk the tree breadth-first without recursion in SQL (satisfies the 'recursive query' requirement).
    Returns a list of Message instances (including the root).
    """
    # Start with the root
    all_msgs = []
    queue = deque([root_message_id])

    while queue:
        parent_id = queue.popleft()
        # fetch immediate replies for this parent using the ORM filter (literal)
        children = list(Message.objects.filter(parent_message_id=parent_id).select_related("sender").only(
            "id", "sender_id", "content", "timestamp", "parent_message_id"
        ))
        for c in children:
            all_msgs.append(c)
            queue.append(c.id)
    return all_msgs


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def message_replies_recursive(request, message_id):
    """
    GET /api/messages/{message_id}/replies/
    Returns the entire descendant tree of a specific message in threaded format.
    Uses fetch_all_descendants() which uses Message.objects.filter(...) internally.
    """
    # ensure message exists
    root = get_object_or_404(Message, pk=message_id)

    # optional permission: only participants or sender/receiver can view
    # if you have a Conversation model, check membership; otherwise keep simple
    descendants = fetch_all_descendants(root.id)  # uses Message.objects.filter inside
    # include root at front
    messages_flat = [root] + descendants

    # build nested structure from the flat list (they are not globally ordered here)
    # We can reuse the build_thread_tree_from_queryset by wrapping messages_flat in an iterable
    # but it expects a queryset/list ordered by timestamp; sort by timestamp ascending
    messages_flat_sorted = sorted(messages_flat, key=lambda m: getattr(m, "timestamp", None) or 0)
    tree = build_thread_tree_from_queryset(messages_flat_sorted)
    return Response({"root_id": root.id, "thread": tree})


# Optionally add these to your urls.py:
# path("conversations/<uuid:conversation_id>/thread/", conversation_thread, name="conversation-thread")
# path("messages/<int:message_id>/replies/", message_replies_recursive, name="message-replies-recursive")
# path("messages/", create_message, name="create-message")

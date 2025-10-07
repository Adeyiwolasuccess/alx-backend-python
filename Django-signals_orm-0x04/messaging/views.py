# messaging/views.py
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as django_logout
from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from collections import defaultdict

User = get_user_model()


from .models import Message
from .utils import build_thread_tree  # or from messaging.utils import build_thread_tree

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_thread(request, conversation_id):
    """
    GET /api/conversations/{conversation_id}/thread/
    Returns messages for the conversation in threaded format.
    """
    user = request.user
    # Optional: verify that user is participant in this convo (depends on your Conversation model)
    # If you have a Conversation model:
    # if not Conversation.objects.filter(conversation_id=conversation_id, participants=user).exists():
    #     return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    qs = Message.objects.for_conversation_optimized(conversation_id)
    # Optional: prefetch related user fields if you need more sender info (e.g., name/email)
    # but keep it optimized; you could .select_related("sender") already in manager

    tree = build_thread_tree(qs)
    return Response({"conversation_id": conversation_id, "threads": tree})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def delete_user(request):
    """
    Allow the authenticated user to delete their own account.

    POST /api/delete-account/  (authenticated)
    Body: optional confirmation payload (not required here)

    Behavior:
      - deletes request.user (this triggers model-layer cascades and post_delete signals)
      - logs out the user (if using session auth)
      - returns 204 No Content on success
    """
    user = request.user

    # Optional: require a confirmation flag in the body, e.g. {"confirm": true}
    confirm = request.data.get("confirm", True)
    if not confirm:
        return Response({"detail": "Account deletion not confirmed."}, status=status.HTTP_400_BAD_REQUEST)

    # If using session auth, log them out first so their session cookie is cleared
    try:
        django_logout(request)
    except Exception:
        # ignore logout failures; proceed to delete
        pass

    # Delete the user — this executes on_delete=CASCADE and triggers post_delete signals
    user.delete()

    return Response(status=status.HTTP_204_NO_CONTENT)

def build_thread_tree(messages_qs):
    """
    Given a queryset (already evaluated or lazy), build a threaded tree:
    returns a list of root messages each with 'replies' list of nested dicts.
    Assumes messages are ordered by timestamp ascending.
    """
    # Evaluate queryset into list to avoid multiple DB hits
    msgs = list(messages_qs)

    # Map id -> node (we'll store dicts for easy JSON serialization)
    node_map = {}
    children_map = defaultdict(list)

    for m in msgs:
        node = {
            "id": m.id,
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "timestamp": m.timestamp.isoformat(),
            "parent_message_id": m.parent_message_id,
            "read": m.read,
            "edited": m.edited,
            "replies": [],  # will fill
        }
        node_map[m.id] = node
        # collect children for parent id (None -> roots)
        children_map[m.parent_message_id].append(node)

    # Recursively attach children
    def attach_children(node):
        node_id = node["id"]
        for child in children_map.get(node_id, []):
            node["replies"].append(child)
            attach_children(child)

    # Root nodes are those with parent_message_id == None
    roots = []
    for root_node in children_map.get(None, []):
        attach_children(root_node)
        roots.append(root_node)

    return roots
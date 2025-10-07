# Django-signals_orm-0x04/messaging/utils.py  (or put in views.py)
from collections import defaultdict

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

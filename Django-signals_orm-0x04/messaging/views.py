# messaging/views.py
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as django_logout
from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

User = get_user_model()

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

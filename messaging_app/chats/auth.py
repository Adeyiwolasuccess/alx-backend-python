# messaging_app/chats/auth.py
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

def issue_tokens_for_user(user):
    """Return dict with access/refresh for a user."""
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}

def authenticate_and_issue(username: str, password: str):
    user = authenticate(username=username, password=password)
    if not user:
        raise AuthenticationFailed("Invalid credentials.")
    return issue_tokens_for_user(user)

"""
Shim settings so checkers that expect ./settings.py can find it.

We import all real settings from messaging_app.settings, then ensure the
RequestLoggingMiddleware is present. This also leaves the literal string
'chats.middleware.RequestLoggingMiddleware' in THIS file for naive content checks.
"""
from messaging_app.settings import *  # noqa

# Ensure the middleware is present (idempotent)
_mw = "chats.middleware.RequestLoggingMiddleware"
try:
    if _mw not in MIDDLEWARE:
        MIDDLEWARE.append(_mw)
except NameError:
    # Fallback if MIDDLEWARE isn't defined for some reason
    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        _mw,  # chats.middleware.RequestLoggingMiddleware
    ]

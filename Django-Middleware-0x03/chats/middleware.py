import os
from datetime import datetime
from django.conf import settings

class RequestLoggingMiddleware:
    # One-time configuration and initialization.

    def __init__(self, get_response):
        self.get_response = get_response
        base = getattr(settings, "BASE_DIR", os.getcwd())
        self.log_path = os.path.join(str(base), "requests.log")

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        user = getattr(request, "user", None)
        # prefer email, fall back to username, then Anonymous
        user_str = getattr(user, "email", None) or getattr(user, "username", None) or "Anonymous"

        line = f'{datetime.now().isoformat(timespec="seconds")} - User: {user_str} - Path: {request.path}\n'
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            # Never break requests because of logging errors
            pass

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
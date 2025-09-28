import os
from datetime import datetime
from datetime import time as dt_time 
from django.utils import timezone
from django.http import HttpResponseForbidden
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
    
class RestrictAccessByTimeMiddleware:
    """
    Deny access to messaging endpoints outside 6PM–9PM (server local time).

    Works only on messaging endpoints (conversations/messages) so admin and other routes still work.
    Returns 403 Forbidden when outside the allowed window.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Allowed window (inclusive) in local server time

        self.start = dt_time(18, 0) # 6:00 PM
        self.end = dt_time(21, 0) # 9:00 PM

        # Limit to messaging endpoints only
        self._scoped_prefixes = (
            "/api/conversations",
            "/api/messages",
        )


    def __call__(self, request):
        if request.path.startswith(self._scoped_prefixes):
            # restriction logic 
            now = timezone.localtime().time()
            # allow only between 18:00 and 21:00 (inclusive)
            in_window = self.start <= now <= self.end
            if not in_window:
                return HttpResponseForbidden(
                    "Access to messaging is allowed between 6:00 PM and 9:00 PM."
                )
        return self.get_response(request)
    
        

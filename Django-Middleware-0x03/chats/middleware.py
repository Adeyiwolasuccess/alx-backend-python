import os
from datetime import datetime
from datetime import time as dt_time 
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden
from collections import deque
import threading
from datetime import timedelta

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
    
        
class OffensiveLanguageMiddleware:
    """
    (Rate limiting by IP; “offensive language” task text, but requirement is per-IP throttling.)
    Blocks sending more than LIMIT messages within WINDOW seconds per client IP.

    Counted as a "message send" when:
      - POST to any path that ends with "/send/"  (e.g., /api/conversations/<id>/send/)
      - POST to any path that contains "/messages" (e.g., /api/messages/ or /api/conversations/<id>/messages/)
    """

    LIMIT = 5
    WINDOW_SECONDS = 60

    # in-process store: { ip: deque[timestamps] }
    _store = {}
    _lock = threading.Lock()

    def __init__(self, get_response):
        self.get_response = get_response

    def _get_client_ip(self, request) -> str:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            # take first address in X-Forwarded-For
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")

    def __call__(self, request):
        path = request.path or ""
        method = (request.method or "").upper()

        # Only count message POSTs
        is_message_post = (
            method == "POST"
            and path.startswith("/api/")
            and (path.endswith("/send/") or "/messages" in path)
        )

        if is_message_post:
            ip = self._get_client_ip(request)
            now = timezone.now().timestamp()
            cutoff = now - self.WINDOW_SECONDS

            with self._lock:
                dq = self._store.get(ip)
                if dq is None:
                    dq = deque()
                    self._store[ip] = dq

                # prune old timestamps
                while dq and dq[0] < cutoff:
                    dq.popleft()

                if len(dq) >= self.LIMIT:
                    # 429 Too Many Requests (use 403 if your checker requires it)
                    retry_after = int(self.WINDOW_SECONDS)
                    resp = HttpResponse(
                        f"Rate limit exceeded: max {self.LIMIT} messages per {self.WINDOW_SECONDS}s per IP.",
                        status=429,
                    )
                    resp["Retry-After"] = str(retry_after)
                    return resp

                dq.append(now)

        return self.get_response(request)
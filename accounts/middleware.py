"""Middleware that records user activity (page views and actions)."""

from django.utils.deprecation import MiddlewareMixin


# Bu on-eklerle baslayan yollar loglanmaz (gurultu: statik, admin, favicon...).
_IGNORE_PREFIXES = (
    "/static/", "/media/", "/favicon", "/admin/jsi18n",
    "/__debug__", "/health", "/robots.txt",
)
# Bu tam yollar loglanmaz (AJAX/JSON uc noktalari - cok siktir, degeri dusuk).
_IGNORE_SUFFIXES = (
    "-options-json/", "_json/", ".json", ".map",
)
# POST method -> action_type tahmini (path ipuclarina gore).
_ACTION_HINTS = {
    "delete": "DELETE",
    "update": "UPDATE",
    "edit": "UPDATE",
    "add": "CREATE",
    "create": "CREATE",
    "upload": "UPLOAD",
    "report": "REPORT",
    "managerial": "REPORT",
    "report-obs": "REPORT",
}


class ActivityLogMiddleware(MiddlewareMixin):
    """
    Logs one ActivityLog row per meaningful request from an authenticated
    user. Static files, admin internals, AJAX/JSON endpoints and anonymous
    requests are skipped to keep the log clean and cheap.
    """

    def process_response(self, request, response):
        """Record the request after the view runs, if it is loggable."""
        try:
            self._maybe_log(request, response)
        except Exception:
            # Loglama asla asil istegi bozmamali; sessizce gec.
            pass
        return response

    def _maybe_log(self, request, response):
        """Decide whether to log this request, and if so, write a row."""
        # Sadece giris yapmis kullanicilar
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return

        path = request.path or ""

        # Gurultu filtreleri
        if any(path.startswith(p) for p in _IGNORE_PREFIXES):
            return
        if any(path.endswith(s) for s in _IGNORE_SUFFIXES):
            return
        # Django admin'i loglamayalim (admin zaten kendi log'unu tutar)
        if path.startswith("/admin/"):
            return
        # Basarisiz/yonlendirme yanitlarini atla (sadece 2xx anlamli goruntuleme)
        status = getattr(response, "status_code", 200)
        if status >= 400:
            return

        method = request.method or "GET"

        # action_type belirle
        if method == "POST":
            action = "ACTION"
            low = path.lower()
            for hint, atype in _ACTION_HINTS.items():
                if hint in low:
                    action = atype
                    break
        else:
            # GET: rapor ekranlari REPORT, digerleri VIEW
            low = path.lower()
            if any(h in low for h in ("report", "managerial", "report-obs")):
                action = "REPORT" if request.GET.get("run") or request.GET.get("comp_type") else "VIEW"
            else:
                action = "VIEW"

        # Ekran adini path'ten turet (ilk-iki segment yeterli)
        screen = self._screen_name(path)

        # IP
        ip = self._client_ip(request)

        from .models import ActivityLog

        ActivityLog.objects.create(
            user=user,
            action_type=action,
            screen=screen,
            path=path[:255],
            method=method,
            ip_address=ip,
        )

    @staticmethod
    def _screen_name(path):
        """Human-ish screen label from the path (e.g. /sales/report-obs/ -> sales / report-obs)."""
        parts = [p for p in path.split("/") if p]
        if not parts:
            return "home"
        return " / ".join(parts[:2])[:120]

    @staticmethod
    def _client_ip(request):
        """Best-effort client IP (respects X-Forwarded-For behind Azure proxy)."""
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

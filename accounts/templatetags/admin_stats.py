"""Template tags that compute dashboard statistics for the admin index."""

import json
from datetime import timedelta

from django import template
from django.utils import timezone

register = template.Library()


@register.simple_tag
def solgar_admin_stats():
    """
    Return a JSON blob with dashboard stats for the admin index charts:
      - record counts (users, screens, chains, dad queries)
      - activity by day (last 14 days)
      - activity by action type
      - top active users (last 30 days)
      - logins by day (last 14 days)
    Safe to fail: if a model is missing, that section is skipped.
    """
    data = {}

    # --- Record counts ---
    counts = {}
    try:
        from accounts.models import User
        counts["users"] = User.objects.count()
    except Exception:
        pass
    try:
        from authorization.models import Screen
        counts["screens"] = Screen.objects.count()
    except Exception:
        pass
    try:
        from sales.models import ChainDefinition
        counts["chains"] = ChainDefinition.objects.count()
    except Exception:
        pass
    try:
        from sales.models import DadQuery
        counts["dad_queries"] = DadQuery.objects.count()
    except Exception:
        pass
    data["counts"] = counts

    now = timezone.now()

    # --- Activity by day (last 14 days) ---
    try:
        from accounts.models import ActivityLog
        since = now - timedelta(days=14)
        rows = ActivityLog.objects.filter(timestamp__gte=since)
        by_day = {}
        for r in rows.values_list("timestamp", flat=True):
            key = timezone.localtime(r).strftime("%d.%m")
            by_day[key] = by_day.get(key, 0) + 1
        # son 14 gunu sirala
        days = [(now - timedelta(days=i)) for i in range(13, -1, -1)]
        labels = [timezone.localtime(d).strftime("%d.%m") for d in days]
        data["activity_by_day"] = {
            "labels": labels,
            "values": [by_day.get(l, 0) for l in labels],
        }

        # --- Activity by action type ---
        by_action = {}
        for a in rows.values_list("action_type", flat=True):
            by_action[a] = by_action.get(a, 0) + 1
        data["activity_by_action"] = {
            "labels": list(by_action.keys()),
            "values": list(by_action.values()),
        }

        # --- Top active users (last 30 days) ---
        since30 = now - timedelta(days=30)
        by_user = {}
        for uname in ActivityLog.objects.filter(
            timestamp__gte=since30
        ).values_list("user__username", flat=True):
            by_user[uname] = by_user.get(uname, 0) + 1
        top = sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:8]
        data["top_users"] = {
            "labels": [t[0] for t in top],
            "values": [t[1] for t in top],
        }
    except Exception:
        pass

    # --- Logins by day (last 14 days) ---
    try:
        from accounts.models import LoginLog
        since = now - timedelta(days=14)
        rows = LoginLog.objects.filter(timestamp__gte=since)
        by_day = {}
        for r in rows.values_list("timestamp", flat=True):
            key = timezone.localtime(r).strftime("%d.%m")
            by_day[key] = by_day.get(key, 0) + 1
        days = [(now - timedelta(days=i)) for i in range(13, -1, -1)]
        labels = [timezone.localtime(d).strftime("%d.%m") for d in days]
        data["logins_by_day"] = {
            "labels": labels,
            "values": [by_day.get(l, 0) for l in labels],
        }
    except Exception:
        pass

    return json.dumps(data)

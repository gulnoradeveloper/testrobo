"""Umumiy yordamchi servislar: bildirishnoma va audit log."""
from .models import AuditLog, Notification


def notify(user, message, link=""):
    return Notification.objects.create(user=user, message=message, link=link)


def client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def audit(actor, action, obj=None, request=None, **details):
    return AuditLog.objects.create(
        actor=actor if (actor and actor.is_authenticated) else None,
        action=action,
        object_type=obj.__class__.__name__ if obj is not None else "",
        object_id=str(getattr(obj, "pk", "") or ""),
        details=details,
        ip_address=client_ip(request),
    )

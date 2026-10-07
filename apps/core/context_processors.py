def begoyim(request):
    ctx = {"SITE_NAME": "BEGOYIM", "SLOGAN": "Ayoldan ayolga — imkoniyat va ko‘mak."}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        ctx["unread_count"] = user.notifications.filter(is_read=False).count()
    return ctx

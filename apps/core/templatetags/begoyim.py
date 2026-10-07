from django import template

register = template.Library()


@register.filter
def som(value):
    """150000 -> '150 000 so‘m'"""
    try:
        return f"{int(value):,}".replace(",", " ") + " so‘m"
    except (TypeError, ValueError):
        return "—"


@register.filter
def stars(value):
    try:
        n = round(float(value))
    except (TypeError, ValueError):
        n = 0
    return "★" * n + "☆" * (5 - n)


@register.filter
def status_class(value):
    return f"st-{str(value).lower()}"


@register.filter
def get_item(d, key):
    return d.get(key) if hasattr(d, "get") else None


@register.simple_tag(takes_context=True)
def qs_replace(context, **kwargs):
    params = context["request"].GET.copy()
    for k, v in kwargs.items():
        params[k] = v
    return params.urlencode()


@register.filter
def num(value):
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return value

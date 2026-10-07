"""Xizmatlarni qidirish, filtrlash va saralash (web va API uchun umumiy)."""
from django.db.models import Case, F, IntegerField, Q, Value, When

from .models import Service

SORT_CHOICES = [
    ("recommended", "Tavsiya etilgan"),
    ("rating", "Yuqori reyting"),
    ("cheap", "Arzon"),
    ("new", "Yangi"),
]


def _int(value):
    try:
        return int(str(value).replace(" ", ""))
    except (TypeError, ValueError):
        return None


def _float(value):
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def search_services(params):
    qs = Service.objects.public().select_related("provider__profile", "category", "region", "district").prefetch_related("images")
    q = (params.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q))
    category = params.get("category")
    if category:
        qs = qs.filter(category__slug=category) if not str(category).isdigit() else qs.filter(category_id=category)
    if _int(params.get("region")):
        qs = qs.filter(region_id=_int(params.get("region")))
    if _int(params.get("district")):
        qs = qs.filter(district_id=_int(params.get("district")))
    if _int(params.get("price_min")) is not None:
        qs = qs.filter(price__gte=_int(params.get("price_min")))
    if _int(params.get("price_max")) is not None:
        qs = qs.filter(price__lte=_int(params.get("price_max")))
    if _float(params.get("min_rating")):
        qs = qs.filter(provider__profile__rating__gte=_float(params.get("min_rating")))
    if str(params.get("verified", "")).lower() in ("1", "true", "on", "yes"):
        qs = qs.filter(provider__profile__verification_status="verified")
    mode = params.get("mode")
    if mode in Service.Mode.values:
        qs = qs.filter(service_mode=mode)

    sort = params.get("sort") or "recommended"
    if sort == "rating":
        qs = qs.order_by("-provider__profile__rating", "-provider__profile__reviews_count", "-created_at")
    elif sort == "cheap":
        qs = qs.order_by(F("price").asc(nulls_last=True), "-created_at")
    elif sort == "new":
        qs = qs.order_by("-created_at")
    else:
        qs = qs.annotate(
            is_verified=Case(
                When(provider__profile__verification_status="verified", then=Value(1)),
                default=Value(0), output_field=IntegerField(),
            )
        ).order_by("-is_verified", "-provider__profile__rating", "-created_at")
    return qs

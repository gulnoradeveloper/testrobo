"""Buyurtma, sharh va statistika biznes-logikasi (web va API uchun umumiy)."""
from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.core.services import audit, notify

from .models import Order, OrderStatusHistory, Review, Service

S = Order.Status

# (joriy holat, yangi holat) -> kim bajara oladi
TRANSITIONS = {
    (S.NEW, S.ACCEPTED): "provider",
    (S.NEW, S.REJECTED): "provider",
    (S.ACCEPTED, S.IN_PROGRESS): "provider",
    (S.IN_PROGRESS, S.COMPLETED): "provider",
    (S.NEW, S.CANCELLED): "customer",
    (S.ACCEPTED, S.CANCELLED): "customer",
}

STATUS_MESSAGES = {
    S.ACCEPTED: "Buyurtmangiz qabul qilindi",
    S.REJECTED: "Buyurtmangiz rad etildi",
    S.IN_PROGRESS: "Buyurtmangiz bo‘yicha ish boshlandi",
    S.COMPLETED: "Xizmat bajarildi — iltimos, baho qoldiring",
    S.CANCELLED: "Buyurtma bekor qilindi",
}

MONTHS_UZ = ["Yan", "Fev", "Mar", "Apr", "May", "Iyun", "Iyul", "Avg", "Sen", "Okt", "Noy", "Dek"]


def create_order(customer, service, service_date, price=None, address_or_area="", comment="", request=None):
    if not customer.can_order:
        raise PermissionDenied("Buyurtma berish uchun buyurtmachi yoki xizmat ko‘rsatuvchi sifatida kiring.")
    if service.provider_id == customer.pk:
        raise ValidationError("O‘z xizmatingizga buyurtma bera olmaysiz.")
    if service.status != Service.Status.ACTIVE or not service.provider.is_active:
        raise ValidationError("Bu xizmat hozir buyurtma qabul qilmaydi.")
    if service_date < timezone.localdate():
        raise ValidationError("Sana o‘tib ketgan bo‘lmasligi kerak.")
    if price is None and service.price_type != Service.PriceType.NEGOTIABLE:
        price = service.price
    with transaction.atomic():
        order = Order.objects.create(
            customer=customer, provider=service.provider, service=service, price=price,
            service_date=service_date, address_or_area=address_or_area, comment=comment,
        )
        OrderStatusHistory.objects.create(order=order, to_status=S.NEW, changed_by=customer)
    notify(service.provider, f"Yangi buyurtma keldi: {service.title}", order.get_absolute_url())
    audit(customer, "order.create", order, request)
    return order


def allowed_transitions(order, user):
    result = []
    for (src, dst), who in TRANSITIONS.items():
        if src != order.status:
            continue
        if who == "provider" and user.pk == order.provider_id:
            result.append(dst)
        elif who == "customer" and user.pk == order.customer_id:
            result.append(dst)
    return result


def change_order_status(order, user, new_status, request=None):
    if new_status not in allowed_transitions(order, user):
        raise PermissionDenied("Bu holatga o‘tkazishga ruxsat yo‘q.")
    old = order.status
    now = timezone.now()
    with transaction.atomic():
        order.status = new_status
        fields = ["status", "updated_at"]
        if new_status == S.IN_PROGRESS:
            order.started_at = now  # BEGOYIM Safe: "Ishni boshladim" vaqti
            fields.append("started_at")
        if new_status == S.COMPLETED:
            order.completed_at = now  # BEGOYIM Safe: "Ishni yakunladim" vaqti
            fields.append("completed_at")
        order.save(update_fields=fields)
        OrderStatusHistory.objects.create(order=order, from_status=old, to_status=new_status, changed_by=user)
    recipient = order.customer if user.pk == order.provider_id else order.provider
    notify(recipient, f"{STATUS_MESSAGES[new_status]}: {order.service.title}", order.get_absolute_url())
    audit(user, "order.status", order, request, from_status=old, to_status=new_status)
    return order


def recalc_provider_rating(provider):
    agg = Review.objects.filter(provider=provider, is_hidden=False).aggregate(avg=Avg("rating"), n=Count("id"))
    profile = provider.profile
    profile.rating = round(agg["avg"] or 0, 2)
    profile.reviews_count = agg["n"]
    profile.save(update_fields=["rating", "reviews_count"])


def create_review(order, user, rating, quality, communication, punctuality, comment="", request=None):
    if user.pk != order.customer_id:
        raise PermissionDenied("Faqat buyurtmachi baho bera oladi.")
    if order.status != S.COMPLETED:
        raise ValidationError("Faqat bajarilgan buyurtmaga baho berish mumkin.")
    if Review.objects.filter(order=order).exists():
        raise ValidationError("Bu buyurtmaga baho allaqachon berilgan.")
    for v in (rating, quality, communication, punctuality):
        if not (1 <= int(v) <= 5):
            raise ValidationError("Baho 1 dan 5 gacha bo‘lishi kerak.")
    with transaction.atomic():
        review = Review.objects.create(
            order=order, customer=user, provider=order.provider, rating=rating, quality_rating=quality,
            communication_rating=communication, punctuality_rating=punctuality, comment=comment,
        )
        recalc_provider_rating(order.provider)
    notify(order.provider, f"Sizga yangi baho berildi: {rating}★", order.get_absolute_url())
    audit(user, "review.create", review, request)
    return review


def _shift_month(d, delta):
    m = d.month - 1 + delta
    return date(d.year + m // 12, m % 12 + 1, 1)


def monthly_series(qs, date_field, value_expr=None, months=6):
    """Oxirgi N oy uchun [(label, value)] ro'yxati."""
    today = timezone.localdate()
    start = _shift_month(today.replace(day=1), -(months - 1))
    agg = value_expr if value_expr is not None else Count("id")
    rows = (
        qs.filter(**{f"{date_field}__date__gte": start})
        .annotate(m=TruncMonth(date_field))
        .values("m")
        .annotate(v=agg)
    )
    by_month = {}
    for r in rows:
        m = r["m"]
        if hasattr(m, "date"):
            m = timezone.localtime(m).date() if timezone.is_aware(m) else m.date()
        by_month[(m.year, m.month)] = r["v"] or 0
    series = []
    for i in range(months):
        d = _shift_month(start, i)
        series.append({"label": MONTHS_UZ[d.month - 1], "value": by_month.get((d.year, d.month), 0)})
    peak = max([s["value"] for s in series] + [1])
    for s in series:
        s["pct"] = round(100 * s["value"] / peak)
    return series


def provider_dashboard(provider):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    orders = Order.objects.filter(provider=provider)
    month_orders = orders.filter(created_at__date__gte=month_start)
    completed = orders.filter(status=S.COMPLETED)
    month_completed = completed.filter(completed_at__date__gte=month_start)
    return {
        "month_orders": month_orders.count(),
        "month_completed": month_completed.count(),
        "month_income": month_completed.aggregate(s=Sum("price"))["s"] or 0,
        "total_income": completed.aggregate(s=Sum("price"))["s"] or 0,
        "total_completed": completed.count(),
        "new_orders": orders.filter(status=S.NEW).count(),
        "active_orders": orders.filter(status__in=[S.ACCEPTED, S.IN_PROGRESS]).count(),
        "rating": provider.profile.rating,
        "reviews_count": provider.profile.reviews_count,
        "income_series": monthly_series(completed, "completed_at", Sum("price")),
        "orders_series": monthly_series(orders, "created_at"),
    }


def mahalla_dashboard(mahalla):
    """Faqat agregat ko'rsatkichlar — shaxsiy yoki psixologik ma'lumot yo'q."""
    from apps.accounts.models import Profile, User

    users = User.objects.filter(profile__mahalla=mahalla, is_active=True)
    providers = users.filter(role=User.Role.PROVIDER)
    services = Service.objects.public().filter(provider__profile__mahalla=mahalla)
    orders = Order.objects.filter(provider__profile__mahalla=mahalla)
    completed = orders.filter(status=S.COMPLETED)
    top = (
        orders.values("service__category__name", "service__category__icon")
        .annotate(n=Count("id"))
        .order_by("-n")[:5]
    )
    return {
        "users": users.count(),
        "providers": providers.count(),
        "verified": providers.filter(profile__verification_status=Profile.Verification.VERIFIED).count(),
        "active_services": services.count(),
        "active_providers": providers.filter(services__in=services).distinct().count(),
        "women_with_orders": providers.filter(orders_received__isnull=False).distinct().count(),
        "completed_orders": completed.count(),
        "pending_verifications": mahalla.verification_requests.filter(status="pending").count(),
        "top_categories": list(top),
        "orders_series": monthly_series(orders, "created_at"),
    }


def admin_dashboard():
    from apps.accounts.models import User, VerificationRequest
    from apps.core.models import Report
    from apps.psychology.models import Psychologist

    by_role = dict(User.objects.values_list("role").annotate(n=Count("id")))
    orders = Order.objects.all()
    return {
        "users_total": User.objects.count(),
        "by_role": {label: by_role.get(value, 0) for value, label in User.Role.choices},
        "services_active": Service.objects.filter(status=Service.Status.ACTIVE).count(),
        "services_blocked": Service.objects.filter(status=Service.Status.BLOCKED).count(),
        "orders_total": orders.count(),
        "orders_by_status": {label: orders.filter(status=value).count() for value, label in S.choices},
        "income_total": orders.filter(status=S.COMPLETED).aggregate(s=Sum("price"))["s"] or 0,
        "verifications_pending": VerificationRequest.objects.filter(status="pending").count(),
        "reports_open": Report.objects.filter(~Q(status=Report.Status.RESOLVED)).count(),
        "psychologists": Psychologist.objects.filter(is_approved=True).count(),
        "psychologists_pending": Psychologist.objects.filter(is_approved=False).count(),
        "orders_series": monthly_series(orders, "created_at"),
    }

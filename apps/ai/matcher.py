"""AI Smart Matching — tushuntiriladigan reyting.

MatchScore = xizmat mosligi (40) + hudud mosligi (25) + reyting (15)
           + verifikatsiya (10) + mavjudlik (10)  -> 0..100 %

Faqat bazada mavjud, faol xizmatlar qaytariladi: AI topmagan xizmatni
"mavjud" deb yaratmaydi. Natija — tavsiya, qaror emas.
"""
from dataclasses import dataclass, field

from django.db.models import Count, Q

from apps.catalog.models import Order, Service

from .parser import normalize, parse_query

W_SERVICE, W_REGION, W_RATING, W_VERIFIED, W_AVAILABLE = 40, 25, 15, 10, 10
BUSY_THRESHOLD = 3


@dataclass
class Match:
    service: Service
    score: int
    breakdown: dict
    reasons: list = field(default_factory=list)

    def as_dict(self):
        p = self.service.provider.profile
        return {
            "service_id": self.service.pk,
            "title": self.service.title,
            "provider": self.service.provider.display_name,
            "provider_id": self.service.provider_id,
            "category": self.service.category.name,
            "price": self.service.price_label,
            "location": f"{self.service.district.name}, {self.service.region.name}",
            "rating": float(p.rating),
            "verified": p.is_verified,
            "score": self.score,
            "breakdown": self.breakdown,
            "reasons": self.reasons,
        }


def _text_overlap(service, tokens):
    hay = normalize(f"{service.title} {service.description}")
    hits = [t for t in tokens if t[:5] in hay]
    return hits


def smart_match(text, limit=5, user=None):
    parsed = parse_query(text)
    result = {"parsed": parsed.as_dict(), "matches": [], "message": ""}
    if not normalize(text):
        result["message"] = "So‘rov matnini kiriting."
        return result

    qs = Service.objects.public().select_related("provider__profile", "category", "region", "district")
    if user is not None and user.is_authenticated:
        qs = qs.exclude(provider=user)
    if parsed.category is not None:
        candidates = qs.filter(category=parsed.category)
    else:
        # Kategoriya aniqlanmadi — matndagi so'zlar bo'yicha qidiramiz
        token_q = Q()
        for t in parsed.tokens:
            token_q |= Q(title__icontains=t[:5]) | Q(description__icontains=t[:5])
        candidates = qs.filter(token_q) if parsed.tokens else qs.none()

    candidates = candidates.annotate(
        active_orders=Count("provider__orders_received", filter=Q(provider__orders_received__status__in=Order.ACTIVE_STATUSES), distinct=True)
    )

    matches = []
    for s in candidates[:200]:
        profile = s.provider.profile
        reasons, b = [], {}

        # 1. Xizmat mosligi
        if parsed.category is not None:
            overlap = _text_overlap(s, parsed.category_keywords)
            b["xizmat"] = W_SERVICE if overlap or len(parsed.category_keywords) <= 1 else int(W_SERVICE * 0.85)
            reasons.append(f"Kategoriya mos: {s.category.name}")
        else:
            overlap = _text_overlap(s, parsed.tokens)
            if not overlap:
                continue
            b["xizmat"] = min(W_SERVICE, 15 + 8 * len(overlap))
            reasons.append("Tavsifda so‘rovdagi so‘zlar bor")

        # 2. Hudud mosligi
        if s.service_mode == Service.Mode.REMOTE:
            b["hudud"] = W_REGION
            reasons.append("Masofadan xizmat — hudud cheklovi yo‘q")
        elif parsed.district is not None:
            if s.district_id == parsed.district.pk:
                b["hudud"] = W_REGION
                reasons.append(f"Hudud mos: {s.district.name}")
            elif s.region_id == parsed.region.pk:
                b["hudud"] = int(W_REGION * 0.6)
                reasons.append(f"Viloyat mos: {s.region.name}")
            else:
                b["hudud"] = 0
                reasons.append(f"Boshqa hudud: {s.district.name}")
        elif parsed.region is not None:
            b["hudud"] = W_REGION if s.region_id == parsed.region.pk else 0
            reasons.append(f"Viloyat mos: {s.region.name}" if b["hudud"] else f"Boshqa hudud: {s.region.name}")
        else:
            b["hudud"] = int(W_REGION * 0.5)  # hudud ko'rsatilmagan — neytral

        # 3. Reyting (sharh bo'lmasa neytral qiymat)
        if profile.reviews_count:
            b["reyting"] = round(W_RATING * float(profile.rating) / 5)
            reasons.append(f"Reyting: {float(profile.rating):.1f} ★ ({profile.reviews_count} ta sharh)")
        else:
            b["reyting"] = round(W_RATING * 0.5)

        # 4. Verifikatsiya
        b["verifikatsiya"] = W_VERIFIED if profile.is_verified else 0
        if profile.is_verified:
            reasons.append("✓ Mahalla tomonidan tasdiqlangan")

        # 5. Mavjudlik
        busy_on_date = parsed.when and s.provider.orders_received.filter(
            service_date=parsed.when, status__in=Order.ACTIVE_STATUSES
        ).exists()
        if busy_on_date:
            b["mavjudlik"] = 0
            reasons.append(f"{parsed.when_label} kuni band bo‘lishi mumkin")
        elif s.active_orders >= BUSY_THRESHOLD:
            b["mavjudlik"] = W_AVAILABLE // 2
        else:
            b["mavjudlik"] = W_AVAILABLE

        if parsed.mode and s.service_mode == parsed.mode:
            reasons.append(f"Xizmat shakli mos: {s.get_service_mode_display()}")

        matches.append(Match(service=s, score=min(100, sum(b.values())), breakdown=b, reasons=reasons))

    matches.sort(key=lambda m: (-m.score, -float(m.service.provider.profile.rating), -m.service.pk))
    result["matches"] = matches[:limit]
    if not matches:
        result["message"] = (
            "Afsuski, so‘rovingizga mos xizmat hozircha platformada topilmadi. "
            "Kategoriya yoki hududni o‘zgartirib qidirib ko‘ring."
        )
    return result

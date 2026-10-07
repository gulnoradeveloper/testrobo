"""Tabiiy tildagi so'rovni tahlil qilish (intent / parametrlar).

MVP uchun mahalliy, tushuntiriladigan qoidaviy tahlil ishlatiladi: kategoriya
kalit so'zlari (admin paneldan tahrirlanadi), hudud nomlari bazadan olinadi,
vaqt ifodalari esa oddiy lug'at orqali aniqlanadi. Natija faqat tavsiya —
AI hech qanday qaror qabul qilmaydi.
"""
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from django.utils import timezone

APOSTROPHES = "'‘’ʻʼ`´"
_strip_re = re.compile(f"[{re.escape(APOSTROPHES)}]")

WEEKDAYS = {
    "dushanba": 0, "seshanba": 1, "chorshanba": 2, "payshanba": 3, "juma": 4, "shanba": 5, "yakshanba": 6,
}

MODE_HINTS = {
    "remote": ["masofa", "onlayn", "online", "internet orqali", "zoom", "telegram orqali"],
    "client_address": ["uyimga", "uyimizga", "manzilga", "kelib", "uyga kelib", "xonani", "xonalarni"],
}


def normalize(text):
    text = _strip_re.sub("", (text or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def _stem(name):
    """'Buxoro viloyati' -> 'buxoro', 'Buxoro shahri' -> 'buxoro'."""
    words = normalize(name).replace("shahri", "").replace("viloyati", "").replace("tumani", "").split()
    return " ".join(words).strip()


def _has(text, needle):
    return bool(needle) and re.search(r"(?<![a-z0-9])" + re.escape(needle), text) is not None


@dataclass
class ParsedQuery:
    text: str
    category: object = None
    category_keywords: list = field(default_factory=list)
    region: object = None
    district: object = None
    when: date = None
    when_label: str = ""
    mode: str = ""
    tokens: list = field(default_factory=list)

    def as_dict(self):
        return {
            "xizmat": self.category.name if self.category else None,
            "kalit_sozlar": self.category_keywords,
            "hudud": (self.district.name if self.district else (self.region.name if self.region else None)),
            "viloyat_id": self.region.pk if self.region else None,
            "tuman_id": self.district.pk if self.district else None,
            "vaqt": self.when_label or None,
            "sana": self.when.isoformat() if self.when else None,
            "shakl": {"remote": "masofadan", "client_address": "mijoz manzilida"}.get(self.mode),
        }


def _detect_when(text):
    today = timezone.localdate()
    if _has(text, "bugun"):
        return today, "bugun"
    if _has(text, "indinga"):
        return today + timedelta(days=2), "indinga"
    if _has(text, "ertaga") or _has(text, "ertangi"):
        return today + timedelta(days=1), "ertaga"
    if _has(text, "hafta oxiri") or _has(text, "dam olish"):
        days = (5 - today.weekday()) % 7 or 7
        return today + timedelta(days=days), "hafta oxiri"
    for name, wd in WEEKDAYS.items():
        if _has(text, name):
            days = (wd - today.weekday()) % 7 or 7
            return today + timedelta(days=days), name
    m = re.search(r"\b(\d{1,2})[./](\d{1,2})\b", text)
    if m:
        try:
            d = date(today.year, int(m.group(2)), int(m.group(1)))
            if d < today:
                d = date(today.year + 1, d.month, d.day)
            return d, d.strftime("%d.%m.%Y")
        except ValueError:
            pass
    return None, ""


def parse_query(text):
    from apps.catalog.models import Category
    from apps.core.models import District, Region

    norm = normalize(text)
    parsed = ParsedQuery(text=text, tokens=[t for t in re.findall(r"[a-z0-9]+", norm) if len(t) > 2])

    best, best_hits = None, []
    for cat in Category.objects.filter(is_active=True):
        hits = [k for k in (normalize(k) for k in cat.keyword_list()) if _has(norm, k)]
        if _has(norm, normalize(cat.name)):
            hits.append(normalize(cat.name))
        # Uzunroq (aniqroq) kalit so'z ko'proq vazn oladi: "parda tik" > "tik"
        if hits and (best is None or sum(map(len, hits)) > sum(map(len, best_hits))):
            best, best_hits = cat, hits
    parsed.category, parsed.category_keywords = best, best_hits

    says_city = "shahr" in norm or "shahar" in norm
    says_district = "tuman" in norm
    candidates = [d for d in District.objects.select_related("region") if _stem(d.name) and _has(norm, _stem(d.name))]
    if candidates:
        def pick(d):
            # "Buxoro shahrida" -> "Buxoro shahri"; "Buxoro tumanida" -> "Buxoro tumani"
            name = normalize(d.name)
            return (says_city and "shahri" in name) * 2 + (says_district and "tumani" in name) * 2 + len(name) / 100

        district = max(candidates, key=pick)
        parsed.region = district.region
        ambiguous = _stem(district.name) == _stem(district.region.name) and not (says_city or says_district)
        parsed.district = None if ambiguous else district
    else:
        for region in Region.objects.all():
            if _has(norm, _stem(region.name)):
                parsed.region = region
                break

    parsed.when, parsed.when_label = _detect_when(norm)
    for mode, hints in MODE_HINTS.items():
        if any(_has(norm, h) for h in hints):
            parsed.mode = mode
            break
    return parsed

"""Ma'lumotnomalar va demo ma'lumotlarni yuklash.

    python manage.py seed_demo                  # ma'lumotnomalar + demo foydalanuvchilar
    python manage.py seed_demo --reference-only # faqat hududlar, kategoriyalar, ko'nikmalar

Demo ma'lumotlar faqat taqdimot uchun; production'da --reference-only ishlating.
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Profile, Skill, User, UserSkill, VerificationRequest
from apps.catalog.models import Category, Order, OrderStatusHistory, Review, Service
from apps.catalog.services import recalc_provider_rating
from apps.core.models import District, Mahalla, Region
from apps.core.reference_data import CATEGORIES, REGIONS, SKILLS
from apps.psychology.models import Psychologist, PsychologistSchedule

DEMO_PASSWORD = "Begoyim2026!"


def load_reference():
    for region_name, districts in REGIONS.items():
        region, _ = Region.objects.get_or_create(name=region_name)
        for district_name, mahallas in districts.items():
            district, _ = District.objects.get_or_create(region=region, name=district_name)
            for m in mahallas:
                Mahalla.objects.get_or_create(district=district, name=f"{m} MFY")
    for i, (name, slug, icon, keywords) in enumerate(CATEGORIES):
        Category.objects.update_or_create(slug=slug, defaults={"name": name, "icon": icon, "keywords": keywords, "order": i})
    for slug, names in SKILLS.items():
        cat = Category.objects.get(slug=slug)
        for n in names:
            Skill.objects.get_or_create(name=n, defaults={"category": cat})


def mahalla(district, name):
    return Mahalla.objects.get(district__name=district, name=f"{name} MFY")


def make_user(phone, role, first, last, mahalla_obj=None, verified=False, **profile_extra):
    user, created = User.objects.get_or_create(phone=phone, defaults={"role": role})
    if created:
        user.set_password(DEMO_PASSWORD)
        user.save()
    p, _ = Profile.objects.get_or_create(user=user)
    p.first_name, p.last_name = first, last
    if mahalla_obj:
        p.mahalla, p.district, p.region = mahalla_obj, mahalla_obj.district, mahalla_obj.district.region
    if verified:
        p.verification_status = Profile.Verification.VERIFIED
    for k, v in profile_extra.items():
        setattr(p, k, v)
    p.save()
    return user


PROVIDERS = [
    # phone, ism, familiya, (tuman, mahalla), verified, ko'nikmalar, bio, xizmatlar[(kategoriya, nom, narx, narx turi, shakl, muddat, tavsif)]
    ("+998901000001", "Dilnoza", "Rahimova", ("Buxoro shahri", "Navbahor"), True, ["Uy tozalash", "Dazmollash"],
     "8 yillik tajriba. Ozodalik va tartib — mening ishim.",
     [("uy-tozalash", "Uy va xonalarni tozalash", 150000, "from", "client_address", "1 kun",
       "Xonalarni, oshxona va hammomni puxta tozalayman. O‘z vositalarim bilan kelaman.")]),
    ("+998901000002", "Mohira", "Saidova", ("Buxoro shahri", "Mustaqillik"), True, ["Uy tozalash", "Gilam yuvish"],
     "Uy tozalash va gilam yuvish bo‘yicha 5 yillik tajriba.",
     [("uy-tozalash", "Umumiy uy tozalash (bayramoldi)", 120000, "from", "client_address", "1 kun",
       "Bayram oldidan umumiy tozalash, derazalarni yuvish, gilamlarni changdan tozalash.")]),
    ("+998901000003", "Gulchehra", "Nazarova", ("Buxoro shahri", "Ko‘hna shahar"), True, ["Milliy taomlar", "Somsa tayyorlash"],
     "Uy sharoitida milliy taomlar va somsa tayyorlayman.",
     [("pazandachilik", "Uy sharoitida milliy somsa tayyorlash", 80000, "from", "at_home", "1 kun",
       "Tandir somsa, qovoq somsa va go‘shtli somsa. 20 donadan buyurtma qabul qilaman."),
      ("pishiriqlar", "Buyurtma asosida tort pishirish", 250000, "from", "at_home", "2 kun",
       "Tug‘ilgan kun va bayramlar uchun uy tortlari.")]),
    ("+998901000004", "Feruza", "Qodirova", ("G‘ijduvon tumani", "Sohibkor"), False, ["Kashtachilik", "Zardo‘zlik"],
     "G‘ijduvon kashtachilik maktabi an’analarini davom ettiraman.",
     [("hunarmandchilik", "Qo‘lda kashta (suzana) tikish", None, "negotiable", "at_home", "2–4 hafta",
       "Buyurtma asosida suzana, so‘zana va kashta bezaklari.")]),
    ("+998901000005", "Zarina", "Yusupova", ("Chilonzor tumani", "Qatortol"), True, ["Milliy taomlar", "To‘y oshi"],
     "Toshkentda to‘y-marosimlar uchun taom tayyorlayman.",
     [("pazandachilik", "Marosimlar uchun palov va somsa", 500000, "from", "client_address", "1 kun",
       "50 kishidan ortiq marosimlar uchun palov, somsa va salatlar.")]),
    ("+998901000006", "Shahnoza", "Ergasheva", ("Samarqand shahri", "Registon"), True, ["Chopon tikish", "Atlas-adras bilan ishlash"],
     "Milliy kiyim va kelin sarpolari tikaman.",
     [("milliy-kiyim", "Atlas va adrasdan milliy ko‘ylak tikish", 400000, "from", "at_home", "5–7 kun",
       "O‘lcham bo‘yicha milliy ko‘ylak, kamzul va chopon.")]),
    ("+998901000007", "Madina", "Tursunova", ("Yunusobod tumani", "Minor"), True, ["Ingliz tili"],
     "IELTS 8.0. Bolalar va kattalar uchun ingliz tili.",
     [("repetitorlik", "Masofadan ingliz tili darslari", 100000, "fixed", "remote", "60 daqiqa",
       "Onlayn darslar: grammatika, so‘zlashuv, IELTS tayyorlov.")]),
    ("+998901000008", "Nilufar", "Karimova", ("Mirzo Ulug‘bek tumani", "Qorasuv"), False, ["Soch turmaklash", "Makiyaj"],
     "To‘y va bayramlar uchun pardoz.",
     [("gozallik", "Kelin pardozi va soch turmaklash", 300000, "from", "client_address", "3 soat",
       "Mijoz manziliga borib pardoz va soch turmaklash.")]),
    ("+998901000009", "Sabina", "Hamroyeva", ("Kogon shahri", "Do‘stlik"), True, ["Parda tikish", "Parda o‘rnatish"],
     "12 yildan beri parda tikaman.",
     [("parda-tikish", "Zamonaviy parda tikish va o‘rnatish", 200000, "from", "client_address", "3–5 kun",
       "O‘lchov olish, mato tanlashda yordam, parda tikish va o‘rnatish.")]),
    ("+998901000010", "Barno", "Usmonova", ("Buxoro shahri", "Bahoriston"), True, ["Enagalik", "Maktabgacha tarbiya"],
     "Pedagog-tarbiyachi, 9 yillik bog‘cha tajribasi.",
     [("bolalarga-qarash", "Bolalarga qarash (enagalik) — kunlik yoki soatbay", 50000, "from", "client_address", "soatbay",
       "1–6 yoshli bolalarga mehr bilan qarayman: o‘yinlar, ovqatlantirish, rivojlantiruvchi mashg‘ulotlar.")]),
]

CUSTOMERS = [
    ("+998902000001", "Sevara", "Aminova", ("Buxoro shahri", "Bahoriston")),
    ("+998902000002", "Kamola", "Rashidova", ("Chilonzor tumani", "Lutfiy")),
    ("+998902000003", "Dildora", "Xolova", ("Buxoro shahri", "Navbahor")),
]

COMMENTS = [
    "Juda puxta va o‘z vaqtida bajardi, rahmat!", "Muomalasi a’lo, yana murojaat qilaman.",
    "Sifat zo‘r, narxi ham hamyonbop.", "Tavsiya qilaman!", "Hammasi kelishilgandek bo‘ldi.",
]


class Command(BaseCommand):
    help = "Hududlar, kategoriyalar va (ixtiyoriy) demo ma'lumotlarni yuklaydi"

    def add_arguments(self, parser):
        parser.add_argument("--reference-only", action="store_true")

    @transaction.atomic
    def handle(self, *args, **opts):
        load_reference()
        self.stdout.write(self.style.SUCCESS("Ma’lumotnomalar yuklandi."))
        if opts["reference_only"]:
            return
        rng = random.Random(42)

        admin = make_user("+998900000001", User.Role.ADMIN, "Tizim", "Administratori")
        admin.is_staff = admin.is_superuser = True
        admin.save()
        make_user("+998900000002", User.Role.MAHALLA, "Saodat", "Islomova (Navbahor MFY)", mahalla("Buxoro shahri", "Navbahor"))
        make_user("+998900000003", User.Role.MAHALLA, "Muhabbat", "Aliyeva (Qatortol MFY)", mahalla("Chilonzor tumani", "Qatortol"))

        for phone, first, last, spec, years, fmt, about in [
            ("+998900000004", "Nodira", "Karimova", "Oilaviy psixologiya, stress va xavotir", 12, "both",
             "Klinik psixolog. Oilaviy munosabatlar, ona va bola psixologiyasi."),
            ("+998900000005", "Malika", "Sobirova", "Ayollar psixologiyasi, o‘zini anglash", 7, "online",
             "Onlayn konsultatsiyalar. Ishga qaytish va o‘ziga ishonchni tiklash."),
        ]:
            u = make_user(phone, User.Role.PSYCHOLOGIST, first, last, mahalla("Buxoro shahri", "Mustaqillik"))
            p, _ = Psychologist.objects.update_or_create(user=u, defaults={
                "specialization": spec, "experience_years": years, "consultation_format": fmt, "about": about,
                "office_address": "Buxoro sh., M. Iqbol ko‘chasi, 12" if fmt != "online" else "", "is_approved": True,
            })
            if not p.slots.exists():
                base = timezone.localtime().replace(hour=10, minute=0, second=0, microsecond=0)
                for day in range(1, 8):
                    for hour in (10, 14, 16):
                        start = base + timedelta(days=day, hours=hour - 10)
                        PsychologistSchedule.objects.create(psychologist=p, start_at=start, end_at=start + timedelta(minutes=50))

        providers = []
        for phone, first, last, (district, mah), verified, skills, bio, services in PROVIDERS:
            m = mahalla(district, mah)
            u = make_user(phone, User.Role.PROVIDER, first, last, m, verified, bio=bio,
                          experience=bio, age_range=rng.choice(["25-34", "35-44", "45-54"]))
            for sk in skills:
                UserSkill.objects.get_or_create(user=u, skill=Skill.objects.get(name=sk))
            if verified and not u.verification_requests.exists():
                VerificationRequest.objects.create(user=u, mahalla=m, status="approved", decided_at=timezone.now())
            for cat, title, price, ptype, mode, dur, desc in services:
                Service.objects.get_or_create(provider=u, title=title, defaults={
                    "category": Category.objects.get(slug=cat), "description": desc, "price": price, "price_type": ptype,
                    "service_mode": mode, "region": m.district.region, "district": m.district, "duration": dur,
                })
            providers.append(u)

        customers = [make_user(ph, User.Role.CUSTOMER, f, l, mahalla(d, mh)) for ph, f, l, (d, mh) in CUSTOMERS]

        if not Order.objects.exists():
            now = timezone.now()
            for prov in providers:
                for svc in prov.services.all():
                    for i in range(rng.randint(3, 7)):
                        # birinchi buyurtma joriy oyda — "Bu oy" dashboardi bo'sh bo'lmasligi uchun
                        days_ago = rng.randint(min(2, timezone.localdate().day - 1), max(2, timezone.localdate().day - 1)) if i == 0 else rng.randint(3, 170)
                        created = now - timedelta(days=days_ago, hours=6)
                        customer = rng.choice(customers)
                        price = svc.price or rng.choice([150000, 250000, 400000])
                        o = Order.objects.create(customer=customer, provider=prov, service=svc, price=price,
                                                 service_date=(created + timedelta(days=1)).date(),
                                                 address_or_area=svc.district.name, status=Order.Status.COMPLETED,
                                                 started_at=min(created + timedelta(days=1), now),
                                                 completed_at=min(created + timedelta(days=1, hours=4), now))
                        Order.objects.filter(pk=o.pk).update(created_at=created)
                        for a, b in [("", "NEW"), ("NEW", "ACCEPTED"), ("ACCEPTED", "IN_PROGRESS"), ("IN_PROGRESS", "COMPLETED")]:
                            OrderStatusHistory.objects.create(order=o, from_status=a, to_status=b, changed_by=prov)
                        r = rng.choice([5, 5, 5, 4, 5, 4])
                        rv = Review.objects.create(order=o, customer=customer, provider=prov, rating=r, quality_rating=r,
                                              communication_rating=rng.choice([4, 5]), punctuality_rating=rng.choice([4, 5]),
                                              comment=rng.choice(COMMENTS))
                        Review.objects.filter(pk=rv.pk).update(created_at=o.completed_at)
                recalc_provider_rating(prov)

        self.stdout.write(self.style.SUCCESS("Demo ma’lumotlar yuklandi. Barcha demo parollar: " + DEMO_PASSWORD))

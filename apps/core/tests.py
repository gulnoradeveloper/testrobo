"""MVP Acceptance Criteria (TT, 26-bo'lim) — 15 bosqichli jonli demo ssenariysi
hamda xavfsizlik/maxfiylik talablari bo'yicha testlar."""
import io
import shutil
import tempfile
from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from apps.accounts.models import Profile, User, VerificationRequest
from apps.catalog.models import Category, Order, Review, Service
from apps.core.models import AuditLog, District, Mahalla, Notification, Region
from apps.psychology.models import Consultation, Psychologist

PASSWORD = "Begoyim2026!"
MEDIA = tempfile.mkdtemp()


def png_bytes(name="p.png"):
    buf = io.BytesIO()
    Image.new("RGB", (20, 20), "red").save(buf, "PNG")
    buf.seek(0)
    buf.name = name
    return buf


@override_settings(MEDIA_ROOT=MEDIA)
class AcceptanceScenarioTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=io.StringIO())

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def login(self, phone):
        self.client.logout()
        r = self.client.post(reverse("accounts:login"), {"phone": phone, "password": PASSWORD})
        self.assertEqual(r.status_code, 302, f"login failed for {phone}")

    def test_full_mvp_scenario(self):
        c = self.client
        mahalla = Mahalla.objects.get(name="Navbahor MFY")
        district = mahalla.district
        region = district.region
        before = self._mahalla_stats()
        c.logout()

        # 1. Yangi ayol ro'yxatdan o'tadi
        r = c.post(reverse("accounts:register"), {
            "phone": "+998 93 555 44 33", "password1": PASSWORD, "password2": PASSWORD, "role": "provider",
        })
        self.assertRedirects(r, reverse("accounts:profile_edit"))
        aziza = User.objects.get(phone="+998935554433")
        self.assertTrue(aziza.check_password(PASSWORD))
        self.assertNotEqual(aziza.password, PASSWORD)  # parol ochiq saqlanmaydi

        # 2-3. Profilini to'ldiradi va ko'nikmasini belgilaydi
        from apps.accounts.models import Skill
        skill = Skill.objects.get(name="Parda tikish")
        r = c.post(reverse("accounts:profile_edit"), {
            "first_name": "Aziza", "last_name": "Olimova", "age_range": "35-44",
            "region": region.pk, "district": district.pk, "mahalla": mahalla.pk,
            "bio": "Parda tikuvchi", "experience": "10 yil", "skills": [skill.pk],
            "portfolio": [png_bytes()],
        })
        self.assertRedirects(r, reverse("accounts:profile"))
        aziza.refresh_from_db()
        self.assertTrue(aziza.profile.is_complete)
        self.assertTrue(aziza.user_skills.filter(skill=skill).exists())
        self.assertEqual(aziza.portfolio.count(), 1)

        # 4. Mahalla verifikatsiyasiga yuboradi
        c.post(reverse("accounts:verification_submit"), {"note": "Iltimos tasdiqlang"})
        aziza.profile.refresh_from_db()
        self.assertEqual(aziza.profile.verification_status, Profile.Verification.PENDING)
        vr = VerificationRequest.objects.get(user=aziza)

        # 5. Mahalla vakili tasdiqlaydi
        self.login("+998900000002")
        r = c.get(reverse("accounts:mahalla_verifications"))
        self.assertContains(r, "Aziza Olimova")
        r = c.post(reverse("accounts:mahalla_verification_detail", args=[vr.pk]), {"decision": "approve", "comment": ""})
        self.assertEqual(r.status_code, 302)
        aziza.profile.refresh_from_db()
        self.assertTrue(aziza.profile.is_verified)
        self.assertTrue(Notification.objects.filter(user=aziza, message__icontains="tasdiqlandi").exists())

        # 6. Ayol "Parda tikish" xizmatini yaratadi
        self.login("+998935554433")
        parda = Category.objects.get(slug="parda-tikish")
        r = c.post(reverse("catalog:service_create"), {
            "title": "Parda tikish — Buxoro", "category": parda.pk, "description": "Har xil parda tikaman",
            "price_type": "from", "price": 180000, "service_mode": "client_address",
            "region": region.pk, "district": district.pk, "duration": "3 kun", "status_choice": "active",
            "images": [png_bytes("a.png")],
        })
        service = Service.objects.get(title="Parda tikish — Buxoro")
        self.assertRedirects(r, service.get_absolute_url())
        self.assertEqual(service.images.count(), 1)
        r = c.get(reverse("accounts:profile"))
        self.assertContains(r, "Mahalla tomonidan tasdiqlangan")

        # 7. Ikkinchi foydalanuvchi xizmatni qidiradi
        self.login("+998902000001")
        r = c.get(reverse("catalog:service_list"), {"q": "parda", "region": region.pk, "verified": "on"})
        self.assertContains(r, "Parda tikish — Buxoro")

        # 8. AI Smart Matching xizmatni mos natijalar qatorida chiqaradi
        r = c.get(reverse("catalog:smart_match"), {"text": "Ertaga Buxoro shahrida parda tikib beradigan ayol kerak"})
        matches = r.context["result"]["matches"]
        self.assertIn(service.pk, [m.service.pk for m in matches])
        top = next(m for m in matches if m.service.pk == service.pk)
        self.assertGreaterEqual(top.score, 80)
        self.assertEqual(r.context["result"]["parsed"]["vaqt"], "ertaga")

        # 9. Buyurtmachi buyurtma beradi
        tomorrow = timezone.localdate() + timedelta(days=1)
        r = c.post(reverse("catalog:order_create", args=[service.pk]), {
            "service_date": tomorrow.isoformat(), "price": 180000, "address_or_area": "Navbahor MFY", "comment": "2 xona",
        })
        order = Order.objects.get(service=service)
        self.assertRedirects(r, order.get_absolute_url())
        self.assertEqual(order.status, Order.Status.NEW)
        self.assertTrue(Notification.objects.filter(user=aziza, message__startswith="Yangi buyurtma keldi").exists())

        # Baho faqat COMPLETED holatida
        r = c.post(reverse("catalog:review_create", args=[order.pk]), self._review())
        self.assertFalse(Review.objects.filter(order=order).exists())

        # 10-12. Ijrochi qabul qiladi -> IN_PROGRESS -> COMPLETED (BEGOYIM Safe vaqtlari)
        self.login("+998935554433")
        for st in ("ACCEPTED", "IN_PROGRESS", "COMPLETED"):
            c.post(reverse("catalog:order_status", args=[order.pk]), {"status": st})
            order.refresh_from_db()
            self.assertEqual(order.status, st)
        self.assertIsNotNone(order.started_at)
        self.assertIsNotNone(order.completed_at)
        self.assertEqual(order.history.count(), 4)

        # 13. Buyurtmachi baho beradi (faqat bir marta)
        self.login("+998902000001")
        c.post(reverse("catalog:review_create", args=[order.pk]), self._review())
        c.post(reverse("catalog:review_create", args=[order.pk]), self._review(rating=1))
        self.assertEqual(Review.objects.filter(order=order).count(), 1)
        aziza.profile.refresh_from_db()
        self.assertEqual(float(aziza.profile.rating), 5.0)

        # 14. Ijrochi dashboardida buyurtma va hisoblangan daromad aks etadi
        self.login("+998935554433")
        r = c.get(reverse("catalog:income_dashboard"))
        stats = r.context["stats"]
        self.assertEqual(stats["month_completed"], 1)
        self.assertEqual(stats["month_income"], 180000)
        self.assertContains(r, "180 000 so‘m")

        # 15. Mahalla dashboardida agregat bandlik ko'rsatkichi yangilanadi
        after = self._mahalla_stats()
        self.assertEqual(after["providers"], before["providers"] + 1)
        self.assertEqual(after["verified"], before["verified"] + 1)
        self.assertEqual(after["women_with_orders"], before["women_with_orders"] + 1)
        self.assertEqual(after["completed_orders"], before["completed_orders"] + 1)
        self.assertTrue(AuditLog.objects.filter(action="order.status").exists())

    def _review(self, rating=5):
        return {"rating": rating, "quality_rating": 5, "communication_rating": 5, "punctuality_rating": 5, "comment": "Zo‘r"}

    def _mahalla_stats(self):
        self.login("+998900000002")
        return self.client.get(reverse("accounts:mahalla_home")).context["stats"]


@override_settings(MEDIA_ROOT=MEDIA)
class SecurityAndPrivacyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=io.StringIO())

    def login(self, phone):
        self.client.logout()
        self.assertTrue(self.client.login(phone=phone, password=PASSWORD))

    def test_all_pages_render_for_each_role(self):
        public = ["core:home", "core:how_it_works", "catalog:service_list", "catalog:smart_match", "psychology:list",
                  "accounts:login", "accounts:register", "core:offline"]
        for name in public:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse("catalog:service_detail", args=[Service.objects.first().pk])).status_code, 200)
        pages = {
            "+998901000001": ["accounts:profile", "accounts:profile_edit", "catalog:my_services", "catalog:service_create",
                              "catalog:order_list", "catalog:income_dashboard", "core:notifications", "catalog:favorites"],
            "+998902000001": ["accounts:profile", "catalog:order_list", "catalog:favorites", "psychology:my_consultations"],
            "+998900000002": ["accounts:mahalla_home", "accounts:mahalla_verifications"],
            "+998900000004": ["psychology:cabinet"],
            "+998900000001": ["core:panel_home", "core:panel_reports", "core:panel_services"],
        }
        for phone, names in pages.items():
            self.login(phone)
            for name in names:
                self.assertEqual(self.client.get(reverse(name)).status_code, 200, f"{phone} {name}")
        order = Order.objects.first()
        self.login(order.provider.phone)
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 200)
        self.login("+998900000001")
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_role_based_access(self):
        self.login("+998902000001")  # buyurtmachi
        self.assertEqual(self.client.get(reverse("catalog:service_create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("accounts:mahalla_home")).status_code, 403)
        self.assertEqual(self.client.get(reverse("core:panel_home")).status_code, 403)
        other = Order.objects.exclude(customer__phone="+998902000001").exclude(provider__phone="+998902000001").first()
        self.assertEqual(self.client.get(other.get_absolute_url()).status_code, 403)

    def test_mahalla_rep_sees_only_own_mahalla(self):
        u = User.objects.get(phone="+998901000004")  # G'ijduvon, tasdiqlanmagan
        vr = VerificationRequest.objects.create(user=u, mahalla=u.profile.mahalla)
        self.login("+998900000002")  # Navbahor vakili
        self.assertEqual(self.client.get(reverse("accounts:mahalla_verification_detail", args=[vr.pk])).status_code, 403)
        r = self.client.post(reverse("accounts:mahalla_verification_detail", args=[vr.pk]), {"decision": "approve"})
        self.assertEqual(r.status_code, 403)
        vr.refresh_from_db()
        self.assertEqual(vr.status, "pending")

    def test_consultation_privacy(self):
        p = Psychologist.objects.get(user__phone="+998900000004")
        slot = p.slots.first()
        self.login("+998902000001")
        self.client.post(reverse("psychology:detail", args=[p.pk]), {"slot": slot.pk, "format": "online", "message": "MAXFIY-MATN"})
        cons = Consultation.objects.get(client__phone="+998902000001")
        slot.refresh_from_db()
        self.assertTrue(slot.is_booked)
        # Psixolog ko'radi
        self.login("+998900000004")
        self.assertContains(self.client.get(reverse("psychology:cabinet")), "MAXFIY-MATN")
        self.client.post(reverse("psychology:consultation_action", args=[cons.pk, "confirm"]))
        cons.refresh_from_db()
        self.assertEqual(cons.status, "CONFIRMED")
        self.assertTrue(Notification.objects.filter(user=cons.client, message="Psixolog konsultatsiyangiz tasdiqlandi.").exists())
        # Bildirishnomada mazmun yo'q
        self.assertFalse(Notification.objects.filter(message__contains="MAXFIY-MATN").exists())
        # Mahalla vakili, admin dashboardi va API boshqalarga ko'rsatmaydi
        for phone, url in [("+998900000002", reverse("accounts:mahalla_home")), ("+998900000001", reverse("core:panel_home")),
                           ("+998900000001", "/admin/"), ("+998900000001", "/api/consultations/")]:
            self.login(phone)
            r = self.client.get(url)
            self.assertNotContains(r, "MAXFIY-MATN")
        self.assertEqual(self.client.get("/admin/psychology/consultation/").status_code, 404)
        self.login("+998902000002")
        self.assertEqual(self.client.post(reverse("psychology:consultation_action", args=[cons.pk, "cancel"])).status_code, 403)

    def test_login_rate_limit(self):
        for _ in range(5):
            self.client.post(reverse("accounts:login"), {"phone": "+998901000001", "password": "wrong-pass"})
        r = self.client.post(reverse("accounts:login"), {"phone": "+998901000001", "password": PASSWORD})
        self.assertEqual(r.status_code, 429)

    def test_upload_validation(self):
        self.login("+998901000001")
        fake = io.BytesIO(b"<?php echo 1; ?>")
        fake.name = "evil.php"
        p = User.objects.get(phone="+998901000001").profile
        r = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "D", "last_name": "R", "region": p.region_id, "district": p.district_id,
            "mahalla": p.mahalla_id, "avatar": fake,
        })
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors.get("avatar"))

    def test_ai_does_not_invent_services(self):
        r = self.client.get(reverse("catalog:smart_match"), {"text": "kosmik kema ta'mirlaydigan usta"})
        self.assertEqual(r.context["result"]["matches"], [])
        self.assertContains(r, "topilmadi")

    def test_region_consistency(self):
        self.client.post(reverse("accounts:register"), {"phone": "+998935550000", "password1": PASSWORD, "password2": PASSWORD, "role": "customer"})
        tashkent = District.objects.get(name="Chilonzor tumani")
        bukhara = Region.objects.get(name="Buxoro viloyati")
        r = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "A", "last_name": "B", "region": bukhara.pk, "district": tashkent.pk,
            "mahalla": tashkent.mahallas.first().pk,
        })
        self.assertTrue(r.context["form"].errors.get("district"))


class ApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=io.StringIO())

    def token(self, phone):
        r = self.client.post("/api/auth/login", {"phone": phone, "password": PASSWORD}, content_type="application/json")
        self.assertEqual(r.status_code, 200, r.content)
        return {"HTTP_AUTHORIZATION": "Bearer " + r.json()["access"]}

    def test_api_flow(self):
        r = self.client.post("/api/auth/register", {"phone": "+998935551111", "password": PASSWORD, "password_confirm": PASSWORD, "role": "provider"}, content_type="application/json")
        self.assertEqual(r.status_code, 201, r.content)
        h = self.token("+998935551111")
        m = Mahalla.objects.get(name="Navbahor MFY")
        r = self.client.patch("/api/profile/update", {"first_name": "Lola", "last_name": "Z", "region": m.district.region_id, "district": m.district_id, "mahalla": m.pk}, content_type="application/json", **h)
        self.assertEqual(r.status_code, 200, r.content)
        r = self.client.post("/api/verification/", {"note": "x"}, content_type="application/json", **h)
        self.assertEqual(r.status_code, 201, r.content)
        vr_id = r.json()["id"]
        # Mahalla vakili tasdiqlaydi
        hm = self.token("+998900000002")
        r = self.client.post(f"/api/verification/{vr_id}/decide/", {"decision": "approve"}, content_type="application/json", **hm)
        self.assertEqual(r.status_code, 200, r.content)
        # Xizmat yaratish
        cat = Category.objects.get(slug="uy-tozalash")
        r = self.client.post("/api/services/", {"title": "Tozalash API", "category": cat.pk, "description": "d", "price_type": "fixed", "price": 90000,
                                                 "service_mode": "client_address", "region": m.district.region_id, "district": m.district_id}, content_type="application/json", **h)
        self.assertEqual(r.status_code, 201, r.content)
        sid = r.json()["id"]
        # AI match
        r = self.client.post("/api/ai/match", {"text": "Buxoro shahrida uy tozalash kerak"}, content_type="application/json")
        self.assertIn(sid, [x["service_id"] for x in r.json()["matches"]] + [None])
        self.assertTrue(r.json()["matches"])
        # Buyurtma
        hc = self.token("+998902000001")
        r = self.client.post("/api/orders/", {"service": sid, "service_date": (timezone.localdate() + timedelta(days=2)).isoformat()}, content_type="application/json", **hc)
        self.assertEqual(r.status_code, 201, r.content)
        oid = r.json()["id"]
        # Buyurtmachi o'zi qabul qila olmaydi
        r = self.client.post(f"/api/orders/{oid}/status/", {"status": "ACCEPTED"}, content_type="application/json", **hc)
        self.assertEqual(r.status_code, 403)
        for st in ("ACCEPTED", "IN_PROGRESS", "COMPLETED"):
            r = self.client.post(f"/api/orders/{oid}/status/", {"status": st}, content_type="application/json", **h)
            self.assertEqual(r.status_code, 200, r.content)
        r = self.client.post("/api/reviews/", {"order": oid, "rating": 5, "quality_rating": 5, "communication_rating": 4, "punctuality_rating": 5}, content_type="application/json", **hc)
        self.assertEqual(r.status_code, 201, r.content)
        r = self.client.get("/api/dashboard/provider", **h)
        self.assertEqual(r.json()["month_income"], 90000)
        self.assertEqual(self.client.get("/api/dashboard/admin", **h).status_code, 403)
        self.assertEqual(self.client.get("/api/dashboard/mahalla", **hm).status_code, 200)
        self.assertEqual(self.client.get("/api/notifications/", **h).status_code, 200)

    def test_public_endpoints(self):
        self.assertEqual(self.client.get("/api/categories/").status_code, 200)
        self.assertEqual(self.client.get("/api/search?q=somsa").status_code, 200)
        self.assertEqual(self.client.get("/api/psychologists/").status_code, 200)
        self.assertEqual(self.client.get("/api/profile").status_code, 401)

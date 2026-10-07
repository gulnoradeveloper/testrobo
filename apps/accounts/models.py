from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.validators import IMAGE_VALIDATORS, phone_validator


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone, password, **extra):
        if not phone:
            raise ValueError("Telefon raqami majburiy")
        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra)

    def create_superuser(self, phone, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.Role.ADMIN)
        return self._create_user(phone, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        PROVIDER = "provider", "Xizmat ko‘rsatuvchi"
        CUSTOMER = "customer", "Buyurtmachi"
        MAHALLA = "mahalla", "Mahalla vakili"
        PSYCHOLOGIST = "psychologist", "Psixolog"
        ADMIN = "admin", "Administrator"

    SELF_REGISTER_ROLES = [Role.PROVIDER, Role.CUSTOMER, Role.PSYCHOLOGIST]

    phone = models.CharField("Telefon", max_length=13, unique=True, validators=[phone_validator])
    role = models.CharField("Rol", max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    is_active = models.BooleanField("Faol", default=True)
    is_staff = models.BooleanField("Admin panelga kirish", default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.display_name} ({self.phone})"

    @property
    def display_name(self):
        profile = getattr(self, "profile", None)
        if profile and (profile.first_name or profile.last_name):
            return f"{profile.first_name} {profile.last_name}".strip()
        return self.phone

    @property
    def is_provider(self):
        return self.role == self.Role.PROVIDER

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def is_mahalla(self):
        return self.role == self.Role.MAHALLA

    @property
    def is_psychologist(self):
        return self.role == self.Role.PSYCHOLOGIST

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def can_order(self):
        return self.role in (self.Role.CUSTOMER, self.Role.PROVIDER)


class Profile(models.Model):
    class Verification(models.TextChoices):
        UNVERIFIED = "unverified", "Tasdiqlanmagan"
        PENDING = "pending", "Tekshirilmoqda"
        VERIFIED = "verified", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"

    class AgeRange(models.TextChoices):
        A18 = "18-24", "18–24"
        A25 = "25-34", "25–34"
        A35 = "35-44", "35–44"
        A45 = "45-54", "45–54"
        A55 = "55+", "55 va undan katta"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField("Ism", max_length=60, blank=True)
    last_name = models.CharField("Familiya", max_length=60, blank=True)
    avatar = models.ImageField("Profil rasmi", upload_to="avatars/%Y/%m/", blank=True, validators=IMAGE_VALIDATORS)
    bio = models.TextField("Qisqacha ma’lumot", blank=True, max_length=1000)
    experience = models.TextField("Ish tajribasi", blank=True, max_length=1000)
    birth_year = models.PositiveSmallIntegerField("Tug‘ilgan yil", null=True, blank=True)
    age_range = models.CharField("Yosh diapazoni", max_length=8, choices=AgeRange.choices, blank=True)
    region = models.ForeignKey("core.Region", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Viloyat")
    district = models.ForeignKey("core.District", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tuman/shahar")
    mahalla = models.ForeignKey("core.Mahalla", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Mahalla", related_name="profiles")
    verification_status = models.CharField(
        "Verifikatsiya holati", max_length=12, choices=Verification.choices, default=Verification.UNVERIFIED
    )
    rating = models.DecimalField("Reyting", max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField("Sharhlar soni", default=0)

    class Meta:
        db_table = "profiles"
        verbose_name = "Profil"
        verbose_name_plural = "Profillar"

    def __str__(self):
        return self.full_name or self.user.phone

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_verified(self):
        return self.verification_status == self.Verification.VERIFIED

    @property
    def is_complete(self):
        return bool(self.first_name and self.last_name and self.region_id and self.district_id and self.mahalla_id)

    @property
    def location_label(self):
        parts = [p.name for p in (self.district, self.region) if p]
        return ", ".join(parts)


class Skill(models.Model):
    name = models.CharField("Ko‘nikma", max_length=80, unique=True)
    category = models.ForeignKey("catalog.Category", on_delete=models.SET_NULL, null=True, blank=True, related_name="skills")

    class Meta:
        db_table = "skills"
        ordering = ["name"]
        verbose_name = "Ko‘nikma"
        verbose_name_plural = "Ko‘nikmalar"

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Boshlang‘ich"
        MIDDLE = "middle", "O‘rta"
        EXPERT = "expert", "Tajribali"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="user_skills")
    level = models.CharField("Daraja", max_length=10, choices=Level.choices, default=Level.MIDDLE)

    class Meta:
        db_table = "user_skills"
        unique_together = [("user", "skill")]
        verbose_name = "Foydalanuvchi ko‘nikmasi"
        verbose_name_plural = "Foydalanuvchi ko‘nikmalari"

    def __str__(self):
        return f"{self.user.display_name}: {self.skill}"


class PortfolioImage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolio")
    image = models.ImageField("Rasm", upload_to="portfolio/%Y/%m/", validators=IMAGE_VALIDATORS)
    caption = models.CharField("Izoh", max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "portfolio_images"
        ordering = ["-created_at"]
        verbose_name = "Portfolio rasmi"
        verbose_name_plural = "Portfolio rasmlari"


class VerificationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Tekshirilmoqda"
        APPROVED = "approved", "Tasdiqlandi"
        REJECTED = "rejected", "Rad etildi"
        REVISION = "revision", "Qayta ko‘rib chiqishga yuborildi"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification_requests")
    mahalla = models.ForeignKey("core.Mahalla", on_delete=models.PROTECT, related_name="verification_requests", verbose_name="Mahalla")
    note = models.TextField("Ariza izohi", blank=True, max_length=1000)
    status = models.CharField("Holat", max_length=10, choices=Status.choices, default=Status.PENDING)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+", verbose_name="Ko‘rib chiqqan"
    )
    reviewer_comment = models.TextField("Mahalla vakili izohi", blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "verification_requests"
        ordering = ["-created_at"]
        verbose_name = "Verifikatsiya arizasi"
        verbose_name_plural = "Verifikatsiya arizalari"

    def __str__(self):
        return f"{self.user.display_name} — {self.get_status_display()}"



class RoleUserManager(UserManager):
    use_in_migrations = False
    role = None

    def get_queryset(self):
        return super().get_queryset().filter(role=self.role)


class ProviderManager(RoleUserManager):
    role = User.Role.PROVIDER


class CustomerManager(RoleUserManager):
    role = User.Role.CUSTOMER


class MahallaManager(RoleUserManager):
    role = User.Role.MAHALLA


class PsychologistManager(RoleUserManager):
    role = User.Role.PSYCHOLOGIST


class ProviderUser(User):
    objects = ProviderManager()

    class Meta:
        proxy = True
        verbose_name = "Xizmat ko‘rsatuvchi"
        verbose_name_plural = "Foydalanuvchilar: xizmat ko‘rsatuvchilar"


class CustomerUser(User):
    objects = CustomerManager()

    class Meta:
        proxy = True
        verbose_name = "Buyurtmachi"
        verbose_name_plural = "Foydalanuvchilar: buyurtmachilar"


class MahallaUser(User):
    objects = MahallaManager()

    class Meta:
        proxy = True
        verbose_name = "Mahalla vakili"
        verbose_name_plural = "Foydalanuvchilar: mahalla vakillari"


class PsychologistUser(User):
    objects = PsychologistManager()

    class Meta:
        proxy = True
        verbose_name = "Psixolog (foydalanuvchi)"
        verbose_name_plural = "Foydalanuvchilar: psixologlar"

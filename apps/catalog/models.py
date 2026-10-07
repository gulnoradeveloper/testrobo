from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from apps.core.validators import IMAGE_VALIDATORS


class Category(models.Model):
    name = models.CharField("Nomi", max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    icon = models.CharField("Ikonka (emoji)", max_length=8, blank=True, default="✨")
    keywords = models.TextField(
        "AI kalit so‘zlari", blank=True,
        help_text="Vergul bilan ajratilgan so‘z o‘zaklari. Smart Matching shu so‘zlar orqali kategoriyani aniqlaydi.",
    )
    order = models.PositiveSmallIntegerField("Tartib", default=0)
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        db_table = "categories"
        ordering = ["order", "name"]
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return f"{self.icon} {self.name}".strip()

    def keyword_list(self):
        return [k.strip().lower() for k in self.keywords.split(",") if k.strip()]


class ServiceQuerySet(models.QuerySet):
    def public(self):
        return self.filter(status=Service.Status.ACTIVE, provider__is_active=True, category__is_active=True)


class Service(models.Model):
    class PriceType(models.TextChoices):
        FIXED = "fixed", "Belgilangan"
        FROM = "from", "Boshlang‘ich"
        NEGOTIABLE = "negotiable", "Kelishiladi"

    class Mode(models.TextChoices):
        AT_HOME = "at_home", "Uyimda"
        CLIENT_ADDRESS = "client_address", "Mijoz manzilida"
        REMOTE = "remote", "Masofadan"

    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        PAUSED = "paused", "To‘xtatilgan"
        BLOCKED = "blocked", "Bloklangan (moderatsiya)"

    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="services", verbose_name="Ijrochi")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="services", verbose_name="Kategoriya")
    title = models.CharField("Xizmat nomi", max_length=140)
    description = models.TextField("Tavsif", max_length=3000)
    price_type = models.CharField("Narx turi", max_length=12, choices=PriceType.choices, default=PriceType.FIXED)
    price = models.PositiveIntegerField("Narx (so‘m)", null=True, blank=True)
    service_mode = models.CharField("Xizmat ko‘rsatish shakli", max_length=16, choices=Mode.choices, default=Mode.AT_HOME)
    region = models.ForeignKey("core.Region", on_delete=models.PROTECT, verbose_name="Viloyat")
    district = models.ForeignKey("core.District", on_delete=models.PROTECT, verbose_name="Tuman/shahar")
    duration = models.CharField("Bajarish muddati", max_length=80, blank=True, help_text="Masalan: 1 kun, 3–5 kun")
    status = models.CharField("Holat", max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ServiceQuerySet.as_manager()

    class Meta:
        db_table = "services"
        ordering = ["-created_at"]
        verbose_name = "Xizmat"
        verbose_name_plural = "Xizmatlar"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("catalog:service_detail", args=[self.pk])

    @property
    def price_label(self):
        if self.price_type == self.PriceType.NEGOTIABLE or not self.price:
            return "Kelishiladi"
        amount = f"{self.price:,}".replace(",", " ")
        suffix = " so‘mdan" if self.price_type == self.PriceType.FROM else " so‘m"
        return amount + suffix

    @property
    def cover(self):
        img = self.images.first()
        return img.image.url if img else None


class ServiceImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("Rasm", upload_to="services/%Y/%m/", validators=IMAGE_VALIDATORS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "service_images"
        ordering = ["id"]
        verbose_name = "Xizmat rasmi"
        verbose_name_plural = "Xizmat rasmlari"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "favorites"
        unique_together = [("user", "service")]
        verbose_name = "Sevimli"
        verbose_name_plural = "Sevimlilar"


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "Yangi"
        ACCEPTED = "ACCEPTED", "Qabul qilindi"
        IN_PROGRESS = "IN_PROGRESS", "Jarayonda"
        COMPLETED = "COMPLETED", "Bajarildi"
        CANCELLED = "CANCELLED", "Bekor qilindi"
        REJECTED = "REJECTED", "Rad etildi"

    ACTIVE_STATUSES = [Status.NEW, Status.ACCEPTED, Status.IN_PROGRESS]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders_made", verbose_name="Buyurtmachi")
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders_received", verbose_name="Ijrochi")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="orders", verbose_name="Xizmat")
    price = models.PositiveIntegerField("Kelishilgan narx (so‘m)", null=True, blank=True)
    service_date = models.DateField("Sana")
    address_or_area = models.CharField("Manzil yoki hudud", max_length=255, blank=True)
    comment = models.TextField("Izoh", blank=True, max_length=1000)
    status = models.CharField("Holat", max_length=12, choices=Status.choices, default=Status.NEW)
    started_at = models.DateTimeField("Ish boshlangan vaqt", null=True, blank=True)
    completed_at = models.DateTimeField("Ish yakunlangan vaqt", null=True, blank=True)
    created_at = models.DateTimeField("Yaratilgan vaqt", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"

    def __str__(self):
        return f"#{self.pk} {self.service.title}"

    def get_absolute_url(self):
        return reverse("catalog:order_detail", args=[self.pk])

    @property
    def is_on_site(self):
        """BEGOYIM Safe: mijoz manzilida bajariladigan buyurtma."""
        return self.service.service_mode == Service.Mode.CLIENT_ADDRESS

    @property
    def price_label(self):
        if not self.price:
            return "Kelishiladi"
        return f"{self.price:,}".replace(",", " ") + " so‘m"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=12, blank=True)
    to_status = models.CharField(max_length=12)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_status_history"
        ordering = ["created_at"]
        verbose_name = "Buyurtma holati tarixi"
        verbose_name_plural = "Buyurtma holati tarixi"

    @property
    def to_label(self):
        return Order.Status(self.to_status).label


RATING_VALIDATORS = [MinValueValidator(1), MaxValueValidator(5)]


class Review(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="review")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_given")
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_received")
    rating = models.PositiveSmallIntegerField("Umumiy baho", validators=RATING_VALIDATORS)
    quality_rating = models.PositiveSmallIntegerField("Xizmat sifati", validators=RATING_VALIDATORS)
    communication_rating = models.PositiveSmallIntegerField("Muomala", validators=RATING_VALIDATORS)
    punctuality_rating = models.PositiveSmallIntegerField("Vaqtida bajarilishi", validators=RATING_VALIDATORS)
    comment = models.TextField("Umumiy izoh", blank=True, max_length=1000)
    is_hidden = models.BooleanField("Yashirilgan (moderatsiya)", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews"
        ordering = ["-created_at"]
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"

    def __str__(self):
        return f"{self.rating}★ — {self.order}"

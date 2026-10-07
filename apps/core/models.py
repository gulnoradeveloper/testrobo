from django.conf import settings
from django.db import models


class Region(models.Model):
    name = models.CharField("Nomi", max_length=120, unique=True)

    class Meta:
        db_table = "regions"
        ordering = ["name"]
        verbose_name = "Viloyat"
        verbose_name_plural = "Hududlar: viloyatlar"

    def __str__(self):
        return self.name


class District(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="districts", verbose_name="Viloyat")
    name = models.CharField("Nomi", max_length=120)

    class Meta:
        db_table = "districts"
        ordering = ["name"]
        unique_together = [("region", "name")]
        verbose_name = "Tuman/shahar"
        verbose_name_plural = "Hududlar: tumanlar/shaharlar"

    def __str__(self):
        return self.name


class Mahalla(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="mahallas", verbose_name="Tuman/shahar")
    name = models.CharField("Nomi", max_length=160)

    class Meta:
        db_table = "mahallas"
        ordering = ["name"]
        unique_together = [("district", "name")]
        verbose_name = "Mahalla"
        verbose_name_plural = "Hududlar: mahallalar"

    def __str__(self):
        return f"{self.name} ({self.district.name})"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField("Xabar", max_length=255)
    link = models.CharField("Havola", max_length=255, blank=True)
    is_read = models.BooleanField("O‘qilgan", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"

    def __str__(self):
        return self.message


class Report(models.Model):
    """Shikoyat: xizmat yoki profil bo'yicha."""

    class Reason(models.TextChoices):
        WRONG_INFO = "wrong_info", "Noto‘g‘ri ma’lumot"
        QUALITY = "quality", "Xizmat sifati"
        BEHAVIOR = "behavior", "Nomaqbul xatti-harakat"
        FRAUD = "fraud", "Firibgarlik gumoni"
        SAFETY = "safety", "Xavfsizlik"
        OTHER = "other", "Boshqa"

    class Status(models.TextChoices):
        NEW = "NEW", "Yangi"
        REVIEWING = "REVIEWING", "Ko‘rib chiqilmoqda"
        RESOLVED = "RESOLVED", "Hal qilindi"

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_sent", verbose_name="Shikoyatchi")
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="reports_received", verbose_name="Profil"
    )
    target_service = models.ForeignKey(
        "catalog.Service", on_delete=models.CASCADE, null=True, blank=True, related_name="reports", verbose_name="Xizmat"
    )
    reason = models.CharField("Sabab", max_length=20, choices=Reason.choices)
    comment = models.TextField("Izoh", blank=True, max_length=1000)
    status = models.CharField("Holat", max_length=12, choices=Status.choices, default=Status.NEW)
    admin_note = models.TextField("Admin izohi", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reports"
        ordering = ["-created_at"]
        verbose_name = "Shikoyat"
        verbose_name_plural = "Shikoyatlar"

    def __str__(self):
        return f"#{self.pk} {self.get_reason_display()} ({self.get_status_display()})"

    @property
    def target_label(self):
        if self.target_service_id:
            return f"Xizmat: {self.target_service.title}"
        if self.target_user_id:
            return f"Profil: {self.target_user.display_name}"
        return "—"


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    action = models.CharField(max_length=80)
    object_type = models.CharField(max_length=60, blank=True)
    object_id = models.CharField(max_length=40, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        verbose_name = "Audit yozuvi"
        verbose_name_plural = "Audit log"

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action}"

"""Psixologik yordam moduli.

MAXFIYLIK: Consultation.message (murojaat mazmuni) va psychologist_note faqat
murojaat egasi va tegishli psixologga ko'rinadi. Ular admin panelda, mahalla
dashboardida va statistikada ko'rsatilmaydi.
"""
from django.conf import settings
from django.db import models


class Psychologist(models.Model):
    class Format(models.TextChoices):
        ONLINE = "online", "ONLINE"
        OFFLINE = "offline", "OFFLINE"
        BOTH = "both", "ONLINE / OFFLINE"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="psychologist")
    specialization = models.CharField("Yo‘nalish", max_length=160)
    experience_years = models.PositiveSmallIntegerField("Tajriba (yil)", default=0)
    consultation_format = models.CharField("Konsultatsiya shakli", max_length=8, choices=Format.choices, default=Format.BOTH)
    about = models.TextField("Mutaxassis haqida", blank=True, max_length=2000)
    office_address = models.CharField("Offline qabul manzili", max_length=255, blank=True)
    is_approved = models.BooleanField("Admin tomonidan tasdiqlangan", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "psychologists"
        verbose_name = "Psixolog"
        verbose_name_plural = "Psixologlar"

    def __str__(self):
        return self.user.display_name

    def supports(self, fmt):
        return self.consultation_format in (self.Format.BOTH, fmt)


class PsychologistSchedule(models.Model):
    psychologist = models.ForeignKey(Psychologist, on_delete=models.CASCADE, related_name="slots")
    start_at = models.DateTimeField("Boshlanish")
    end_at = models.DateTimeField("Tugash")
    is_booked = models.BooleanField("Band", default=False)

    class Meta:
        db_table = "psychologist_schedules"
        ordering = ["start_at"]
        verbose_name = "Qabul vaqti"
        verbose_name_plural = "Qabul jadvallari"

    def __str__(self):
        return f"{self.start_at:%d.%m.%Y %H:%M}–{self.end_at:%H:%M}"


class Consultation(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "So‘rov yuborildi"
        CONFIRMED = "CONFIRMED", "Tasdiqlandi"
        REJECTED = "REJECTED", "Rad etildi"
        COMPLETED = "COMPLETED", "Yakunlandi"
        CANCELLED = "CANCELLED", "Bekor qilindi"

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consultations")
    psychologist = models.ForeignKey(Psychologist, on_delete=models.CASCADE, related_name="consultations")
    slot = models.ForeignKey(PsychologistSchedule, on_delete=models.SET_NULL, null=True, related_name="consultations")
    format = models.CharField("Shakl", max_length=8, choices=[("online", "ONLINE"), ("offline", "OFFLINE")])
    message = models.TextField("Murojaat mazmuni (maxfiy)", blank=True, max_length=2000)
    status = models.CharField("Holat", max_length=10, choices=Status.choices, default=Status.REQUESTED)
    psychologist_note = models.TextField("Psixolog izohi mijozga (maxfiy)", blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consultations"
        ordering = ["-created_at"]
        verbose_name = "Konsultatsiya"
        verbose_name_plural = "Konsultatsiyalar"

    def can_view(self, user):
        return user.is_authenticated and (user.pk == self.client_id or user.pk == self.psychologist.user_id)

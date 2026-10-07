"""Admin panel: psixologlar va qabul jadvallari.

Consultation modeli ATAYLAB ro'yxatdan o'tkazilmagan: murojaat mazmuni oddiy
administratorga ham ko'rinmasligi kerak (TT, 2.4 va 11-bo'lim).
"""
from django.contrib import admin

from apps.core.services import notify

from .models import Psychologist, PsychologistSchedule


@admin.register(Psychologist)
class PsychologistAdmin(admin.ModelAdmin):
    list_display = ["user", "specialization", "experience_years", "consultation_format", "is_approved"]
    list_filter = ["is_approved", "consultation_format"]
    search_fields = ["user__phone", "user__profile__first_name", "user__profile__last_name", "specialization"]
    actions = ["approve"]

    @admin.action(description="Mutaxassisni tasdiqlash")
    def approve(self, request, queryset):
        for p in queryset.filter(is_approved=False):
            p.is_approved = True
            p.save(update_fields=["is_approved"])
            notify(p.user, "Psixolog profilingiz administrator tomonidan tasdiqlandi.", "/psixologik-yordam/kabinet/")


@admin.register(PsychologistSchedule)
class PsychologistScheduleAdmin(admin.ModelAdmin):
    list_display = ["psychologist", "start_at", "end_at", "is_booked"]
    list_filter = ["is_booked", "psychologist"]

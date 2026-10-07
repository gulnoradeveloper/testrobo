"""Verifikatsiya biznes-logikasi (web va API uchun umumiy)."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.core.services import audit, notify

from .models import Profile, VerificationRequest


def submit_verification(user, note="", request=None):
    profile = user.profile
    if not user.is_provider:
        raise PermissionDenied("Verifikatsiya faqat xizmat ko‘rsatuvchilar uchun.")
    if not profile.is_complete:
        raise ValidationError("Avval profilingizni to‘liq to‘ldiring (ism, familiya, viloyat, tuman, mahalla).")
    if profile.verification_status in (Profile.Verification.PENDING, Profile.Verification.VERIFIED):
        raise ValidationError("Arizangiz allaqachon ko‘rib chiqilmoqda yoki tasdiqlangan.")
    with transaction.atomic():
        vr = VerificationRequest.objects.create(user=user, mahalla=profile.mahalla, note=note)
        profile.verification_status = Profile.Verification.PENDING
        profile.save(update_fields=["verification_status"])
    from apps.accounts.models import User

    for rep in User.objects.filter(role=User.Role.MAHALLA, is_active=True, profile__mahalla=profile.mahalla):
        notify(rep, f"Yangi verifikatsiya arizasi: {user.display_name}", reverse("accounts:mahalla_verifications"))
    audit(user, "verification.submit", vr, request)
    return vr


def can_review_verification(reviewer, vr):
    if reviewer.is_admin_role:
        return True
    return reviewer.is_mahalla and getattr(reviewer.profile, "mahalla_id", None) == vr.mahalla_id


DECISIONS = {
    "approve": (VerificationRequest.Status.APPROVED, Profile.Verification.VERIFIED, "Verifikatsiyangiz tasdiqlandi. ✓"),
    "reject": (VerificationRequest.Status.REJECTED, Profile.Verification.REJECTED, "Verifikatsiya arizangiz rad etildi."),
    "revision": (
        VerificationRequest.Status.REVISION,
        Profile.Verification.UNVERIFIED,
        "Verifikatsiya arizangiz qayta ko‘rib chiqish uchun qaytarildi. Ma’lumotlarni yangilab, qayta yuboring.",
    ),
}


def decide_verification(reviewer, vr, decision, comment="", request=None):
    if decision not in DECISIONS:
        raise ValidationError("Noma’lum qaror.")
    if not can_review_verification(reviewer, vr):
        raise PermissionDenied("Bu ariza sizning hududingizga tegishli emas.")
    if vr.status != VerificationRequest.Status.PENDING:
        raise ValidationError("Bu ariza allaqachon ko‘rib chiqilgan.")
    vr_status, profile_status, message = DECISIONS[decision]
    with transaction.atomic():
        vr.status = vr_status
        vr.reviewer = reviewer
        vr.reviewer_comment = comment
        vr.decided_at = timezone.now()
        vr.save()
        profile = vr.user.profile
        profile.verification_status = profile_status
        profile.save(update_fields=["verification_status"])
    if comment:
        message = f"{message} Izoh: {comment}"
    notify(vr.user, message, reverse("accounts:profile"))
    audit(reviewer, f"verification.{decision}", vr, request, user_id=vr.user_id)
    return vr

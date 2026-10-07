"""Psixologik yordam. Murojaat mazmuni faqat mijoz va psixologga ko'rinadi."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.core.permissions import role_required
from apps.core.services import audit, notify

from .forms import BookingForm, PsychologistProfileForm, SlotForm
from .models import Consultation, Psychologist, PsychologistSchedule


def psychologist_list(request):
    items = Psychologist.objects.filter(is_approved=True, user__is_active=True).select_related("user__profile")
    now = timezone.now()
    for p in items:
        p.next_slot = p.slots.filter(is_booked=False, start_at__gt=now).first()
    return render(request, "psychology/list.html", {"items": items})


def psychologist_detail(request, pk):
    p = get_object_or_404(Psychologist.objects.select_related("user__profile"), pk=pk, is_approved=True, user__is_active=True)
    form = BookingForm(request.POST or None, psychologist=p)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={request.path}")
        if request.user.pk == p.user_id:
            raise PermissionDenied("O‘zingizga yozila olmaysiz.")
        if form.is_valid():
            with transaction.atomic():
                slot = PsychologistSchedule.objects.select_for_update().get(pk=form.cleaned_data["slot"].pk)
                if slot.is_booked:
                    messages.error(request, "Bu vaqt band bo‘lib qoldi. Boshqa vaqtni tanlang.")
                    return redirect(request.path)
                c = form.save(commit=False)
                c.client, c.psychologist = request.user, p
                c.save()
                slot.is_booked = True
                slot.save(update_fields=["is_booked"])
            # Bildirishnomada murojaat mazmuni yo'q — faqat fakt
            notify(p.user, "Yangi konsultatsiya so‘rovi keldi.", reverse("psychology:cabinet"))
            audit(request.user, "consultation.request", c, request)
            messages.success(request, "So‘rovingiz psixologga yuborildi. Tasdiqlanganda xabar olasiz.")
            return redirect("psychology:my_consultations")
    return render(request, "psychology/detail.html", {"p": p, "form": form})


@login_required
def my_consultations(request):
    items = Consultation.objects.filter(client=request.user).select_related("psychologist__user__profile", "slot")
    return render(request, "psychology/my_consultations.html", {"items": items})


def _get_psychologist(user):
    p, _ = Psychologist.objects.get_or_create(user=user, defaults={"specialization": "Oilaviy psixologiya"})
    return p


@role_required(User.Role.PSYCHOLOGIST, allow_admin=False)
def cabinet(request):
    p = _get_psychologist(request.user)
    profile_form = PsychologistProfileForm(instance=p, prefix="pf")
    slot_form = SlotForm(prefix="sl")
    if request.method == "POST":
        if "save_profile" in request.POST:
            profile_form = PsychologistProfileForm(request.POST, instance=p, prefix="pf")
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil saqlandi.")
                return redirect("psychology:cabinet")
        elif "add_slot" in request.POST:
            slot_form = SlotForm(request.POST, prefix="sl")
            if slot_form.is_valid():
                slot = slot_form.save(commit=False)
                slot.psychologist = p
                slot.save()
                messages.success(request, "Qabul vaqti qo‘shildi.")
                return redirect("psychology:cabinet")
    return render(request, "psychology/cabinet.html", {
        "p": p, "profile_form": profile_form, "slot_form": slot_form,
        "slots": p.slots.filter(start_at__gt=timezone.now()),
        "requests": p.consultations.select_related("client__profile", "slot"),
    })


@role_required(User.Role.PSYCHOLOGIST, allow_admin=False)
@require_POST
def slot_delete(request, pk):
    slot = get_object_or_404(PsychologistSchedule, pk=pk, psychologist__user=request.user, is_booked=False)
    slot.delete()
    return redirect("psychology:cabinet")


ACTIONS = {
    # action: (kim, ruxsat etilgan joriy holatlar, yangi holat, mijozga xabar)
    "confirm": ("psychologist", [Consultation.Status.REQUESTED], Consultation.Status.CONFIRMED, "Psixolog konsultatsiyangiz tasdiqlandi."),
    "reject": ("psychologist", [Consultation.Status.REQUESTED], Consultation.Status.REJECTED, "Psixolog konsultatsiya so‘rovingizni rad etdi."),
    "complete": ("psychologist", [Consultation.Status.CONFIRMED], Consultation.Status.COMPLETED, "Konsultatsiya yakunlandi."),
    "cancel": ("client", [Consultation.Status.REQUESTED, Consultation.Status.CONFIRMED], Consultation.Status.CANCELLED, None),
}


@login_required
@require_POST
def consultation_action(request, pk, action):
    c = get_object_or_404(Consultation.objects.select_related("psychologist__user", "slot"), pk=pk)
    if action not in ACTIONS or not c.can_view(request.user):
        raise PermissionDenied
    who, allowed, new_status, msg = ACTIONS[action]
    is_psy = request.user.pk == c.psychologist.user_id
    if (who == "psychologist" and not is_psy) or (who == "client" and request.user.pk != c.client_id) or c.status not in allowed:
        raise PermissionDenied("Bu amalni bajarib bo‘lmaydi.")
    with transaction.atomic():
        c.status = new_status
        if is_psy and request.POST.get("note"):
            c.psychologist_note = request.POST["note"][:1000]
        c.save()
        if new_status in (Consultation.Status.REJECTED, Consultation.Status.CANCELLED) and c.slot:
            c.slot.is_booked = False
            c.slot.save(update_fields=["is_booked"])
    if msg:
        notify(c.client, msg, reverse("psychology:my_consultations"))
    else:
        notify(c.psychologist.user, "Konsultatsiya mijoz tomonidan bekor qilindi.", reverse("psychology:cabinet"))
    audit(request.user, f"consultation.{action}", c, request)
    messages.success(request, f"Holat: {c.get_status_display()}")
    return redirect("psychology:cabinet" if is_psy else "psychology:my_consultations")

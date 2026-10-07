from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.catalog.models import Order, Review, Service
from apps.catalog.services import mahalla_dashboard
from apps.core.forms import ReportForm
from apps.core.permissions import role_required
from apps.core.services import audit, client_ip

from .forms import LoginForm, ProfileForm, RegisterForm, VerificationDecisionForm, VerificationForm
from .models import PortfolioImage, Skill, User, UserSkill, VerificationRequest
from .services import decide_verification, submit_verification


def _safe_next(request, default):
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return nxt
    return default


def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    form = RegisterForm(request.POST or None, initial={"role": request.GET.get("role", User.Role.PROVIDER)})
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        audit(user, "auth.register", user, request, role=user.role)
        messages.success(request, "Ro‘yxatdan o‘tdingiz! Endi ma’lumotlaringizni to‘ldiring.")
        return redirect("accounts:profile_edit")
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        phone = form.cleaned_data["phone"]
        key = f"login-attempts:{client_ip(request)}:{phone}"
        attempts = cache.get(key, 0)
        if attempts >= settings.LOGIN_RATE_LIMIT:
            messages.error(request, "Juda ko‘p urinish. Iltimos, 15 daqiqadan so‘ng qayta urinib ko‘ring.")
            return render(request, "accounts/login.html", {"form": form}, status=429)
        user = authenticate(request, phone=phone, password=form.cleaned_data["password"])
        if user is None:
            cache.set(key, attempts + 1, settings.LOGIN_RATE_WINDOW)
            messages.error(request, "Telefon raqami yoki parol noto‘g‘ri.")
        else:
            cache.delete(key)
            login(request, user)
            audit(user, "auth.login", user, request)
            return redirect(_safe_next(request, "core:home"))
    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("core:home")


def _profile_context(user):
    profile = user.profile
    completed = Order.objects.filter(provider=user, status=Order.Status.COMPLETED).count()
    return {
        "owner": user,
        "p": profile,
        "skills": user.user_skills.select_related("skill"),
        "portfolio": user.portfolio.all()[:12],
        "services": Service.objects.public().filter(provider=user).select_related("category", "district").prefetch_related("images"),
        "reviews": Review.objects.filter(provider=user, is_hidden=False).select_related("customer__profile", "order__service")[:10],
        "completed_orders": completed,
    }


@login_required
def my_profile(request):
    ctx = _profile_context(request.user)
    ctx["is_me"] = True
    ctx["verification_form"] = VerificationForm()
    ctx["last_request"] = request.user.verification_requests.first()
    return render(request, "accounts/profile.html", ctx)


def public_profile(request, pk):
    user = get_object_or_404(User, pk=pk, is_active=True, role=User.Role.PROVIDER)
    ctx = _profile_context(user)
    ctx["is_me"] = request.user == user
    ctx["report_form"] = ReportForm()
    return render(request, "accounts/profile.html", ctx)


@login_required
def profile_edit(request):
    profile = request.user.profile
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        if "skills" in form.cleaned_data:
            chosen = set(form.cleaned_data["skills"])
            new_name = (form.cleaned_data.get("new_skill") or "").strip()
            if new_name:
                skill, _ = Skill.objects.get_or_create(
                    name__iexact=new_name, defaults={"name": new_name, "category": form.cleaned_data.get("new_skill_category")}
                )
                chosen.add(skill)
            UserSkill.objects.filter(user=request.user).exclude(skill__in=chosen).delete()
            for s in chosen:
                UserSkill.objects.get_or_create(user=request.user, skill=s)
        for img in form.cleaned_data.get("portfolio") or []:
            PortfolioImage.objects.create(user=request.user, image=img)
        audit(request.user, "profile.update", profile, request)
        messages.success(request, "Profil saqlandi.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
@require_POST
def portfolio_delete(request, pk):
    img = get_object_or_404(PortfolioImage, pk=pk, user=request.user)
    img.image.delete(save=False)
    img.delete()
    messages.success(request, "Rasm o‘chirildi.")
    return redirect("accounts:profile_edit")


@role_required(User.Role.PROVIDER, allow_admin=False)
@require_POST
def verification_submit(request):
    form = VerificationForm(request.POST)
    if form.is_valid():
        try:
            submit_verification(request.user, form.cleaned_data["note"], request)
            messages.success(request, "Ariza mahalla vakiliga yuborildi. Holat: Tekshirilmoqda.")
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))
    return redirect("accounts:profile")


# ----- Mahalla vakili -----

def _rep_mahalla(user):
    mahalla = user.profile.mahalla
    if mahalla is None:
        raise PermissionDenied("Sizga mahalla biriktirilmagan. Administratorga murojaat qiling.")
    return mahalla


@role_required(User.Role.MAHALLA, allow_admin=False)
def mahalla_home(request):
    mahalla = _rep_mahalla(request.user)
    return render(request, "accounts/mahalla_dashboard.html", {"mahalla": mahalla, "stats": mahalla_dashboard(mahalla)})


@role_required(User.Role.MAHALLA, allow_admin=False)
def mahalla_verifications(request):
    mahalla = _rep_mahalla(request.user)
    status = request.GET.get("status", "pending")
    qs = VerificationRequest.objects.filter(mahalla=mahalla).select_related("user__profile")
    if status in VerificationRequest.Status.values:
        qs = qs.filter(status=status)
    return render(request, "accounts/mahalla_verifications.html", {
        "mahalla": mahalla, "requests": qs, "status": status, "statuses": VerificationRequest.Status.choices,
    })


@role_required(User.Role.MAHALLA)
def mahalla_verification_detail(request, pk):
    vr = get_object_or_404(VerificationRequest.objects.select_related("user__profile"), pk=pk)
    if not request.user.is_admin_role and vr.mahalla_id != getattr(request.user.profile, "mahalla_id", None):
        raise PermissionDenied("Bu ariza sizning hududingizga tegishli emas.")
    form = VerificationDecisionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            decide_verification(request.user, vr, form.cleaned_data["decision"], form.cleaned_data["comment"], request)
            messages.success(request, "Qaror saqlandi.")
            return redirect("accounts:mahalla_verifications")
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))
    applicant = vr.user
    return render(request, "accounts/mahalla_verification_detail.html", {
        "vr": vr, "form": form, "applicant": applicant,
        "skills": applicant.user_skills.select_related("skill"),
        "portfolio": applicant.portfolio.all()[:8],
        "services_count": applicant.services.count(),
        "history": VerificationRequest.objects.filter(user=applicant).exclude(pk=vr.pk),
    })

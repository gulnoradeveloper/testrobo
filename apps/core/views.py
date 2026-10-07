from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.catalog.models import Category, Order, Service
from apps.catalog.services import admin_dashboard
from apps.psychology.models import Psychologist

from .forms import ReportForm
from .models import District, Mahalla, Notification, Report
from .permissions import admin_required
from .services import audit, notify


def safe_back(request, url, default="/"):
    if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return url
    return default


def home(request):
    recommended = (
        Service.objects.public()
        .select_related("provider__profile", "category", "district", "region")
        .prefetch_related("images")
        .order_by("-provider__profile__rating", "-created_at")
    )
    profile = getattr(request.user, "profile", None) if request.user.is_authenticated else None
    if profile and profile.region_id:
        local = recommended.filter(region_id=profile.region_id)
        if local.exists():
            recommended = local
    return render(request, "core/home.html", {
        "categories": Category.objects.filter(is_active=True),
        "recommended": recommended[:6],
        "psychologists": Psychologist.objects.filter(is_approved=True, user__is_active=True).select_related("user__profile")[:3],
        "stats": {
            "providers": User.objects.filter(role=User.Role.PROVIDER, is_active=True).count(),
            "services": Service.objects.public().count(),
            "completed": Order.objects.filter(status=Order.Status.COMPLETED).count(),
        },
    })


def how_it_works(request):
    return render(request, "core/how_it_works.html")


@login_required
def notifications(request):
    items = request.user.notifications.all()[:100]
    return render(request, "core/notifications.html", {"items": items})


@login_required
def notification_open(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    if not n.is_read:
        n.is_read = True
        n.save(update_fields=["is_read"])
    if n.link.startswith("/"):
        return redirect(n.link)
    return redirect("core:notifications")


@login_required
@require_POST
def notifications_read_all(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect("core:notifications")


@login_required
@require_POST
def report_create(request):
    form = ReportForm(request.POST)
    service_id, user_id = request.POST.get("service"), request.POST.get("user")
    back = safe_back(request, request.META.get("HTTP_REFERER"))
    if form.is_valid() and (service_id or user_id):
        report = form.save(commit=False)
        report.reporter = request.user
        if service_id:
            report.target_service = get_object_or_404(Service, pk=service_id)
        if user_id:
            report.target_user = get_object_or_404(User, pk=user_id)
        report.save()
        audit(request.user, "report.create", report, request)
        for admin in User.objects.filter(role=User.Role.ADMIN, is_active=True):
            notify(admin, f"Yangi shikoyat: {report.get_reason_display()}", "/panel/shikoyatlar/")
        messages.success(request, "Shikoyatingiz administratorga yuborildi. Rahmat!")
    else:
        messages.error(request, "Shikoyat sababini tanlang.")
    return redirect(back)


@cache_control(max_age=3600)
def districts_json(request):
    qs = District.objects.filter(region_id=request.GET.get("region") or 0).values("id", "name")
    return JsonResponse({"results": list(qs)})


@cache_control(max_age=3600)
def mahallas_json(request):
    qs = Mahalla.objects.filter(district_id=request.GET.get("district") or 0).values("id", "name")
    return JsonResponse({"results": list(qs)})


# ----- Administrator paneli (qisqa dashboard + shikoyatlar va moderatsiya) -----

@admin_required
def panel_home(request):
    return render(request, "core/panel_home.html", {"stats": admin_dashboard()})


@admin_required
def panel_reports(request):
    status = request.GET.get("status", "")
    qs = Report.objects.select_related("reporter__profile", "target_user__profile", "target_service")
    if status in Report.Status.values:
        qs = qs.filter(status=status)
    return render(request, "core/panel_reports.html", {"reports": qs, "status": status, "statuses": Report.Status.choices})


@admin_required
@require_POST
def panel_report_update(request, pk):
    report = get_object_or_404(Report, pk=pk)
    new_status = request.POST.get("status")
    if new_status in Report.Status.values:
        report.status = new_status
        report.admin_note = request.POST.get("admin_note", report.admin_note)[:2000]
        report.save()
        audit(request.user, "report.status", report, request, status=new_status)
    action = request.POST.get("action")
    if action == "block_service" and report.target_service:
        report.target_service.status = Service.Status.BLOCKED
        report.target_service.save(update_fields=["status"])
        notify(report.target_service.provider, f"Xizmatingiz moderatsiya tomonidan bloklandi: {report.target_service.title}")
        audit(request.user, "service.block", report.target_service, request)
    elif action == "block_user" and report.target_user and not report.target_user.is_superuser:
        report.target_user.is_active = False
        report.target_user.save(update_fields=["is_active"])
        audit(request.user, "user.block", report.target_user, request)
    messages.success(request, "Shikoyat yangilandi.")
    return redirect("core:panel_reports")


@admin_required
def panel_services(request):
    status = request.GET.get("status", "")
    qs = Service.objects.select_related("provider__profile", "category", "district").order_by("-created_at")
    if status in Service.Status.values:
        qs = qs.filter(status=status)
    return render(request, "core/panel_services.html", {"services": qs[:200], "status": status, "statuses": Service.Status.choices})


@admin_required
@require_POST
def panel_service_moderate(request, pk):
    service = get_object_or_404(Service, pk=pk)
    action = request.POST.get("action")
    if action == "block":
        service.status = Service.Status.BLOCKED
        notify(service.provider, f"Xizmatingiz moderatsiya tomonidan bloklandi: {service.title}")
    elif action == "unblock":
        service.status = Service.Status.ACTIVE
        notify(service.provider, f"Xizmatingiz qayta faollashtirildi: {service.title}", service.get_absolute_url())
    service.save(update_fields=["status"])
    audit(request.user, f"service.{action}", service, request)
    return redirect(safe_back(request, request.POST.get("back"), "core:panel_services"))


# ----- PWA -----

def manifest(request):
    data = {
        "name": "BEGOYIM — Ayollar bandligi va farovonligi raqamli ekotizimi",
        "short_name": "BEGOYIM",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#fffaf5",
        "theme_color": "#8e1238",
        "lang": "uz",
        "icons": [
            {"src": static("begoyim/img/icon-192.png"), "sizes": "192x192", "type": "image/png"},
            {"src": static("begoyim/img/icon-512.png"), "sizes": "512x512", "type": "image/png"},
        ],
    }
    return JsonResponse(data, content_type="application/manifest+json")


def service_worker(request):
    js = render(request, "core/sw.js").content
    return HttpResponse(js, content_type="application/javascript")


def offline(request):
    return render(request, "core/offline.html")


def error_403(request, exception=None):
    return render(request, "core/error.html", {"code": 403, "title": "Ruxsat yo‘q", "text": str(exception or "") or "Bu sahifa sizning rolingiz uchun mavjud emas."}, status=403)


def error_404(request, exception=None):
    return render(request, "core/error.html", {"code": 404, "title": "Sahifa topilmadi", "text": "Siz izlagan sahifa mavjud emas."}, status=404)

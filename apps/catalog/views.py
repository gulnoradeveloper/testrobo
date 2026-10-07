from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.ai.matcher import smart_match
from apps.core.forms import ReportForm
from apps.core.permissions import role_required
from apps.core.services import audit

from . import services as svc
from .forms import OrderForm, ReviewForm, SearchForm, ServiceForm, SmartMatchForm
from .models import Category, Favorite, Order, Service, ServiceImage
from .search import search_services


def service_list(request):
    form = SearchForm(request.GET or None)
    qs = search_services(request.GET)
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "catalog/service_list.html", {
        "form": form, "page": page, "total": qs.count(), "querystring": params.urlencode(),
        "categories": Category.objects.filter(is_active=True),
        "active_category": request.GET.get("category", ""),
    })


def service_detail(request, pk):
    service = get_object_or_404(
        Service.objects.select_related("provider__profile", "category", "region", "district").prefetch_related("images"), pk=pk
    )
    is_owner = request.user.is_authenticated and request.user.pk == service.provider_id
    if service.status != Service.Status.ACTIVE and not is_owner and not (request.user.is_authenticated and request.user.is_admin_role):
        raise PermissionDenied("Bu xizmat hozir mavjud emas.")
    is_fav = request.user.is_authenticated and Favorite.objects.filter(user=request.user, service=service).exists()
    reviews = service.provider.reviews_received.filter(is_hidden=False).select_related("customer__profile")[:5]
    return render(request, "catalog/service_detail.html", {
        "s": service, "p": service.provider.profile, "is_owner": is_owner, "is_fav": is_fav,
        "order_form": OrderForm(service=service), "report_form": ReportForm(), "reviews": reviews,
        "similar": Service.objects.public().filter(category=service.category).exclude(pk=service.pk).select_related("provider__profile", "district")[:3],
    })


@role_required(User.Role.PROVIDER, allow_admin=False)
def service_create(request):
    return _service_form(request, Service(provider=request.user))


@role_required(User.Role.PROVIDER, allow_admin=False)
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk, provider=request.user)
    return _service_form(request, service)


def _service_form(request, service):
    profile = request.user.profile
    initial = {}
    if not service.pk:
        initial = {"region": profile.region_id, "district": profile.district_id}
    form = ServiceForm(request.POST or None, request.FILES or None, instance=service, initial=initial)
    if request.method == "POST" and form.is_valid():
        is_new = service.pk is None
        obj = form.save(commit=False)
        if obj.status != Service.Status.BLOCKED:
            obj.status = form.cleaned_data.get("status_choice") or Service.Status.ACTIVE
        obj.save()
        for img in form.cleaned_data.get("images") or []:
            ServiceImage.objects.create(service=obj, image=img)
        audit(request.user, "service.create" if is_new else "service.update", obj, request)
        messages.success(request, "Xizmat saqlandi." if not is_new else "Xizmat yaratildi va katalogda ko‘rinadi.")
        return redirect(obj)
    return render(request, "catalog/service_form.html", {"form": form, "service": service})


@role_required(User.Role.PROVIDER, allow_admin=False)
@require_POST
def service_image_delete(request, pk):
    img = get_object_or_404(ServiceImage, pk=pk, service__provider=request.user)
    service = img.service
    img.image.delete(save=False)
    img.delete()
    return redirect("catalog:service_edit", pk=service.pk)


@role_required(User.Role.PROVIDER, allow_admin=False)
def my_services(request):
    services = Service.objects.filter(provider=request.user).select_related("category", "district").prefetch_related("images")
    return render(request, "catalog/my_services.html", {"services": services})


@login_required
@require_POST
def favorite_toggle(request, pk):
    service = get_object_or_404(Service.objects.public(), pk=pk)
    fav, created = Favorite.objects.get_or_create(user=request.user, service=service)
    if not created:
        fav.delete()
        messages.info(request, "Sevimlilardan olib tashlandi.")
    else:
        messages.success(request, "Sevimlilarga saqlandi.")
    return redirect(service)


@login_required
def favorites(request):
    favs = Favorite.objects.filter(user=request.user, service__status=Service.Status.ACTIVE).select_related(
        "service__provider__profile", "service__district", "service__category"
    ).prefetch_related("service__images")
    return render(request, "catalog/favorites.html", {"favorites": favs})


# ----- Buyurtmalar -----

@login_required
@require_POST
def order_create(request, pk):
    service = get_object_or_404(Service.objects.public(), pk=pk)
    form = OrderForm(request.POST, service=service)
    if form.is_valid():
        d = form.cleaned_data
        try:
            order = svc.create_order(request.user, service, d["service_date"], d.get("price"), d["address_or_area"], d["comment"], request)
            messages.success(request, "Buyurtma yuborildi! Ijrochi javobini bildirishnomalarda kuzating.")
            return redirect(order)
        except (ValidationError, PermissionDenied) as e:
            messages.error(request, " ".join(getattr(e, "messages", [str(e)])))
    else:
        for errs in form.errors.values():
            messages.error(request, " ".join(errs))
    return redirect(service)


@login_required
def order_list(request):
    user = request.user
    tab = request.GET.get("tab") or ("received" if user.is_provider else "made")
    if tab == "received":
        qs = Order.objects.filter(provider=user)
    else:
        qs = Order.objects.filter(customer=user)
    status = request.GET.get("status")
    if status in Order.Status.values:
        qs = qs.filter(status=status)
    qs = qs.select_related("service", "customer__profile", "provider__profile")
    return render(request, "catalog/order_list.html", {
        "orders": qs, "tab": tab, "status": status, "statuses": Order.Status.choices,
    })


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related("service", "customer__profile", "provider__profile"), pk=pk)
    user = request.user
    if user.pk not in (order.customer_id, order.provider_id) and not user.is_admin_role:
        raise PermissionDenied("Bu buyurtma sizga tegishli emas.")
    can_review = user.pk == order.customer_id and order.status == Order.Status.COMPLETED and not hasattr(order, "review")
    S = Order.Status
    labels = {
        S.ACCEPTED: ("✓ Qabul qilish", "btn-main"),
        S.REJECTED: ("✕ Rad etish", "btn-danger-soft"),
        # BEGOYIM Safe: mijoz manzilidagi ishda vaqt qayd qilinadi
        S.IN_PROGRESS: ("▶ Ishni boshladim" if order.is_on_site else "▶ Jarayonda", "btn-main"),
        S.COMPLETED: ("■ Ishni yakunladim" if order.is_on_site else "✓ Bajarildi", "btn-main"),
        S.CANCELLED: ("Bekor qilish", "btn-danger-soft"),
    }
    actions = [(st, *labels[st]) for st in svc.allowed_transitions(order, user)]
    flow = [S.NEW, S.ACCEPTED, S.IN_PROGRESS, S.COMPLETED]
    reached = [h.to_status for h in order.history.all()]
    return render(request, "catalog/order_detail.html", {
        "o": order,
        "actions": actions,
        "flow": [(st.label, st in reached, st == order.status) for st in flow],
        "history": order.history.select_related("changed_by__profile"),
        "review_form": ReviewForm() if can_review else None,
        "is_provider": user.pk == order.provider_id,
        "S": Order.Status,
    })


@login_required
@require_POST
def order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    try:
        svc.change_order_status(order, request.user, request.POST.get("status"), request)
        messages.success(request, f"Buyurtma holati: {order.get_status_display()}")
    except PermissionDenied as e:
        messages.error(request, str(e))
    return redirect(order)


@login_required
@require_POST
def review_create(request, pk):
    order = get_object_or_404(Order, pk=pk)
    form = ReviewForm(request.POST)
    if form.is_valid():
        d = form.cleaned_data
        try:
            svc.create_review(order, request.user, d["rating"], d["quality_rating"], d["communication_rating"],
                              d["punctuality_rating"], d["comment"], request)
            messages.success(request, "Rahmat! Bahoyingiz saqlandi.")
        except (ValidationError, PermissionDenied) as e:
            messages.error(request, " ".join(getattr(e, "messages", [str(e)])))
    else:
        messages.error(request, "Barcha baholarni belgilang.")
    return redirect(order)


@role_required(User.Role.PROVIDER, allow_admin=False)
def income_dashboard(request):
    stats = svc.provider_dashboard(request.user)
    recent = Order.objects.filter(provider=request.user).select_related("service", "customer__profile")[:8]
    return render(request, "catalog/income_dashboard.html", {"stats": stats, "recent": recent})


def smart_match_view(request):
    form = SmartMatchForm(request.GET or None)
    result = None
    if form.is_valid():
        result = smart_match(form.cleaned_data["text"], user=request.user)
    examples = [
        "Ertaga Buxoro shahrida 2 ta xonani tozalaydigan ayol kerak.",
        "Buxoroda parda tikib beradigan usta kerak",
        "Toshkentda to‘yga 200 ta somsa tayyorlab beradigan pazanda",
        "Farzandimga masofadan ingliz tili repetitori kerak",
    ]
    return render(request, "catalog/smart_match.html", {"form": form, "result": result, "examples": examples})


def category_redirect(request, slug):
    get_object_or_404(Category, slug=slug, is_active=True)
    return redirect(f"{reverse('catalog:service_list')}?category={slug}")


"""BEGOYIM REST API. Har bir endpoint rolga asoslangan ruxsat bilan himoyalangan."""
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import VerificationRequest
from apps.accounts.services import decide_verification, submit_verification
from apps.ai.matcher import smart_match
from apps.catalog import services as svc
from apps.catalog.models import Category, Order, Review, Service
from apps.catalog.search import search_services
from apps.core.models import District, Mahalla, Region, Report
from apps.core.services import audit, notify
from apps.psychology.models import Consultation, Psychologist

from . import serializers as s
from .permissions import CanOrder, IsAdminRole, IsMahalla, IsProvider


def _django_errors(fn):
    """Domen qatlamidagi Django xatolarini DRF xatolariga aylantirish."""
    try:
        return fn()
    except DjangoPermissionDenied as e:
        raise PermissionDenied(str(e) or None)
    except DjangoValidationError as e:
        raise ValidationError(e.messages)


# ----- Auth -----

class RegisterView(generics.CreateAPIView):
    serializer_class = s.RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def perform_create(self, serializer):
        user = serializer.save()
        audit(user, "auth.register", user, self.request, role=user.role, channel="api")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user = serializer.instance
        return Response({"id": user.pk, "phone": user.phone, "role": user.role}, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """phone + password -> JWT (access, refresh)."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


# ----- Profil -----

@api_view(["GET"])
def profile(request):
    return Response(s.ProfileSerializer(request.user.profile).data)


@api_view(["PATCH", "PUT"])
def profile_update(request):
    ser = s.ProfileSerializer(request.user.profile, data=request.data, partial=True)
    ser.is_valid(raise_exception=True)
    ser.save()
    audit(request.user, "profile.update", request.user.profile, request, channel="api")
    return Response(ser.data)


# ----- Ma'lumotnomalar -----

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = s.CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None


@api_view(["GET"])
@permission_classes([AllowAny])
def regions(request):
    return Response(s.RegionSerializer(Region.objects.all(), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def districts(request):
    qs = District.objects.filter(region_id=request.GET.get("region") or 0)
    return Response(s.DistrictSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def mahallas(request):
    qs = Mahalla.objects.filter(district_id=request.GET.get("district") or 0)
    return Response(s.MahallaSerializer(qs, many=True).data)


# ----- Xizmatlar -----

class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = s.ServiceSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsProvider()]

    def get_queryset(self):
        qs = Service.objects.select_related("provider__profile").prefetch_related("images")
        user = self.request.user
        if self.action in ("list", "retrieve"):
            visible = Q(status=Service.Status.ACTIVE, provider__is_active=True)
            if user.is_authenticated:
                visible |= Q(provider=user)
            return qs.filter(visible)
        return qs.filter(provider=user)

    def perform_create(self, serializer):
        obj = serializer.save(provider=self.request.user)
        audit(self.request.user, "service.create", obj, self.request, channel="api")

    def perform_update(self, serializer):
        obj = serializer.save()
        audit(self.request.user, "service.update", obj, self.request, channel="api")


@api_view(["GET"])
@permission_classes([AllowAny])
def search(request):
    qs = search_services(request.GET)
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(s.ServiceSerializer(page, many=True, context={"request": request}).data)


class AIMatchView(APIView):
    """Tabiiy tildagi so'rov -> Top 3–5 mos xizmat (faqat bazada mavjudlari)."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai"

    def post(self, request):
        text = str(request.data.get("text", ""))[:500]
        result = smart_match(text, user=request.user)
        return Response({
            "parsed": result["parsed"],
            "matches": [m.as_dict() for m in result["matches"]],
            "message": result["message"],
            "formula": "MatchScore = xizmat mosligi(40) + hudud mosligi(25) + reyting(15) + verifikatsiya(10) + mavjudlik(10)",
        })


# ----- Buyurtmalar -----

class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = s.OrderSerializer

    def get_permissions(self):
        if self.action == "create":
            return [CanOrder()]
        return [IsAuthenticated()]

    def get_queryset(self):
        u = self.request.user
        qs = Order.objects.select_related("service", "customer__profile", "provider__profile")
        if u.is_admin_role:
            return qs
        role = self.request.GET.get("as")
        if role == "provider":
            return qs.filter(provider=u)
        if role == "customer":
            return qs.filter(customer=u)
        return qs.filter(Q(provider=u) | Q(customer=u))

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        service = get_object_or_404(Service.objects.public(), pk=d["service"].pk)
        order = _django_errors(lambda: svc.create_order(
            request.user, service, d["service_date"], d.get("price"), d.get("address_or_area", ""), d.get("comment", ""), request
        ))
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def status(self, request, pk=None):
        order = self.get_object()
        ser = s.OrderStatusSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        _django_errors(lambda: svc.change_order_status(order, request.user, ser.validated_data["status"], request))
        return Response(self.get_serializer(order).data)


class ReviewViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = s.ReviewSerializer

    def get_permissions(self):
        return [AllowAny()] if self.action == "list" else [IsAuthenticated()]

    def get_queryset(self):
        qs = Review.objects.filter(is_hidden=False).select_related("customer__profile")
        provider = self.request.GET.get("provider")
        return qs.filter(provider_id=provider) if provider else qs

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        review = _django_errors(lambda: svc.create_review(
            d["order"], request.user, d["rating"], d["quality_rating"], d["communication_rating"],
            d["punctuality_rating"], d.get("comment", ""), request
        ))
        return Response(self.get_serializer(review).data, status=status.HTTP_201_CREATED)


# ----- Verifikatsiya -----

class VerificationViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Ijrochi: o'z arizalari va yangi ariza. Mahalla vakili: faqat o'z mahallasidagi arizalar."""

    serializer_class = s.VerificationRequestSerializer

    def get_queryset(self):
        u = self.request.user
        qs = VerificationRequest.objects.select_related("user__profile")
        if u.is_admin_role:
            return qs
        if u.is_mahalla:
            return qs.filter(mahalla_id=getattr(u.profile, "mahalla_id", None) or 0)
        return qs.filter(user=u)

    def create(self, request, *args, **kwargs):
        vr = _django_errors(lambda: submit_verification(request.user, str(request.data.get("note", ""))[:1000], request))
        return Response(self.get_serializer(vr).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsMahalla | IsAdminRole])
    def decide(self, request, pk=None):
        vr = self.get_object()
        ser = s.VerificationDecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        _django_errors(lambda: decide_verification(request.user, vr, ser.validated_data["decision"], ser.validated_data.get("comment", ""), request))
        return Response(self.get_serializer(vr).data)


# ----- Psixologik yordam -----

class PsychologistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Psychologist.objects.filter(is_approved=True, user__is_active=True).select_related("user__profile")
    serializer_class = s.PsychologistSerializer
    permission_classes = [AllowAny]


class ConsultationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """MAXFIY: faqat mijozning o'zi yoki tegishli psixolog ko'radi. Admin va mahalla vakiliga ham yopiq."""

    serializer_class = s.ConsultationSerializer

    def get_queryset(self):
        u = self.request.user
        return Consultation.objects.filter(Q(client=u) | Q(psychologist__user=u)).select_related("psychologist__user__profile")

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        p, slot = d["psychologist"], d.get("slot")
        if not p.is_approved or p.user_id == request.user.pk:
            raise ValidationError("Bu mutaxassisga yozilib bo‘lmaydi.")
        if not p.supports(d["format"]):
            raise ValidationError("Mutaxassis bu shaklda qabul qilmaydi.")
        with transaction.atomic():
            if slot is None or slot.psychologist_id != p.pk:
                raise ValidationError("Bo‘sh vaqtni tanlang.")
            slot = type(slot).objects.select_for_update().get(pk=slot.pk)
            if slot.is_booked or slot.start_at <= timezone.now():
                raise ValidationError("Bu vaqt band yoki o‘tib ketgan.")
            c = ser.save(client=request.user)
            slot.is_booked = True
            slot.save(update_fields=["is_booked"])
        notify(p.user, "Yangi konsultatsiya so‘rovi keldi.", "/psixologik-yordam/kabinet/")
        return Response(self.get_serializer(c).data, status=status.HTTP_201_CREATED)


# ----- Bildirishnomalar -----

class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = s.NotificationSerializer

    def get_queryset(self):
        return self.request.user.notifications.all()

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        n = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"updated": n})


# ----- Shikoyatlar -----

class ReportViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = s.ReportSerializer

    def get_queryset(self):
        u = self.request.user
        return Report.objects.all() if u.is_admin_role else Report.objects.filter(reporter=u)

    def perform_create(self, serializer):
        report = serializer.save(reporter=self.request.user)
        audit(self.request.user, "report.create", report, self.request, channel="api")

    def update(self, request, *args, **kwargs):
        if not request.user.is_admin_role:
            raise PermissionDenied("Shikoyat holatini faqat administrator o‘zgartiradi.")
        report = self.get_object()
        new_status = request.data.get("status")
        if new_status not in Report.Status.values:
            raise ValidationError({"status": "NEW, REVIEWING yoki RESOLVED"})
        report.status = new_status
        report.admin_note = str(request.data.get("admin_note", report.admin_note))[:2000]
        report.save()
        audit(request.user, "report.status", report, request, status=new_status)
        return Response(self.get_serializer(report).data)


# ----- Dashboardlar -----

@api_view(["GET"])
@permission_classes([IsProvider])
def dashboard_provider(request):
    return Response(svc.provider_dashboard(request.user))


@api_view(["GET"])
@permission_classes([IsMahalla])
def dashboard_mahalla(request):
    mahalla = request.user.profile.mahalla
    if mahalla is None:
        raise PermissionDenied("Mahalla biriktirilmagan.")
    data = svc.mahalla_dashboard(mahalla)
    data["mahalla"] = str(mahalla)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAdminRole])
def dashboard_admin(request):
    return Response(svc.admin_dashboard())

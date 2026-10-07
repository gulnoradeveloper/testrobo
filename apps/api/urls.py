from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter(trailing_slash="/?")
router.register("categories", views.CategoryViewSet, basename="categories")
router.register("services", views.ServiceViewSet, basename="services")
router.register("orders", views.OrderViewSet, basename="orders")
router.register("reviews", views.ReviewViewSet, basename="reviews")
router.register("verification", views.VerificationViewSet, basename="verification")
router.register("psychologists", views.PsychologistViewSet, basename="psychologists")
router.register("consultations", views.ConsultationViewSet, basename="consultations")
router.register("notifications", views.NotificationViewSet, basename="notifications")
router.register("reports", views.ReportViewSet, basename="reports")

urlpatterns = [
    path("auth/register", views.RegisterView.as_view(), name="api-register"),
    path("auth/login", views.LoginView.as_view(), name="api-login"),
    path("auth/refresh", TokenRefreshView.as_view(), name="api-refresh"),
    path("profile", views.profile, name="api-profile"),
    path("profile/update", views.profile_update, name="api-profile-update"),
    path("regions", views.regions, name="api-regions"),
    path("districts", views.districts, name="api-districts"),
    path("mahallas", views.mahallas, name="api-mahallas"),
    path("search", views.search, name="api-search"),
    path("ai/match", views.AIMatchView.as_view(), name="api-ai-match"),
    path("dashboard/provider", views.dashboard_provider, name="api-dashboard-provider"),
    path("dashboard/mahalla", views.dashboard_mahalla, name="api-dashboard-mahalla"),
    path("dashboard/admin", views.dashboard_admin, name="api-dashboard-admin"),
    path("", include(router.urls)),
]

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("qanday-ishlaydi/", views.how_it_works, name="how_it_works"),
    path("bildirishnomalar/", views.notifications, name="notifications"),
    path("bildirishnomalar/<int:pk>/", views.notification_open, name="notification_open"),
    path("bildirishnomalar/hammasi-oqildi/", views.notifications_read_all, name="notifications_read_all"),
    path("shikoyat/", views.report_create, name="report_create"),
    path("ajax/tumanlar/", views.districts_json, name="districts_json"),
    path("ajax/mahallalar/", views.mahallas_json, name="mahallas_json"),
    path("panel/", views.panel_home, name="panel_home"),
    path("panel/shikoyatlar/", views.panel_reports, name="panel_reports"),
    path("panel/shikoyatlar/<int:pk>/", views.panel_report_update, name="panel_report_update"),
    path("panel/xizmatlar/", views.panel_services, name="panel_services"),
    path("panel/xizmatlar/<int:pk>/", views.panel_service_moderate, name="panel_service_moderate"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="sw"),
    path("offline/", views.offline, name="offline"),
]

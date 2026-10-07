from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "BEGOYIM — Boshqaruv paneli"
admin.site.site_title = "BEGOYIM admin"
admin.site.index_title = "Tizim boshqaruvi"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.api.urls")),
    path("psixologik-yordam/", include("apps.psychology.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.core.urls")),
]

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

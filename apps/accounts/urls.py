from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("royxatdan-otish/", views.register, name="register"),
    path("kirish/", views.login_view, name="login"),
    path("chiqish/", views.logout_view, name="logout"),
    path("profil/", views.my_profile, name="profile"),
    path("profil/tahrirlash/", views.profile_edit, name="profile_edit"),
    path("profil/portfolio/<int:pk>/ochirish/", views.portfolio_delete, name="portfolio_delete"),
    path("profil/verifikatsiya/", views.verification_submit, name="verification_submit"),
    path("ijrochi/<int:pk>/", views.public_profile, name="public_profile"),
    path("mahalla/", views.mahalla_home, name="mahalla_home"),
    path("mahalla/arizalar/", views.mahalla_verifications, name="mahalla_verifications"),
    path("mahalla/arizalar/<int:pk>/", views.mahalla_verification_detail, name="mahalla_verification_detail"),
]

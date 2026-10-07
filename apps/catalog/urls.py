from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("xizmatlar/", views.service_list, name="service_list"),
    path("xizmatlar/yangi/", views.service_create, name="service_create"),
    path("xizmatlar/<int:pk>/", views.service_detail, name="service_detail"),
    path("xizmatlar/<int:pk>/tahrirlash/", views.service_edit, name="service_edit"),
    path("xizmatlar/<int:pk>/sevimli/", views.favorite_toggle, name="favorite_toggle"),
    path("xizmatlar/<int:pk>/buyurtma/", views.order_create, name="order_create"),
    path("xizmatlar/rasm/<int:pk>/ochirish/", views.service_image_delete, name="service_image_delete"),
    path("kategoriya/<slug:slug>/", views.category_redirect, name="category"),
    path("mening-xizmatlarim/", views.my_services, name="my_services"),
    path("sevimlilar/", views.favorites, name="favorites"),
    path("buyurtmalar/", views.order_list, name="order_list"),
    path("buyurtmalar/<int:pk>/", views.order_detail, name="order_detail"),
    path("buyurtmalar/<int:pk>/holat/", views.order_status, name="order_status"),
    path("buyurtmalar/<int:pk>/baho/", views.review_create, name="review_create"),
    path("daromad/", views.income_dashboard, name="income_dashboard"),
    path("ai-tavsiya/", views.smart_match_view, name="smart_match"),
]

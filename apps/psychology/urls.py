from django.urls import path

from . import views

app_name = "psychology"

urlpatterns = [
    path("", views.psychologist_list, name="list"),
    path("mutaxassis/<int:pk>/", views.psychologist_detail, name="detail"),
    path("murojaatlarim/", views.my_consultations, name="my_consultations"),
    path("kabinet/", views.cabinet, name="cabinet"),
    path("kabinet/vaqt/<int:pk>/ochirish/", views.slot_delete, name="slot_delete"),
    path("konsultatsiya/<int:pk>/<str:action>/", views.consultation_action, name="consultation_action"),
]

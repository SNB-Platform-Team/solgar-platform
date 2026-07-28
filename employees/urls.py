"""employees app — URL routes."""

from django.urls import path

from . import views

app_name = "employees"

urlpatterns = [
    path("", views.employee_list_view, name="list"),
    path("<int:pk>/", views.employee_detail_view, name="detail"),
]
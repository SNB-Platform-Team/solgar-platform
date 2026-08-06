"""sales app — URL routes."""

from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("upload/", views.sales_upload_view, name="upload"),
    path("report/", views.sales_report_view, name="report"),
]
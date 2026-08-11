"""sales app — URL routes."""

from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("upload/", views.sales_upload_view, name="upload"),
    path("report/", views.sales_report_view, name="report"),
    path("export/", views.sales_export_view, name="export"),
    path("chain-report/", views.sales_chain_report_view, name="chain_report"),
    path("distributor/report/", views.distributor_report_view, name="distributor_report"),
]
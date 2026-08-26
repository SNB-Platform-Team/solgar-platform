"""sales app — URL routes."""

from django.urls import path

from . import views

from . import api

app_name = "sales"

urlpatterns = [
    path("upload/", views.sales_upload_view, name="upload"),
    path("report/", views.sales_report_view, name="report"),
    path("export/", views.sales_export_view, name="export"),
    path("chain-report/", views.sales_chain_report_view, name="chain_report"),
    path("chain-report/options/", views.chain_filter_options_json, name="chain_filter_options"),
    path("distributor/upload/", views.distributor_upload_view, name="distributor_upload"),
    path("distributor/report/", views.distributor_report_view, name="distributor_report"),
    path("doctor/address-options/", views.doctor_address_options_json, name="doctor_address_options"),
    path("doctor/", views.doctor_entry_view, name="doctor_entry"),
    path("pharmacy/", views.pharmacy_entry_view, name="pharmacy_entry"),
    path("pharmacy/options/", views.pharmacy_options_json, name="pharmacy_options"),
    path("report-obs/", views.sales_report_obs_view, name="sales_report_obs"),
    path("1c-stock/", views.onec_stock_view, name="onec_stock"),
    path("pharm-managerial/", views.pharm_managerial_view, name="pharm_managerial"),
    path("doctor-managerial/", views.doctor_managerial_view, name="doctor_managerial"),
    path("api/onec/", api.onec_api, name="onec_api"),
    path("onec-react/", views.onec_react_view, name="onec_react"),
    path("api/doctor-managerial/", api.doctor_managerial_api, name="doctor_managerial_api"),
    path("api/pharm-managerial/", api.pharm_managerial_api, name="pharm_managerial_api"),
]
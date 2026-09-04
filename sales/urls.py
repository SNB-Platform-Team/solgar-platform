"""sales app — URL routes."""

from django.urls import path

from . import views

from . import api

app_name = "sales"

#profile
#employees

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
    path("api/pharmacy/", api.pharmacy_api, name="pharmacy_api"),
    path("api/pharmacy/filter-options/", api.pharmacy_filter_options_api, name="pharmacy_filter_options_api"),
    path("api/doctor/", api.doctor_api, name="doctor_api"),
    path("api/chain-report/", api.chain_report_api, name="chain_report_api"),  
    path("api/sales-obs/", api.sales_obs_api, name="sales_obs_api"),   
    path("api/dashboard/", api.dashboard_api, name="dashboard_api"), 
    path("api/dashboard/", api.dashboard_api, name="dashboard_api"),
    path("api/sales-obs/", api.sales_obs_api, name="sales_obs_api"), #
    path("api/faq/", api.faq_api, name="faq_api"),
    path("api/sales-upload/options/", api.sales_upload_options_api, name="sales_upload_options_api"),
    path("api/sales-upload/preview/", api.sales_upload_preview_api, name="sales_upload_preview_api"),
    path("api/sales-upload/save/", api.sales_upload_save_api, name="sales_upload_save_api"),
    path("api/csrf/", api.csrf_api, name="csrf_api"),
    path("api/distributor-upload/options/", api.distributor_upload_options_api, name="distributor_upload_options_api"),
    path("api/distributor-upload/preview/", api.distributor_upload_preview_api, name="distributor_upload_preview_api"),
    path("api/distributor-upload/save/", api.distributor_upload_save_api, name="distributor_upload_save_api"),
    path("api/doctor/filter-options/", api.doctor_filter_options_api, name="doctor_filter_options_api"),
    path("api/me/", api.me_api, name="_me_api"), 
    path("api/chain-report/filter-options/",api.chain_report_filter_options_api , name="chain_report_filter_options_api"),
    path("api/sales-obs/filter-options/", api.sales_obs_filter_options_api, name="sales_obs_filter_options_api"),
    path("api/profile/", api.profile_api, name="profile_api"),    
    path("api/employees/", api.employees_api, name="employees_api"),  
    path("api/country-options/", api.country_options_api, name="country_options_api"),    
    path("api/storage-options/", api.storage_options_api, name="storage_options_api"),
    path("api/depo-upload/preview/", api.depo_upload_preview_api, name="depo_upload_preview_api"),        
    path("api/depo-upload/save/", api.depo_upload_save_api, name="depo_upload_save_api"),
]      




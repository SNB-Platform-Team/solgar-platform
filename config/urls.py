"""Root URL configuration for the Solgar internal platform."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("employees/", include("employees.urls")),
    path("", include("accounts.urls")),
]
"""accounts app — URL routes, namespaced under 'accounts'."""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("login/azure/", views.azure_login_view, name="azure_login"),
    path("logout/", views.logout_view, name="logout"),
]
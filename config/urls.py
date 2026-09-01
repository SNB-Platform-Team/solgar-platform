"""Root URL configuration for the Solgar internal platform."""
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

# React SPA giris noktasi (templates/index.html -> React build).
react_app = TemplateView.as_view(template_name="index.html")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("employees/", include("employees.urls")),
    path("approvals/", include("approvals.urls")),
    path("sales/", include("sales.urls")),
    # accounts: login/, logout/, login/azure/, faq/ Django auth path'leri.
    # accounts.urls icindeki kok ("") home_view'i de tanimli ama React
    # catch-all'u kok "/" yi yakalayacagi icin pratikte React acilir.
    path("", include("accounts.urls")),
    # React SPA catch-all: Django'nun bilinen prefix'leri DISINDAKI
    # tum path'ler React'e (React Router client-side halleder).
    re_path(
        r"^(?!admin/|sales/|employees/|approvals/|login/|logout/|static/|media/|faq/).*$",
        react_app,
        name="react_catchall",
    ),
]



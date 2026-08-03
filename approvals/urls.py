"""approvals app — URL routes."""

from django.urls import path

from . import views

app_name = "approvals"

urlpatterns = [
    path("", views.my_requests_view, name="my_requests"),
    path("new/", views.create_request_view, name="create"),
    path("inbox/", views.approval_inbox_view, name="inbox"),
    path("<int:pk>/approve/", views.approve_view, name="approve"),
    path("<int:pk>/reject/", views.reject_view, name="reject"),
]
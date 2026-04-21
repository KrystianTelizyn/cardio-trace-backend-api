from django.urls import path

from accounts.views import UserProvisionView

urlpatterns = [
    path("users", UserProvisionView.as_view(), name="user-provision"),
]

from django.urls import path

from accounts.views import ProfileUpdateView, UserProvisionView

urlpatterns = [
    path("users", UserProvisionView.as_view(), name="user-provision"),
    path("me/profile", ProfileUpdateView.as_view(), name="profile-update"),
]

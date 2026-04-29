from django.urls import path

from devices.views import (
    AssignDeviceView,
    DeviceAssignmentDeleteView,
    DeviceCreateView,
)

urlpatterns = [
    path("devices", DeviceCreateView.as_view(), name="device-create"),
    path(
        "device-assignments",
        AssignDeviceView.as_view(),
        name="device-assignment-create",
    ),
    path(
        "device-assignments/<int:assignment_id>",
        DeviceAssignmentDeleteView.as_view(),
        name="device-assignment-delete",
    ),
]

from django.urls import path

from devices.views import (
    AssignDeviceView,
    DeviceAssignmentStopView,
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
        DeviceAssignmentStopView.as_view(),
        name="device-assignment-stop",
    ),
]

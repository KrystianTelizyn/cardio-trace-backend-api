from django.urls import path

from measurements.views import MeasurementIngestView, MeasurementSessionStartView

urlpatterns = [
    path("measurements", MeasurementIngestView.as_view(), name="measurement-ingest"),
    path(
        "measurement-sessions",
        MeasurementSessionStartView.as_view(),
        name="measurement-session-start",
    ),
]

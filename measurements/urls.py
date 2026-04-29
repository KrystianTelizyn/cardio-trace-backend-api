from django.urls import path

from measurements.views import MeasurementIngestView

urlpatterns = [
    path("measurements", MeasurementIngestView.as_view(), name="measurement-ingest"),
]

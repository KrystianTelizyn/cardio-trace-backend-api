from django.urls import path

from measurements.views import (
    IngestionEnrichView,
    MeasurementIngestView,
    MeasurementSessionStartView,
    MeasurementSessionStopView,
)

urlpatterns = [
    path("ingestion/enrich", IngestionEnrichView.as_view(), name="ingestion-enrich"),
    path("measurements", MeasurementIngestView.as_view(), name="measurement-ingest"),
    path(
        "measurement-sessions",
        MeasurementSessionStartView.as_view(),
        name="measurement-session-start",
    ),
    path(
        "measurement-sessions/<str:session_id>",
        MeasurementSessionStopView.as_view(),
        name="measurement-session-stop",
    ),
]

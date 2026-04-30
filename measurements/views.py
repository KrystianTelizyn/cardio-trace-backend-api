from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from measurements.serializers import (
    MeasurementIngestInputSerializer,
    MeasurementIngestOutputSerializer,
)
from measurements.use_cases import IngestMeasurement
from config.authentication import InternalTenantAuthentication


class MeasurementIngestView(APIView):
    authentication_classes = [InternalTenantAuthentication]
    permission_classes = []

    def post(self, request: Request) -> Response:
        serializer = MeasurementIngestInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        tenant = request.auth["tenant"]
        measurement = IngestMeasurement().execute(
            measurement_session_id=validated_data["measurement_session_id"],
            tenant=tenant,
            timestamp=validated_data["timestamp"],
            heart_rate=validated_data["heart_rate"],
            hrv=validated_data["hrv"],
        )
        output = MeasurementIngestOutputSerializer(measurement)
        return Response(output.data, status=status.HTTP_201_CREATED)

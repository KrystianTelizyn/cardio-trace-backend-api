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

        tenant = request.auth["tenant"]
        measurement = IngestMeasurement().execute(
            tenant=tenant, **serializer.validated_data
        )
        output = MeasurementIngestOutputSerializer(measurement)
        return Response(output.data, status=status.HTTP_201_CREATED)

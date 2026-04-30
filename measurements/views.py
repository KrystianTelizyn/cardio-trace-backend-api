from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.authentication import GatewayAuthentication, InternalTenantAuthentication
from measurements.serializers import (
    MeasurementIngestInputSerializer,
    MeasurementIngestOutputSerializer,
    MeasurementSessionStopInputSerializer,
    MeasurementSessionStopOutputSerializer,
    MeasurementSessionStartOutputSerializer,
    MeasurementSessionStartInputSerializer,
)
from measurements.use_cases import (
    IngestMeasurement,
    StartMeasurementSession,
    StopMeasurementSession,
)


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


class MeasurementSessionStartView(APIView):
    authentication_classes = [GatewayAuthentication]
    permission_classes = []

    def post(self, request: Request) -> Response:
        serializer = MeasurementSessionStartInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        measurement_session = StartMeasurementSession().execute(
            device_assignment_id=serializer.validated_data["device_assignment_id"],
            tenant=request.user.tenant,
            started_at=serializer.validated_data.get("started_at"),
        )
        output = MeasurementSessionStartOutputSerializer(measurement_session)
        return Response(output.data, status=status.HTTP_201_CREATED)


class MeasurementSessionStopView(APIView):
    authentication_classes = [GatewayAuthentication]
    permission_classes = []

    def patch(self, request: Request, session_id: str) -> Response:
        serializer = MeasurementSessionStopInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        measurement_session = StopMeasurementSession().execute(
            measurement_session_id=session_id,
            tenant=request.user.tenant,
            stopped_at=serializer.validated_data.get("stopped_at"),
        )
        output = MeasurementSessionStopOutputSerializer(measurement_session)
        return Response(output.data, status=status.HTTP_200_OK)

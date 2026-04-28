# Create your views here.
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from devices.serializers import (
    DeviceCreateInputSerializer,
    DeviceCreateOutputSerializer,
)
from devices.use_cases import CreateDevice
from config.authentication import GatewayAuthentication


class DeviceCreateView(APIView):
    authentication_classes = [GatewayAuthentication]
    permission_classes = []

    def post(self, request: Request) -> Response:
        serializer = DeviceCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        use_case = CreateDevice()
        device = use_case.execute(
            **serializer.validated_data, tenant=request.user.tenant
        )
        return Response(
            DeviceCreateOutputSerializer(device).data, status=status.HTTP_201_CREATED
        )

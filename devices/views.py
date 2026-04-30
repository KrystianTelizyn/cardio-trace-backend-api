# Create your views here.
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from devices.serializers import (
    DeviceCreateInputSerializer,
    DeviceCreateOutputSerializer,
    DeviceAssignmentInputSerializer,
    DeviceAssignmentOutputSerializer,
    DeviceAssignmentStopInputSerializer,
)
from devices.use_cases import (
    CreateDevice,
    AssignDevice,
    StopDeviceAssignment,
)
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


class AssignDeviceView(APIView):
    authentication_classes = [GatewayAuthentication]
    permission_classes = []

    def post(self, request: Request) -> Response:
        serializer = DeviceAssignmentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        use_case = AssignDevice()
        device_assignment = use_case.execute(
            **serializer.validated_data,
            doctor_profile=request.user.doctor_profile,
            tenant=request.user.tenant,
        )
        return Response(
            DeviceAssignmentOutputSerializer(device_assignment).data,
            status=status.HTTP_201_CREATED,
        )


class DeviceAssignmentStopView(APIView):
    authentication_classes = [GatewayAuthentication]
    permission_classes = []

    def patch(self, request: Request, assignment_id: int) -> Response:
        serializer = DeviceAssignmentStopInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = StopDeviceAssignment()
        assignment = use_case.execute(
            assignment_id=assignment_id,
            tenant=request.user.tenant,
            unassigned_at=serializer.validated_data.get("unassigned_at"),
        )
        return Response(DeviceAssignmentOutputSerializer(assignment).data)

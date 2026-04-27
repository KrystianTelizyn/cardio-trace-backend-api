from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.serializers import (
    DoctorProfileSerializer,
    DoctorProfileUpdateInputSerializer,
    PatientProfileSerializer,
    PatientProfileUpdateInputSerializer,
    UserProvisionInputSerializer,
    UserProvisionOutputSerializer,
)
from accounts.use_cases import ProvisionUser, UpdateProfile
from config.authentication import GatewayAuthentication


class UserProvisionView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> Response:
        serializer = UserProvisionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, created = ProvisionUser().execute(**serializer.validated_data)

        output = UserProvisionOutputSerializer(user)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(output.data, status=status_code)


class ProfileUpdateView(APIView):
    authentication_classes = [GatewayAuthentication]
    permission_classes = []

    def patch(self, request: Request) -> Response:
        if request.auth.get("role", "") == User.Role.DOCTOR:
            serializer = DoctorProfileUpdateInputSerializer(data=request.data)
            output_serializer = DoctorProfileSerializer
        else:
            serializer = PatientProfileUpdateInputSerializer(data=request.data)
            output_serializer = PatientProfileSerializer

        serializer.is_valid(raise_exception=True)

        profile = UpdateProfile().execute(
            user=request.user, **serializer.validated_data
        )
        output = output_serializer(profile)
        return Response(output.data, status=status.HTTP_200_OK)

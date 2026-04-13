from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import (
    UserProvisionInputSerializer,
    UserProvisionOutputSerializer,
)
from accounts.use_cases import ProvisionUser


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

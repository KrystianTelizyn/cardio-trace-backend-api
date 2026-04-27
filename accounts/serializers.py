from rest_framework import serializers
from accounts.models import User


class UserProvisionInputSerializer(serializers.Serializer):
    auth0_user_id = serializers.CharField()
    auth0_org_id = serializers.CharField()
    role = serializers.ChoiceField(choices=User.Role.choices)
    email = serializers.EmailField()
    name = serializers.CharField(required=False, default="")


class DoctorProfileUpdateInputSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    surname = serializers.CharField(required=False)
    specialization = serializers.CharField(required=False)
    license_number = serializers.CharField(required=False)


class PatientProfileUpdateInputSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    surname = serializers.CharField(required=False)
    dob = serializers.DateField(required=False)
    gender = serializers.CharField(required=False)
    medical_id = serializers.CharField(required=False)


class DoctorProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    surname = serializers.CharField()
    specialization = serializers.CharField()
    license_number = serializers.CharField()


class PatientProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    surname = serializers.CharField()
    dob = serializers.DateField()
    gender = serializers.CharField()
    medical_id = serializers.CharField()


class UserProvisionOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    auth0_user_id = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()
    profile = serializers.SerializerMethodField()

    def get_profile(self, user: User) -> dict:
        if user.role == User.Role.DOCTOR:
            return DoctorProfileSerializer(user.doctor_profile).data
        return PatientProfileSerializer(user.patient_profile).data

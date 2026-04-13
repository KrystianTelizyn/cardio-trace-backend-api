from rest_framework import serializers

from accounts.models import User


# --- Input ---


class UserProvisionInputSerializer(serializers.Serializer):
    auth0_user_id = serializers.CharField()
    auth0_org_id = serializers.CharField()
    role = serializers.ChoiceField(choices=User.Role.choices)
    email = serializers.EmailField()
    name = serializers.CharField(required=False, default="")


# --- Nested profile outputs (reused across endpoints) ---


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


# --- Output ---


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

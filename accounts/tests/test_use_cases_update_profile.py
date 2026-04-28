import datetime

from django.test import TestCase

from accounts.use_cases import UpdateProfile
from tests.mixins import TenantUsersMixin


class UpdateProfileUseCaseTests(TenantUsersMixin, TestCase):
    tenant_auth0_organization_id = "org_profile_test"
    tenant_name = "Profile Clinic"
    doctor_auth0_user_id = "auth0|profile_doc"
    doctor_email = "profiledoc@example.com"
    patient_auth0_user_id = "auth0|profile_pat"
    patient_email = "profilepat@example.com"
    doctor_profile_name = "Doc"
    patient_profile_name = "Pat"

    def test_updates_doctor_fields(self) -> None:
        profile = UpdateProfile().execute(
            user=self.doctor_user,
            name="Updated",
            surname="Smith",
            specialization="Cardiology",
            license_number="LIC-001",
        )

        self.assertEqual(profile.name, "Updated")
        self.assertEqual(profile.surname, "Smith")
        self.assertEqual(profile.specialization, "Cardiology")
        self.assertEqual(profile.license_number, "LIC-001")

    def test_updates_patient_fields(self) -> None:
        profile = UpdateProfile().execute(
            user=self.patient_user,
            name="Updated Pat",
            surname="Jones",
            dob=datetime.date(1990, 5, 15),
            gender="male",
            medical_id="MED-123",
        )

        self.assertEqual(profile.name, "Updated Pat")
        self.assertEqual(profile.surname, "Jones")
        self.assertEqual(profile.dob, datetime.date(1990, 5, 15))
        self.assertEqual(profile.gender, "male")
        self.assertEqual(profile.medical_id, "MED-123")

    def test_noop_when_no_fields_provided(self) -> None:
        profile = UpdateProfile().execute(user=self.doctor_user)
        self.assertEqual(profile.name, "Doc")

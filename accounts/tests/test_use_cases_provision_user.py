from django.test import TestCase

from accounts.exceptions import TenantNotFound
from accounts.models import User
from accounts.use_cases import ProvisionUser
from tests.mixins import TenantUsersMixin


class ProvisionUserUseCaseTests(TenantUsersMixin, TestCase):
    tenant_auth0_organization_id = "org_test123"
    tenant_name = "Test Clinic"

    def test_creates_doctor_with_profile(self) -> None:
        user, created = ProvisionUser().execute(
            auth0_user_id="auth0|doctor1",
            auth0_org_id="org_test123",
            role="doctor",
            email="doc@example.com",
            name="Alice",
        )

        self.assertTrue(created)
        self.assertEqual(user.auth0_user_id, "auth0|doctor1")
        self.assertEqual(user.email, "doc@example.com")
        self.assertEqual(user.role, User.Role.DOCTOR)
        self.assertEqual(user.tenant, self.tenant)
        self.assertEqual(user.doctor_profile.name, "Alice")

    def test_creates_patient_with_profile(self) -> None:
        user, created = ProvisionUser().execute(
            auth0_user_id="auth0|patient1",
            auth0_org_id="org_test123",
            role="patient",
            email="pat@example.com",
            name="Bob",
        )

        self.assertTrue(created)
        self.assertEqual(user.role, User.Role.PATIENT)
        self.assertEqual(user.patient_profile.name, "Bob")

    def test_idempotent_returns_existing_user(self) -> None:
        user1, created1 = ProvisionUser().execute(
            auth0_user_id="auth0|repeat",
            auth0_org_id="org_test123",
            role="doctor",
            email="repeat@example.com",
        )
        user2, created2 = ProvisionUser().execute(
            auth0_user_id="auth0|repeat",
            auth0_org_id="org_test123",
            role="doctor",
            email="repeat@example.com",
        )

        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(user1.pk, user2.pk)

    def test_raises_tenant_not_found(self) -> None:
        with self.assertRaises(TenantNotFound) as exc_info:
            ProvisionUser().execute(
                auth0_user_id="auth0|orphan",
                auth0_org_id="org_nonexistent",
                role="doctor",
                email="orphan@example.com",
            )
        self.assertIn("org_nonexistent", str(exc_info.exception))

    def test_name_defaults_to_empty_string(self) -> None:
        user, _ = ProvisionUser().execute(
            auth0_user_id="auth0|noname",
            auth0_org_id="org_test123",
            role="patient",
            email="noname@example.com",
        )

        self.assertEqual(user.patient_profile.name, "")

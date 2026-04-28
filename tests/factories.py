from __future__ import annotations

import datetime

import factory
from factory.django import DjangoModelFactory

from accounts.models import DoctorProfile, PatientProfile, Tenant, User
from devices.models import Device


class TenantFactory(DjangoModelFactory):
    class Meta:
        model = Tenant

    name = factory.Sequence(lambda n: f"Test Tenant {n}")
    auth0_organization_id = factory.Sequence(lambda n: f"test_org_{n}")


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    @classmethod
    def _create(cls, model_class: type[User], *args: object, **kwargs: object) -> User:
        return model_class.objects.create_user(**kwargs)  # type: ignore[arg-type]

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    tenant = factory.SubFactory(TenantFactory)
    role = User.Role.DOCTOR
    auth0_user_id = factory.Sequence(lambda n: f"auth0|user_{n}")


class DoctorUserFactory(UserFactory):
    role = User.Role.DOCTOR
    email = factory.Sequence(lambda n: f"doctor{n}@example.com")


class PatientUserFactory(UserFactory):
    role = User.Role.PATIENT
    email = factory.Sequence(lambda n: f"patient{n}@example.com")


class DoctorProfileFactory(DjangoModelFactory):
    class Meta:
        model = DoctorProfile

    user = factory.SubFactory(DoctorUserFactory)
    name = "Test Doctor"
    surname = "Test Doctor"
    specialization = "Test Specialization"
    license_number = factory.Sequence(lambda n: f"LIC{n:06d}")


class PatientProfileFactory(DjangoModelFactory):
    class Meta:
        model = PatientProfile

    user = factory.SubFactory(PatientUserFactory)
    name = "Test Patient"
    surname = "Test Patient"
    dob = datetime.date(1990, 1, 1)
    gender = "male"
    medical_id = factory.Sequence(lambda n: f"MED{n:06d}")


class DeviceFactory(DjangoModelFactory):
    class Meta:
        model = Device

    serial_number = factory.Sequence(lambda n: f"SN{n:010d}")
    brand = "Test Brand"
    name = "Test Device"
    tenant = factory.SubFactory(TenantFactory)

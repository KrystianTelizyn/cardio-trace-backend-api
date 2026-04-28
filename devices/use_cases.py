from django.db import transaction
from django.db.utils import IntegrityError

from devices.models import Device, DeviceAssignment
from accounts.models import Tenant, PatientProfile, DoctorProfile
from devices.exceptions import (
    DeviceAssignmentAlreadyExistsError,
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    PatientProfileNotFoundError,
)


class CreateDevice:
    def execute(
        self, *, serial_number: str, brand: str, name: str, tenant: Tenant
    ) -> Device:
        if Device.objects.filter(
            serial_number=serial_number, tenant=tenant, brand=brand
        ).exists():
            raise DeviceAlreadyExistsError(serial_number)

        try:
            return Device.objects.create(
                serial_number=serial_number, brand=brand, name=name, tenant=tenant
            )
        except IntegrityError as exc:
            # Covers concurrent duplicate creates for the unique constraint.
            raise DeviceAlreadyExistsError(serial_number) from exc


class AssignDevice:
    def execute(
        self,
        *,
        device_id: int,
        patient_profile_id: int,
        doctor_profile: DoctorProfile,
        tenant: Tenant,
    ) -> DeviceAssignment:
        device = Device.objects.filter(id=device_id, tenant=tenant).first()
        if not device:
            raise DeviceNotFoundError(device_id)

        patient_profile = PatientProfile.objects.filter(
            id=patient_profile_id,
            user__tenant=tenant,
        ).first()
        if not patient_profile:
            raise PatientProfileNotFoundError(patient_profile_id)

        try:
            with transaction.atomic():
                return DeviceAssignment.objects.create(
                    device=device,
                    patient=patient_profile,
                    doctor=doctor_profile,
                    tenant=tenant,
                )
        except IntegrityError as exc:
            # Covers concurrent duplicate assignments for the unique constraint.
            raise DeviceAssignmentAlreadyExistsError(
                device_id=device_id, patient_profile_id=patient_profile_id
            ) from exc

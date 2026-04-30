from datetime import datetime

from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone

from devices.models import Device, DeviceAssignment
from accounts.models import Tenant, PatientProfile, DoctorProfile
from devices.exceptions import (
    DeviceAlreadyActivelyAssignedError,
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceAssignmentAlreadyStoppedError,
    DeviceAssignmentNotFoundError,
    PatientAlreadyHasActiveDeviceAssignmentError,
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

        with transaction.atomic():
            now = timezone.now()
            active_assignments = DeviceAssignment.objects.filter(
                tenant=tenant,
                unassigned_at__isnull=True,
            )
            if active_assignments.filter(device=device).exists():
                raise DeviceAlreadyActivelyAssignedError(device_id=device_id)

            if active_assignments.filter(patient=patient_profile).exists():
                raise PatientAlreadyHasActiveDeviceAssignmentError(
                    patient_profile_id=patient_profile_id
                )

            return DeviceAssignment.objects.create(
                device=device,
                patient=patient_profile,
                doctor=doctor_profile,
                tenant=tenant,
                assigned_at=now,
                unassigned_at=None,
            )


class StopDeviceAssignment:
    def execute(
        self,
        *,
        assignment_id: int,
        tenant: Tenant,
        unassigned_at: datetime | None = None,
    ) -> DeviceAssignment:
        assignment = DeviceAssignment.objects.filter(
            id=assignment_id,
            tenant=tenant,
        ).first()
        if not assignment:
            raise DeviceAssignmentNotFoundError(assignment_id)

        if assignment.unassigned_at is not None:
            raise DeviceAssignmentAlreadyStoppedError(assignment_id)

        stopped_at = unassigned_at or timezone.now()
        if stopped_at <= assignment.assigned_at:
            stopped_at = timezone.now()

        assignment.unassigned_at = stopped_at
        assignment.save(update_fields=["unassigned_at"])
        return assignment

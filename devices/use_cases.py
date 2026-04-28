from devices.models import Device, DeviceAssignment
from accounts.models import Tenant, PatientProfile, DoctorProfile
from devices.exceptions import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    PatientProfileNotFoundError,
)


class CreateDevice:
    def execute(
        self, *, serial_number: str, brand: str, name: str, tenant: Tenant
    ) -> tuple[Device, bool]:
        if Device.objects.filter(
            serial_number=serial_number, tenant=tenant, brand=brand
        ).exists():
            raise DeviceAlreadyExistsError(serial_number)

        return Device.objects.create(
            serial_number=serial_number, brand=brand, name=name, tenant=tenant
        )


class AssignDevice:
    def execute(
        self,
        *,
        device_id: int,
        patient_profile_id: int,
        doctor_profile: DoctorProfile,
        tenant: Tenant,
    ) -> tuple[DeviceAssignment, bool]:
        if not Device.objects.filter(id=device_id, tenant=tenant).exists():
            raise DeviceNotFoundError(device_id)
        if not PatientProfile.objects.filter(
            id=patient_profile_id,
            user__tenant=tenant,
        ).exists():
            raise PatientProfileNotFoundError(patient_profile_id)
        device = Device.objects.get(id=device_id, tenant=tenant)
        patient_profile = PatientProfile.objects.get(
            id=patient_profile_id,
            user__tenant=tenant,
        )
        return DeviceAssignment.objects.create(
            device=device, patient=patient_profile, doctor=doctor_profile, tenant=tenant
        )

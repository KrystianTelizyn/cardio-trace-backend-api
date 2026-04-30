from config.exceptions import DomainException
from rest_framework import status


class DeviceAlreadyExistsError(DomainException):
    code: str = "device_already_exists"
    message_template: str = "Device with serial number {serial_number} already exists"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, serial_number: str) -> None:
        super().__init__(serial_number=serial_number)


class DeviceNotFoundError(DomainException):
    code: str = "device_not_found"
    message_template: str = "Device with id {device_id} not found"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, device_id: int) -> None:
        super().__init__(device_id=device_id)


class PatientProfileNotFoundError(DomainException):
    code: str = "patient_profile_not_found"
    message_template: str = "Patient profile with id {patient_profile_id} not found"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, patient_profile_id: int) -> None:
        super().__init__(patient_profile_id=patient_profile_id)


class DeviceAlreadyActivelyAssignedError(DomainException):
    code: str = "device_already_actively_assigned"
    message_template: str = "Device {device_id} already has an active assignment"
    status_code: int = status.HTTP_409_CONFLICT

    def __init__(self, device_id: int) -> None:
        super().__init__(device_id=device_id)


class PatientAlreadyHasActiveDeviceAssignmentError(DomainException):
    code: str = "patient_already_has_active_device_assignment"
    message_template: str = (
        "Patient profile {patient_profile_id} already has an active device assignment"
    )
    status_code: int = status.HTTP_409_CONFLICT

    def __init__(self, patient_profile_id: int) -> None:
        super().__init__(patient_profile_id=patient_profile_id)


class DeviceAssignmentAlreadyStoppedError(DomainException):
    code: str = "device_assignment_already_stopped"
    message_template: str = (
        "Device assignment with id {assignment_id} is already stopped"
    )
    status_code: int = status.HTTP_409_CONFLICT

    def __init__(self, assignment_id: int) -> None:
        super().__init__(assignment_id=assignment_id)


class DeviceAssignmentNotFoundError(DomainException):
    code: str = "device_assignment_not_found"
    message_template: str = "Device assignment with id {assignment_id} not found"
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, assignment_id: int) -> None:
        super().__init__(assignment_id=assignment_id)


class DeviceIdentityNotFoundError(DomainException):
    code: str = "device_identity_not_found"
    message_template: str = "Device not found for tenant {tenant_id}, serial_number {serial_number}, brand {brand}"
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, *, tenant_id: int, serial_number: str, brand: str) -> None:
        super().__init__(
            tenant_id=tenant_id,
            serial_number=serial_number,
            brand=brand,
        )

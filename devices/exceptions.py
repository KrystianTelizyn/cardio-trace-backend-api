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


class DeviceAssignmentAlreadyExistsError(DomainException):
    code: str = "device_assignment_already_exists"
    message_template: str = (
        "Device {device_id} already has an active assignment in this tenant"
    )
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, device_id: int, patient_profile_id: int) -> None:
        super().__init__(device_id=device_id, patient_profile_id=patient_profile_id)


class DeviceAssignmentNotFoundError(DomainException):
    code: str = "device_assignment_not_found"
    message_template: str = "Device assignment with id {assignment_id} not found"
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, assignment_id: int) -> None:
        super().__init__(assignment_id=assignment_id)

from rest_framework import status

from config.exceptions import DomainException


class DeviceBySerialNotFoundError(DomainException):
    code: str = "device_not_found"
    message_template: str = "Device with serial number {serial_number} not found"
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, serial_number: str) -> None:
        super().__init__(serial_number=serial_number)


class DeviceHasNoActiveAssignmentError(DomainException):
    code: str = "device_has_no_active_assignment"
    message_template: str = (
        "Device with serial number {serial_number} has no active assignment"
    )
    status_code: int = status.HTTP_409_CONFLICT

    def __init__(self, serial_number: str) -> None:
        super().__init__(serial_number=serial_number)

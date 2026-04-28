from config.exceptions import DomainException
from rest_framework import status


class DeviceAlreadyExistsError(DomainException):
    code: str = "device_already_exists"
    message_template: str = "Device with serial number {serial_number} already exists"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, serial_number: str):
        super().__init__(serial_number=serial_number)

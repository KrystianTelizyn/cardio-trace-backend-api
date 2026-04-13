import logging
from rest_framework import status


class DomainException(Exception):
    code: str = "domain_error"
    status_code: int = status.HTTP_400_BAD_REQUEST
    log_level: int = logging.WARNING
    message: str = "This is a generic error"
    message_template: str = "This is a generic error"

    def __init__(self, **extra: object) -> None:
        self.extra = extra or {}
        self.message = self.message_template.format(**extra)
        super().__init__(self.message)

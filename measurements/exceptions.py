from rest_framework import status

from config.exceptions import DomainException


class MeasurementSessionNotFoundError(DomainException):
    code: str = "measurement_session_not_found"
    message_template: str = (
        "Measurement session {measurement_session_id} not found for tenant {tenant_id}"
    )
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, *, measurement_session_id: str, tenant_id: int) -> None:
        super().__init__(
            measurement_session_id=measurement_session_id,
            tenant_id=tenant_id,
        )


class MeasurementSessionNotActiveError(DomainException):
    code: str = "measurement_session_not_active"
    message_template: str = (
        "Measurement session {measurement_session_id} is not active "
        "or timestamp is outside valid window for tenant {tenant_id}"
    )
    status_code: int = status.HTTP_409_CONFLICT

    def __init__(self, *, measurement_session_id: str, tenant_id: int) -> None:
        super().__init__(
            measurement_session_id=measurement_session_id,
            tenant_id=tenant_id,
        )


class MeasurementDroppedSessionStopped(DomainException):
    code: str = "measurement_dropped_session_stopped"
    message_template: str = (
        "Measurement dropped because session {measurement_session_id} is stopped"
    )
    status_code: int = status.HTTP_202_ACCEPTED

    def __init__(self, *, measurement_session_id: str) -> None:
        super().__init__(measurement_session_id=measurement_session_id)

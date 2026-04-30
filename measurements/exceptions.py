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


class MeasurementSessionAssignmentNotFoundError(DomainException):
    code: str = "measurement_session_assignment_not_found"
    message_template: str = (
        "Active assignment {device_assignment_id} not found in tenant {tenant_id}"
    )
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(
        self,
        *,
        device_assignment_id: int,
        tenant_id: int,
    ) -> None:
        super().__init__(
            device_assignment_id=device_assignment_id,
            tenant_id=tenant_id,
        )


class MeasurementSessionStartOutsideAssignmentWindowError(DomainException):
    code: str = "measurement_session_start_outside_assignment_window"
    message_template: str = (
        "Session start {started_at} is outside assignment window for assignment "
        "{device_assignment_id}"
    )
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, *, started_at: str, device_assignment_id: int) -> None:
        super().__init__(
            started_at=started_at, device_assignment_id=device_assignment_id
        )


class ActiveMeasurementSessionAlreadyExistsError(DomainException):
    code: str = "active_measurement_session_already_exists"
    message_template: str = "Active measurement session already exists for assignment {device_assignment_id}"
    status_code: int = status.HTTP_409_CONFLICT

    def __init__(self, *, device_assignment_id: int) -> None:
        super().__init__(device_assignment_id=device_assignment_id)

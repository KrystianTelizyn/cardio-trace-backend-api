from rest_framework import status

from config.exceptions import DomainException


class TenantNotFound(DomainException):
    code: str = "tenant_not_found"
    message_template: str = "No tenant found for auth0_org_id: {auth0_org_id}"
    status_code: int = status.HTTP_404_NOT_FOUND

    def __init__(self, auth0_org_id: str) -> None:
        super().__init__(auth0_org_id=auth0_org_id)

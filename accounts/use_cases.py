from django.db import transaction
from django.db.utils import IntegrityError
from accounts.exceptions import TenantNotFound
from accounts.models import DoctorProfile, PatientProfile, Tenant, User


class ProvisionUser:
    def execute(
        self,
        *,
        auth0_user_id: str,
        auth0_org_id: str,
        role: str,
        email: str,
        name: str = "",
    ) -> tuple[User, bool]:
        if not Tenant.objects.filter(auth0_organization_id=auth0_org_id).exists():
            raise TenantNotFound(auth0_org_id)
        try:
            with transaction.atomic():
                tenant = Tenant.objects.filter(
                    auth0_organization_id=auth0_org_id
                ).first()
                user = User.objects.create_user(
                    auth0_user_id=auth0_user_id,
                    email=email,
                    tenant=tenant,
                    role=role,
                )
                if role == User.Role.DOCTOR:
                    DoctorProfile.objects.create(user=user, name=name)
                else:
                    PatientProfile.objects.create(user=user, name=name)
                created = True
        except IntegrityError:
            created = False
            user = User.objects.filter(auth0_user_id=auth0_user_id).first()
            if not user:
                raise
        return user, created

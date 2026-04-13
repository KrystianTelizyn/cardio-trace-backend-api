from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class Tenant(models.Model):
    auth0_organization_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, auth0_user_id, email, tenant, role, **extra_fields):
        if not auth0_user_id:
            raise ValueError("auth0_user_id is required")
        if not email:
            raise ValueError("email is required")

        user = self.model(
            auth0_user_id=auth0_user_id,
            email=self.normalize_email(email),
            tenant=tenant,
            role=role,
            **extra_fields,
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, auth0_user_id, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if "tenant" not in extra_fields:
            extra_fields["tenant"] = None
        if "role" not in extra_fields:
            extra_fields["role"] = User.Role.DOCTOR

        user = self.create_user(auth0_user_id, email, **extra_fields)
        if password:
            user.set_password(password)
            user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        DOCTOR = "doctor"
        PATIENT = "patient"

    auth0_user_id = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "auth0_user_id"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.email


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
    )
    name = models.CharField(max_length=255, blank=True, default="")
    surname = models.CharField(max_length=255, blank=True, default="")
    specialization = models.CharField(max_length=255, blank=True, default="")
    license_number = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.name or str(self.user)


class PatientProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )
    name = models.CharField(max_length=255, blank=True, default="")
    surname = models.CharField(max_length=255, blank=True, default="")
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, blank=True, default="")
    medical_id = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.name or str(self.user)

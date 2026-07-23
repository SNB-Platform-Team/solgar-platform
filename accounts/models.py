"""
accounts app — user model.

Extends AbstractUser with fields needed for Azure AD integration later.
All queries against this model go through the ORM.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class UserType(models.TextChoices):
    """Where the account comes from."""

    EMPLOYEE = "EMPLOYEE", "Employee (Azure AD)"
    LOCAL = "LOCAL", "Local Account"


class User(AbstractUser):
    """
    Solgar internal platform user.

    Local accounts sign in with a password. Employees signing in through
    Azure AD are matched by `azure_object_id` once SSO is enabled.
    """

    azure_object_id = models.CharField(
        "Azure Object ID",
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="Azure AD 'oid' claim. Empty for local accounts.",
    )
    user_type = models.CharField(
        "User Type",
        max_length=10,
        choices=UserType.choices,
        default=UserType.LOCAL,
    )
    department = models.CharField("Department", max_length=100, blank=True)
    phone = models.CharField("Phone", max_length=20, blank=True)
    is_enabled = models.BooleanField(
        "Is enabled",
        default=True,
        help_text="Disabled users cannot sign in.",
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "accounts_user"

    def __str__(self) -> str:
        """Readable representation for admin and logs."""
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"
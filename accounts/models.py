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

    access_level = models.ForeignKey(
        "authorization.AccessLevel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Access level",
    )

    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
        verbose_name="Manager",
        help_text="This user's direct manager, for approval routing.",
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


class LoginLog(models.Model):
    """Audit record of a user login or logout event."""

    class EventType(models.TextChoices):
        """Type of authentication event."""

        LOGIN = "LOGIN", "Вход"
        LOGOUT = "LOGOUT", "Выход"

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="login_logs",
        verbose_name="User",
    )
    event_type = models.CharField(
        "Event type", max_length=10, choices=EventType.choices
    )
    ip_address = models.GenericIPAddressField("IP address", null=True, blank=True)
    user_agent = models.CharField("User agent", max_length=300, blank=True)
    timestamp = models.DateTimeField("Timestamp", auto_now_add=True)

    class Meta:
        verbose_name = "Login log"
        verbose_name_plural = "Login logs"
        db_table = "accounts_login_log"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        """Readable representation."""
        return f"{self.user} — {self.get_event_type_display()} — {self.timestamp}"
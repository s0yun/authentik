"""tenant models"""
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _

from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.lib.utils.time import timedelta_string_validator


class Tenant(models.Model):
    """Single tenant"""

    tenant_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    domain = models.TextField(
        help_text=_(
            "Domain that activates this tenant. "
            "Can be a superset, i.e. `a.b` for `aa.b` and `ba.b`"
        )
    )
    default = models.BooleanField(
        default=False,
    )

    branding_title = models.TextField(default="authentik")

    branding_logo = models.TextField(default="/static/dist/assets/icons/icon_left_brand.svg")
    branding_favicon = models.TextField(default="/static/dist/assets/icons/icon.png")

    flow_authentication = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="tenant_authentication"
    )
    flow_invalidation = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="tenant_invalidation"
    )
    flow_recovery = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="tenant_recovery"
    )
    flow_unenrollment = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="tenant_unenrollment"
    )
    flow_user_settings = models.ForeignKey(
        Flow, null=True, on_delete=models.SET_NULL, related_name="tenant_user_settings"
    )

    event_retention = models.TextField(
        default="days=365",
        validators=[timedelta_string_validator],
        help_text=_(
            (
                "Events will be deleted after this duration."
                "(Format: weeks=3;days=2;hours=3,seconds=2)."
            )
        ),
    )

    web_certificate = models.ForeignKey(
        CertificateKeyPair,
        null=True,
        default=None,
        on_delete=models.SET_DEFAULT,
        help_text=_(("Web Certificate used by the authentik Core webserver.")),
    )

    attributes = models.JSONField(default=dict, blank=True)

    @property
    def default_locale(self) -> str:
        """Get default locale"""
        return self.attributes.get("settings", {}).get("locale", "")

    def __str__(self) -> str:
        if self.default:
            return "Default tenant"
        return f"Tenant {self.domain}"

    class Meta:

        verbose_name = _("Tenant")
        verbose_name_plural = _("Tenants")

"""Serializer for tenant models"""
from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ListField, ReadOnlyField
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.lib.config import CONFIG
from authentik.tenants.models import Tenant


class FooterLinkSerializer(PassiveSerializer):
    """Links returned in Config API"""

    href = CharField(read_only=True)
    name = CharField(read_only=True)


class TenantSerializer(ModelSerializer):
    """Tenant Serializer"""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get("default", False):
            tenants = Tenant.objects.filter(default=True)
            if self.instance:
                tenants = tenants.exclude(pk=self.instance.pk)
            if tenants.exists():
                raise ValidationError("Only a single Tenant can be set as default.")
        return super().validate(attrs)

    class Meta:

        model = Tenant
        fields = [
            "tenant_uuid",
            "domain",
            "default",
            "branding_title",
            "branding_logo",
            "branding_favicon",
            "flow_authentication",
            "flow_invalidation",
            "flow_recovery",
            "flow_unenrollment",
            "flow_user_settings",
            "event_retention",
            "web_certificate",
            "attributes",
        ]


class CurrentTenantSerializer(PassiveSerializer):
    """Partial tenant information for styling"""

    matched_domain = CharField(source="domain")
    branding_title = CharField()
    branding_logo = CharField()
    branding_favicon = CharField()
    ui_footer_links = ListField(
        child=FooterLinkSerializer(),
        read_only=True,
        default=CONFIG.y("footer_links", []),
    )

    flow_authentication = CharField(source="flow_authentication.slug", required=False)
    flow_invalidation = CharField(source="flow_invalidation.slug", required=False)
    flow_recovery = CharField(source="flow_recovery.slug", required=False)
    flow_unenrollment = CharField(source="flow_unenrollment.slug", required=False)
    flow_user_settings = CharField(source="flow_user_settings.slug", required=False)

    default_locale = ReadOnlyField()


class TenantViewSet(UsedByMixin, ModelViewSet):
    """Tenant Viewset"""

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    search_fields = [
        "domain",
        "branding_title",
        "web_certificate__name",
    ]
    filterset_fields = [
        "tenant_uuid",
        "domain",
        "default",
        "branding_title",
        "branding_logo",
        "branding_favicon",
        "flow_authentication",
        "flow_invalidation",
        "flow_recovery",
        "flow_unenrollment",
        "flow_user_settings",
        "event_retention",
        "web_certificate",
    ]
    ordering = ["domain"]

    @extend_schema(
        responses=CurrentTenantSerializer(many=False),
    )
    @action(methods=["GET"], detail=False, permission_classes=[AllowAny])
    # pylint: disable=invalid-name, unused-argument
    def current(self, request: Request) -> Response:
        """Get current tenant"""
        tenant: Tenant = request._request.tenant
        return Response(CurrentTenantSerializer(tenant).data)

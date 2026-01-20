"""Configuration for M365 Collaboration Tool."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class M365Config:
    """M365 connection configuration from environment."""

    tenant_id: str
    client_id: str
    client_secret: str
    site_path: str = "root"

    @classmethod
    def from_env(cls) -> "M365Config":
        """Load configuration from environment variables."""
        tenant_id = os.environ.get("M365_TENANT_ID")
        client_id = os.environ.get("M365_CLIENT_ID")
        client_secret = os.environ.get("M365_CLIENT_SECRET")
        site_path = os.environ.get("M365_SITE_PATH", "root")

        missing = []
        if not tenant_id:
            missing.append("M365_TENANT_ID")
        if not client_id:
            missing.append("M365_CLIENT_ID")
        if not client_secret:
            missing.append("M365_CLIENT_SECRET")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Set these to use M365 collaboration."
            )

        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            site_path=site_path,
        )

    @classmethod
    def is_configured(cls) -> bool:
        """Check if M365 is configured without raising."""
        return all([
            os.environ.get("M365_TENANT_ID"),
            os.environ.get("M365_CLIENT_ID"),
            os.environ.get("M365_CLIENT_SECRET"),
        ])

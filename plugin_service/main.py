"""FastAPI entrypoint for acmed certbot plugin service."""

from __future__ import annotations

from acmed_plugin_sdk.server import PluginServerSettings, create_plugin_app
from acmed_issuer_certbot.plugin import CertbotPlugin

app = create_plugin_app(
    CertbotPlugin(),
    settings=PluginServerSettings(require_bearer_auth=True),
)

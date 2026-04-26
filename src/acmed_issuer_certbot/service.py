"""ASGI service entrypoint for the certbot issuer plugin."""

from __future__ import annotations

from acmed_plugin_sdk.server import PluginServerSettings, create_plugin_app

from .plugin import CertbotPlugin

app = create_plugin_app(
    CertbotPlugin(),
    settings=PluginServerSettings(require_bearer_auth=True),
)

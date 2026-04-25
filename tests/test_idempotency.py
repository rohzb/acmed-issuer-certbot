from __future__ import annotations

from pathlib import Path

from acmed_issuer_certbot.plugin import CertbotPlugin
from acmed_plugin_sdk.models import IssueRequest


def test_certbot_plugin_caches_by_order_id(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ACMED_PLUGIN_STATE_DIR", str(tmp_path))

    calls = {"count": 0}

    def fake_run(*args, **kwargs):  # noqa: ANN002,ANN003
        calls["count"] += 1
        workdir = Path(kwargs["cwd"])
        (workdir / "certificate.pem").write_text("CERT", encoding="utf-8")
        (workdir / "fullchain.pem").write_text("FULLCHAIN", encoding="utf-8")
        (workdir / "private.key").write_text("KEY", encoding="utf-8")
        return type("RunResult", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()

    monkeypatch.setattr("acmed_issuer_certbot.plugin.subprocess.run", fake_run)
    monkeypatch.setattr("acmed_issuer_certbot.plugin.shutil.which", lambda _: "/usr/bin/certbot")

    plugin = CertbotPlugin()
    req = IssueRequest(
        order_id="ord-1",
        dns_names=["host.example.org"],
        common_name="host.example.org",
        profile={"plugin_name": "dns-route53", "challenge_mode": "dns-01"},
    )
    r1 = plugin.issue(req)
    r2 = plugin.issue(req)

    assert r1.success is True
    assert r2.success is True
    assert calls["count"] == 1

"""certbot remote plugin handler.

The handler executes certbot inside the plugin service container and returns
normalized contract responses. Terminal results are cached by `order_id` for
idempotent retries.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from time import monotonic

from acmed_plugin_sdk.models import Capabilities, IssueRequest, IssueResult


class CertbotPlugin:
    """certbot plugin handler implementation for remote mode."""

    def __init__(self) -> None:
        self._state_root = Path(os.environ.get("ACMED_PLUGIN_STATE_DIR", "/var/lib/acmed-plugin")) / "certbot"
        self._state_root.mkdir(parents=True, exist_ok=True)

    def capabilities(self) -> Capabilities:
        return Capabilities(
            plugin_name="acmed-issuer-certbot",
            plugin_version="0.2.0",
            challenge_modes=["dns-01", "http-01"],
        )

    def _order_dir(self, order_id: str) -> Path:
        path = self._state_root / "orders" / order_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _result_path(self, order_id: str) -> Path:
        return self._order_dir(order_id) / "result.json"

    def _load_cached_result(self, order_id: str) -> IssueResult | None:
        path = self._result_path(order_id)
        if not path.exists():
            return None
        try:
            return IssueResult.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _save_cached_result(self, request: IssueRequest, result: IssueResult) -> None:
        self._result_path(request.order_id).write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def _read_if_exists(self, path: Path) -> str | None:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def _filtered_env(self, request: IssueRequest) -> dict[str, str]:
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", "/tmp"),
        }
        profile = request.profile if isinstance(request.profile, dict) else {}
        for name in profile.get("credential_env", []):
            if isinstance(name, str) and name in os.environ:
                env[name] = os.environ[name]
        return env

    def issue(self, request: IssueRequest) -> IssueResult:
        cached = self._load_cached_result(request.order_id)
        if cached is not None:
            return cached

        started = monotonic()
        profile = request.profile if isinstance(request.profile, dict) else {}
        challenge_mode = str(profile.get("challenge_mode") or "dns-01")
        plugin_name = str(profile.get("plugin_name") or "").strip()
        directory_url = str(profile.get("ca_directory_url") or "").strip()

        if challenge_mode != "dns-01":
            result = IssueResult(
                success=False,
                result_code="issuer_error",
                reason_code="validation_error",
                command="certbot certonly",
                exit_code=64,
                stderr=f"unsupported certbot challenge_mode: {challenge_mode}",
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result
        if not plugin_name:
            result = IssueResult(
                success=False,
                result_code="issuer_error",
                reason_code="validation_error",
                command="certbot certonly",
                exit_code=64,
                stderr="certbot remote issue requires profile.plugin_name",
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result

        certbot = str(profile.get("executable") or shutil.which("certbot") or "")
        if not certbot:
            result = IssueResult(
                success=False,
                result_code="issuer_error",
                reason_code="dependency_missing",
                command="certbot --version",
                exit_code=127,
                stderr="certbot is not installed in plugin container",
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result

        workdir = self._order_dir(request.order_id)
        cert_path = workdir / "certificate.pem"
        chain_path = workdir / "chain.pem"
        fullchain_path = workdir / "fullchain.pem"
        key_path = workdir / "private.key"

        argv = [
            certbot,
            "certonly",
            "--non-interactive",
            "--agree-tos",
            "--register-unsafely-without-email",
            "--config-dir",
            str(workdir / "config"),
            "--work-dir",
            str(workdir / "work"),
            "--logs-dir",
            str(workdir / "logs"),
            "--cert-path",
            str(cert_path),
            "--chain-path",
            str(chain_path),
            "--fullchain-path",
            str(fullchain_path),
            "--key-path",
            str(key_path),
        ]
        if directory_url:
            argv.extend(["--server", directory_url])

        # Plugin names are expected in certbot style like dns-route53.
        argv.append(f"--{plugin_name}")
        for dns_name in request.dns_names:
            argv.extend(["-d", dns_name])

        env = self._filtered_env(request)

        try:
            run = subprocess.run(  # noqa: S603
                argv,
                check=False,
                capture_output=True,
                text=True,
                timeout=int(profile.get("timeout_seconds") or 120),
                cwd=str(workdir),
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            result = IssueResult(
                success=False,
                result_code="retryable_error",
                reason_code="timeout",
                command=" ".join(argv),
                exit_code=124,
                stderr=f"certbot issue timeout: {exc}",
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result

        cert = self._read_if_exists(cert_path)
        chain = self._read_if_exists(chain_path)
        fullchain = self._read_if_exists(fullchain_path)
        key = self._read_if_exists(key_path)
        missing = []
        if cert is None:
            missing.append("certificate.pem")
        if fullchain is None:
            missing.append("fullchain.pem")
        if key is None:
            missing.append("private.key")

        stderr = run.stderr or ""
        reason_code = "internal_error"
        result_code = "issuer_error"
        if run.returncode != 0:
            reason_code = "dependency_failed"
            if "rate" in stderr.lower() and "limit" in stderr.lower():
                reason_code = "rate_limited"
                result_code = "retryable_error"
            elif "unauthorized" in stderr.lower() or "rejected" in stderr.lower():
                reason_code = "upstream_ca_error"
        elif missing:
            stderr = "\n".join(
                [piece for piece in [stderr, f"issuer output missing required artifacts: {', '.join(missing)}"] if piece]
            )
            reason_code = "internal_error"
        else:
            result = IssueResult(
                success=True,
                result_code="issued",
                reason_code="ok_issued",
                command=" ".join(argv),
                exit_code=0,
                stdout=run.stdout,
                stderr=stderr,
                certificate_pem=cert,
                chain_pem=chain,
                fullchain_pem=fullchain,
                private_key_pem=key,
                duration_ms=int((monotonic() - started) * 1000),
            )
            self._save_cached_result(request, result)
            return result

        result = IssueResult(
            success=False,
            result_code=result_code,
            reason_code=reason_code,
            command=" ".join(argv),
            exit_code=run.returncode if run.returncode != 0 else 65,
            stdout=run.stdout,
            stderr=stderr,
            certificate_pem=cert,
            chain_pem=chain,
            fullchain_pem=fullchain,
            private_key_pem=key,
            duration_ms=int((monotonic() - started) * 1000),
        )
        self._save_cached_result(request, result)
        return result

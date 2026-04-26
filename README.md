# acmed-issuer-certbot

`acmed-issuer-certbot` is a remote issuer plugin for the `acmed` gen2 stack.
It runs `certbot` behind a small HTTP API so `acmed` can delegate issuance to
it using the shared plugin contract (`/healthz`, `/capabilities`, `/issue`).

## What this project is for

Use this plugin when:

- you want ACME issuance delegated out of `acmed` core
- your environment is already based on `certbot` automation
- you want a containerized issuer service with token-authenticated API access

The plugin is intentionally narrow: policy and requester authorization stay in
`acmed`; this service only executes issuance work.

## How it works

For each issue request, the plugin:

1. validates request/profile inputs
2. runs `certbot certonly ...`
3. reads generated certificate/key artifacts from an order-specific state directory
4. returns normalized output and PEM artifacts
5. caches terminal result by `order_id` for idempotent retries

## Current behavior and limits

- API endpoints are implemented: `/healthz`, `/capabilities`, `/issue`
- bearer auth is required for `/capabilities` and `/issue`
- issue path currently supports `dns-01` execution flow
- `profile.plugin_name` is required for `/issue` (for example `dns-route53`)
- certbot binary is installed into the image during build

## Runtime configuration

Environment variables:

- `ACMED_REMOTE_PLUGIN_TOKEN` (required): primary bearer token
- `ACMED_REMOTE_PLUGIN_TOKEN_NEXT` (optional): overlap token for rotation windows
- `ACMED_PLUGIN_STATE_DIR` (optional): state root, default `/var/lib/acmed-plugin`

Issue profile fields used by the handler:

- `plugin_name` (required): certbot plugin flag suffix, e.g. `dns-route53`
- `challenge_mode` (optional): must resolve to `dns-01` for current execution path
- `ca_directory_url` (optional): passed as `--server`
- `timeout_seconds` (optional): subprocess timeout (default `120`)
- `credential_env` (optional list): env var names copied into the certbot process
- `executable` (optional): explicit certbot binary path

## Quick start

Build from repository root:

```bash
docker build -f docker/Dockerfile -t acmed-issuer-certbot:0.2.0 .
```

Run:

```bash
docker run --rm -p 8081:8081 \
  -e ACMED_REMOTE_PLUGIN_TOKEN='replace-with-random-token' \
  acmed-issuer-certbot:0.2.0
```

Check health:

```bash
curl -s http://127.0.0.1:8081/healthz
```

Check capabilities:

```bash
curl -s http://127.0.0.1:8081/capabilities \
  -H "Authorization: Bearer replace-with-random-token"
```

Optional SDK base image override at build time:

```bash
docker build -f docker/Dockerfile \
  --build-arg ACMED_PLUGIN_BASE_IMAGE='ghcr.io/rohzb/acmed-plugin-base-image:v0.2.0' \
  -t acmed-issuer-certbot:0.2.0 .
```

This image extends the released SDK base image package
`ghcr.io/rohzb/acmed-plugin-base-image:<tag>`, which is published by
the `acmed-plugin-sdk` release workflow.

## Integration notes for acmed

- Plugin service listens on `0.0.0.0:8081` in container.
- `acmed` should call this service over remote issuer mode with matching bearer token.
- Keep issuer credentials in environment variables and expose only names via
  `credential_env` in the request profile.

## Troubleshooting

- `401 Unauthorized` on `/issue` or `/capabilities`:
  token mismatch or missing `Authorization: Bearer ...`
- `validation_error` mentioning `challenge_mode`:
  current issue path expects `dns-01`
- `validation_error` mentioning `profile.plugin_name`:
  missing plugin name in issuer profile
- `dependency_missing` for certbot:
  image/addon build issue, verify certbot is present in image
- repeated retries with same `order_id` returning same payload:
  expected idempotency cache behavior

## Release and CI

- CI workflow: `.github/workflows/ci.yml`
- release workflow: `.github/workflows/release.yml`
- release checklist: [`RELEASE.md`](RELEASE.md)
- project changelog: [`CHANGELOG.md`](CHANGELOG.md)

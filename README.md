# acmed-issuer-certbot

Remote issuer plugin service that packages `certbot` tooling and exposes the
acmed plugin contract.

## Current status

- plugin API is implemented (`/healthz`, `/capabilities`, `/issue`)
- container addon installs `certbot`
- `/issue` executes `certbot certonly` with explicit artifact paths
- results are cached by `order_id` for idempotent retries

Runtime environment:

- `ACMED_REMOTE_PLUGIN_TOKEN` (required)
- `ACMED_REMOTE_PLUGIN_TOKEN_NEXT` (optional overlap token)
- `ACMED_PLUGIN_STATE_DIR` (optional, defaults to `/var/lib/acmed-plugin`)

## Build

Run from this repository root:

```bash
docker build -f docker/Dockerfile -t acmed-issuer-certbot:0.2.0 .
```

Optional SDK source override:

```bash
docker build -f docker/Dockerfile \
  --build-arg ACMED_PLUGIN_SDK_SPEC='acmed-plugin-sdk>=0.2.0' \
  --build-arg ACMED_PLUGIN_SDK_FALLBACK='https://example.org/acmed-plugin-sdk-0.2.0.tar.gz' \
  -t acmed-issuer-certbot:0.2.0 .
```

## CI and Release

- CI workflow: `.github/workflows/ci.yml`
- Tag release workflow: `.github/workflows/release.yml`
- Release process notes: [`RELEASE.md`](RELEASE.md)

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

Run from `upstream/acmed_gen2`:

```bash
docker build -f acmed-issuer-certbot/docker/Dockerfile -t acmed-issuer-certbot:0.2.0 .
```

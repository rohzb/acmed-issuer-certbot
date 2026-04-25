# Release Process

## Versioning

- Tags follow `vX.Y.Z`.

## Checklist

1. Verify tests pass locally.
2. Verify Docker image builds locally.
3. Update `CHANGELOG.md`.
4. Commit and push branch.
5. Create and push tag (`vX.Y.Z`).

## Automation

Tag push triggers `.github/workflows/release.yml` and produces:

- Python package artifacts (wheel and sdist)
- container image pushed to `ghcr.io/<owner>/<repo>`
- optional PyPI publish when `PYPI_API_TOKEN` secret is configured
- GitHub release with generated notes and uploaded dist artifacts

# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-04-25

### Added
- Initial `acmed-issuer-certbot` remote issuer plugin package.
- Plugin service API (`/healthz`, `/capabilities`, `/issue`) with idempotent order cache.
- Docker packaging with `certbot` addon tooling.
- GitHub Actions CI and release workflows.

### Changed
- Docker image now extends `ghcr.io/rohzb/acmed-plugin-base-image:<tag>`,
  published by the `acmed-plugin-sdk` release workflow.
- Python dependency now resolves `acmed-plugin-sdk` from GitHub release source
  (`https://github.com/rohzb/acmed-plugin-sdk/archive/refs/tags/v0.2.0.tar.gz`).
- CI and release workflows now use pinned actions, Node24 action runtime flag,
  stricter release tag/version validation, and CI completion gating before release.
- Container entrypoint now runs packaged module path
  `acmed_issuer_certbot.service:app`.

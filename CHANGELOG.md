# Changelog

All notable changes to DevFlow are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-11-22

### Added
- OOP extension shell (`DevFlowExtension`, `Config`, `Commands`) — single responsibility per class.
- `devflow.backendHost`, `devflow.startupTimeoutMs`, `devflow.logLevel` settings — no more hardcoded runtime values.
- `HTTPTicketProvider` base class shared across Jira / Azure DevOps / GitHub providers.
- `POST /ai/validate` endpoint — the `AIEngine.is_available` contract is now live.
- Production webpack build with Terser minification.
- New icon and brand mark.
- `MARKETPLACE.md` publishing guide.

### Changed
- Rewrote README around *problem → what it reduces → who it's for → flow → per-action reference*.
- `BackendManager` now takes a single options object; `baseUrl` is the public surface.
- Sidebar provider receives a backend URL instead of a bare port.
- `server.py` hardcoded `127.0.0.1:9120` fallback replaced with `DEVFLOW_HOST` / `DEVFLOW_PORT` env vars.

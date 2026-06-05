# Changelog

All notable changes to PurpleMCP. This project adheres loosely to
[Semantic Versioning](https://semver.org/) and
[Keep a Changelog](https://keepachangelog.com/).

## [0.5.0]

### Added
- **Settings page** + `purplemcp doctor` — environment readiness (Python, providers,
  Ollama, GUI, lab state) via a shared `purplemcp/environment.py`.
- **`purplemcp taxonomy`** + generated [`docs/TAXONOMY.md`](docs/TAXONOMY.md) — the
  OWASP-LLM / CWE / MITRE-ATLAS mapping, browsable in the Learn page.
- **`purplemcp report`** + [`docs/SECURITY-REPORT.md`](docs/SECURITY-REPORT.md) — a
  reproducible security-posture report (scan summary + taxonomy + guardrails).
- **Dashboard quick-actions** that deep-link into the app.
- **Command palette (⌘K)**, **keyboard shortcuts** (⌘1–9, ⌘,, F1/⌘/), a shortcuts
  help overlay, and a live **status bar**.
- **Learn page** — the whole handbook rendered in-app.
- `--version` flag; `CONTRIBUTING.md` and `SECURITY.md`.

## [0.4.0]

### Added
- **Research layer**: threat taxonomy (`purplemcp/taxonomy.py`), **PurpleMCP-Bench**
  (`purplemcp bench`), **SARIF** scanner output, GitHub Actions CI, and the
  methodology write-up (`docs/07-research-methodology.md`) + `CITATION.cff`.
- Attack/defense modules **18–21**: eval injection, zip slip, mass assignment,
  CSV/formula injection (+ `safe_eval`, `csvsafe`, `assert_assignable` guardrails).

## [0.3.0]

### Added
- **Categorized GUI** (grouped sidebar) with **AI Models** and **MCP Servers**
  management pages, and dedicated **Attack Lab** + **Defense Lab**.
- Attack/defense modules **14–17**: broken access control (IDOR), unrestricted file
  write, weak randomness, output/log injection (+ `authz`, `tokens`, `framing`).

## [0.2.0]

### Added
- Native **PySide6 desktop GUI** (`purplemcp gui`): dashboard, tool explorer, chat
  playground, security scanner, attack/defend arena.
- Attack/defense modules **10–13**: SQL injection, template/format-string injection,
  tool shadowing, insecure deserialization (+ `sqlsafe`, `templating`, `registry`,
  `serialization` guardrails).

## [0.1.0]

### Added
- Initial release: the multi-provider MCP host + agent loop, clean example servers,
  the lab-gated attack modules **01–09**, the hardened twins, the reusable
  `guardrails` library, and the static + dynamic security scanner.

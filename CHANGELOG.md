# Changelog

All notable changes to PurpleMCP. This project adheres loosely to
[Semantic Versioning](https://semver.org/) and
[Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **Manual terminal** in the Attack Lab and Defense Lab — every exploit/defense now
  surfaces the exact `purplemcp …` / `python …` commands behind it, each one
  **copyable** (paste into your own shell) *and* **runnable in place**, with real
  subprocess output streaming into a colourised console. Scoped to the project's
  own commands (`purplemcp.gui.ops.RUNNER_ALLOW`).
- **Defense Lab redesign** — a two-pane "read it, then watch it protect" layout:
  the threat, the mechanism, a step-by-step, and the real guardrail source on the
  left; a one-click **Verify** (exploited → blocked) and the manual terminal on the
  right.
- **Brand assets** — `docs/images/logo.svg` + `docs/images/banner.svg` (and rendered
  PNGs), and a refreshed, screenshot-driven README.
- `defense/compare.py` now accepts a case filter, e.g. `python defense/compare.py ping`.

### Changed
- **Default Ollama model is now `qwen2.5`** (was `llama3.1`). qwen2.5 does Ollama's
  *structured* tool-calling reliably; llama3.1 frequently narrates a JSON "call"
  instead of emitting a real one, which made the Chat Playground look broken even
  though the model was responding. Docs, `.env.example`, and the model suggestions
  updated to match.
- Screenshots are regenerated with the labs and chat **driven live**, so they show
  real exploit output, a real exploited→blocked verify, and real MCP tool calls.
- **UI polish:** cards now have subtle vertical-gradient depth, the selected nav
  item gets a purple left-accent bar, headings use tighter letter-spacing, buttons
  gained pressed states, and the dashboard hero carries the shield logo mark. Every
  page header now leads with a brand accent bar, and the manual terminal sports
  macOS-style traffic-light dots and a "live" pill for a true terminal feel.
- **Sharper banner** — redesigned (soft node halos, dual glow, vignette) and
  rendered at 3× (3840×1200) for crisp display; the README shows it full-width.

### Fixed
- `tests/test_terminal.py` collection no longer requires PySide6: `gui/ops.py`'s
  `Job` import moved under `TYPE_CHECKING`, so CI's GUI-less `.[dev]` install passes.

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

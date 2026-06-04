# 🖥️ The Desktop GUI

`purplemcp gui` launches a native desktop **security console** built with
[PySide6](https://doc.qt.io/qtforpython/) (Qt for Python). It is a thin,
beautiful front-end over the exact same core the CLI drives — `MCPHost`, the
provider adapters, the agent loop, the scanner, and the guardrails. There is no
web server and no browser: it's a real desktop app.

```bash
pip install -e ".[gui]"   # one-time: installs PySide6
purplemcp gui             # or:  python -m purplemcp.gui
```

Everything in the GUI works offline except the Chat Playground (which needs a
real model) — the explorer, scanner, and arena drive the MCP protocol directly
and never call an LLM.

---

## How it's wired

Qt is synchronous and owns its own event loop; the PurpleMCP core is `asyncio`
and spawns MCP servers as stdio subprocesses. The GUI bridges them in
[`purplemcp/gui/async_bridge.py`](../purplemcp/gui/async_bridge.py):

- a **single persistent asyncio loop** runs on a daemon thread;
- one-shot work (list/call a tool, scan, run the arena) is submitted as a
  coroutine and its result comes back on the GUI thread via a Qt signal;
- the Chat Playground holds a **long-lived session task** that owns one
  `MCPHost` + `Agent` for its whole life (so anyio's task-scoped transports open
  and close in the same task) and takes user turns off a queue.

Emitting Qt signals from the loop thread to GUI-thread slots uses queued
connections, which is thread-safe — that's the whole trick.

---

## The pages

### Dashboard
Provider readiness (which keys are set), the registered MCP servers, and lab
stats — attack modules and hardened twins — at a glance.

![Dashboard](images/gui/1_dashboard.png)

### Tool Explorer
Connect to any registered server, browse its tools, read each tool's JSON input
schema, and **call a tool through an auto-generated form**. No model in the loop
— this is the protocol, raw.

![Tool Explorer](images/gui/2_explorer.png)

### Chat Playground
Pick a provider/model and any set of servers, start a session, and chat. As the
agent works, every **tool call and its result stream in live** as inline cards,
so you can see exactly how the model is using the tools.

![Chat Playground](images/gui/3_chat.png)

### Security Scanner
Run the [scanner](../purplemcp/scanner.py) two ways: **static** over a file or
directory (AST analysis — point it at `attacks/` to light it up), or **dynamic**
against a live server's advertised tool definitions. Results come back as a
severity distribution bar, summary pills, and per-finding cards with rule,
location, and detail.

![Security Scanner](images/gui/4_scanner.png)

### Attack / Defend Arena
The signature purple-team demo. Arm the lab, pick an attack, and fire the same
payload at the **vulnerable server and its hardened twin, side by side**. The red
column gets exploited; the blue column blocks it. The verdict on each side is
computed honestly — an explicit "attack-success proof" string plus guardrail
refusal phrases, not a black box.

![Attack/Defend Arena](images/gui/5_arena.png)

The bundled cases map to the attack catalog:

| # | Case | Tool | Guardrail in the hardened twin |
| --- | --- | --- | --- |
| 03 | Command Injection | `ping` | `guardrails.exec.safe_run` (argv, no shell, allowlist) |
| 04 | Path Traversal | `read_doc` | `guardrails.paths.safe_resolve` |
| 05 | SSRF | `fetch` | `guardrails.net.safe_get` |
| 06 | Token Theft | `get_debug_info` | `guardrails.secrets.scrub` |
| 09 | Data Exfiltration | `backup_note` | endpoint allowlist + `scrub` + approval |

---

## Safety

The arena launches intentionally-vulnerable servers, so it is gated exactly like
the CLI lab: nothing insecure starts until you tick **Arm the lab** in the UI,
which is the only thing that injects the `PURPLEMCP_LAB_ENABLED` opt-in token
into a vulnerable server's environment. The sidebar shows a red **Lab ARMED**
indicator while it's on. Exfiltration demos only ever reach a fake local sink.
Read [ETHICS.md](../ETHICS.md) and only run this on a machine you own.

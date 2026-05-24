# ag-trace

**See exactly what your AI agent did.**

Every tool call. Every LLM request. Every file it touched. Every decision it made. Every retry. Every failure. All of it — captured automatically, zero config.

```
ag-trace view

────────────────────────────────────────────────────────────
Session: f6045675  Duration: 2m 05s  Tools: 8  Errors: 1
────────────────────────────────────────────────────────────
▶  +0.00s  START   claude-code
👤  +0.07s  USER    how many tests does this project have?
🔵  +3.55s  TOOL    Glob  **/*.test.*
✅  +3.60s  RESULT  ok  47 files  (51ms)
🔵  +6.06s  TOOL    Bash  $ python -m pytest tests/ -v
❌ +27.65s  RESULT  err exit=1  No module named pytest  [retry→]
🔵 +29.89s  TOOL    Bash  $ uv run --with pytest pytest tests/
✅  +1m43s  RESULT  ok  75 passed  (5.88s)
🤖  +1m52s  AGENT   75 tests, all passing.
■   +1m52s  END     exit=0
────────────────────────────────────────────────────────────

  → 1 error found. Try: ag-trace explain f6045675
  → Cost estimate: ag-trace cost f6045675
  → Full HTML: ag-trace view f6045675 --html out.html
```

---

## Why ag-trace?

AI agents are black boxes. They run, they do things, and you get an answer. But when something goes wrong — a wrong file edited, an unexpected retry loop, a $5 session that should've been $0.05 — you have no idea what happened.

ag-trace captures everything in the background while your agent runs. No code changes. No wrappers. Just run `ag-trace init` once and every Claude Code session is traced automatically.

---

## Install

```bash
pip install ag-trace
```

or with uv:

```bash
uv tool install ag-trace
```

---

## Setup (30 seconds)

```bash
ag-trace init
```

Auto-detects Claude Code, patches your settings, creates the trace directory. Run Claude Code normally after that — traces appear automatically.

```
Initializing ag-trace...

✓ Detected Claude Code at ~/.claude/settings.json
✓ Hooks configured (redaction enabled)
✓ Trace directory ready: .agent-traces/

Ready! Use Claude Code normally.

Quick start:
  ag-trace view          # view latest session
  ag-trace dashboard     # all sessions at a glance
  ag-trace explain       # plain-English breakdown
```

---

## Core Commands

### `ag-trace view` — your main interface

```bash
ag-trace view                          # latest session
ag-trace view abc123                   # specific session
ag-trace view abc123 --html out.html   # export to browser
ag-trace view abc123 --json            # raw JSON events
ag-trace view --no-emoji               # ASCII fallback
```

### `ag-trace explain` — plain English

What did the agent actually do? Why did it retry three times?

```bash
ag-trace explain

Phase 1 (0.07s–27.65s): Tried to run pytest directly — failed, no module found.
Phase 2 (29.89s–1m43s): Retried with uv, found 75 tests, all passing.

2 retries | 1 failure | $0.0042 estimated cost
```

### `ag-trace cost` — money

```bash
ag-trace cost
ag-trace cost --model opus
ag-trace dashboard --trend    # cost over time
```

### `ag-trace diff` — compare sessions

Did the agent behave differently before vs after you changed the prompt?

```bash
ag-trace diff abc123 def456
ag-trace diff abc123 def456 --semantic
```

### `ag-trace watch` — live monitoring

```bash
ag-trace watch
ag-trace watch --rules .agent-rules.json   # kill if cost > $0.50
```

### `ag-trace dashboard` — all sessions

```bash
ag-trace dashboard
ag-trace dashboard --trend          # metrics over time
ag-trace dashboard --html report.html
```

---

## How It Works

ag-trace hooks into Claude Code's lifecycle events:

```
Claude Code runs
  ├── PreToolUse  →  captures tool name + args before execution
  ├── PostToolUse →  captures result + latency after execution
  ├── UserPrompt  →  captures what you asked
  └── Stop        →  captures the final response

All written to: .agent-traces/<session-id>/events.ndjson
```

Every trace is a flat stream of events stored as newline-delimited JSON. No database. No server. Just files — copy them, share them, version-control them.

---

## What Gets Captured

| Event | What You See |
|-------|-------------|
| `tool_call` | Tool name, arguments, exact command |
| `tool_result` | Output, exit code, duration, errors |
| `user_prompt` | What you asked |
| `assistant_response` | What the agent said |
| `error` | Error message, which tool failed, retry chain |
| `file_read` / `file_write` | Which files the agent touched and when |
| `llm_request` / `llm_response` | Token counts, model, latency |
| `session_start` / `session_end` | Duration, exit code, total stats |

---

## More Commands

```bash
ag-trace list                     # list all sessions
ag-trace inspect <id>             # raw JSON dump
ag-trace stats <id>               # tool frequency + timing
ag-trace why <id> <event-num>     # causal chain for an event
ag-trace audit                    # permission audit
ag-trace eval run                 # scoring framework
ag-trace export --format otlp     # send to Datadog / Honeycomb
ag-trace mcp                      # expose traces as MCP tools
```

---

## Export & Integrations

```bash
# OpenTelemetry — Datadog, Honeycomb, New Relic
ag-trace export --format otlp --endpoint https://api.honeycomb.io

# Langfuse
ag-trace export --format langfuse

# JSON / CSV
ag-trace export --format json -o session.json
ag-trace export --format csv -o session.csv
```

---

## MCP Server

Expose your traces as tools so another agent can query them:

```bash
ag-trace mcp
```

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "ag-trace": {
      "command": "ag-trace",
      "args": ["mcp"]
    }
  }
}
```

Now ask Claude: *"Why did that last session retry the Bash tool three times?"*

---

## Trace Storage

```
.agent-traces/
  <session-id>/
    meta.json          ← session metadata (duration, tool counts, cost)
    events.ndjson      ← every event, one JSON object per line
    annotations.jsonl  ← optional notes and bookmarks
```

---

## Secret Redaction

Enabled by default. Scrubs API keys, tokens, AWS credentials, JWTs, and connection strings before writing to disk.

Disable with:
```bash
ag-trace init --no-redact
```

---

## VS Code Extension

Live gutter annotations, status bar cost counter, and event stream panel — all updating in real time as your agent runs.

```
Status bar:  $0.0042 | 8 tools | Bash ●
Gutter:      📖 read 2×   ✏️ modified 1×
```

---

## License

MIT — fork it, build on it, ship it.

Based on [agent-trace](https://github.com/Siddhant-K-code/agent-trace) by Siddhant Khare.

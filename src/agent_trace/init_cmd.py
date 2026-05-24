"""Zero-config initialization for agent-trace."""

import json
import os
import sys
from pathlib import Path


def _find_claude_settings() -> list[Path]:
    """Return candidate paths for Claude Code settings.json, ordered by preference."""
    candidates = []
    # Global Claude Code settings
    global_path = Path.home() / ".claude" / "settings.json"
    candidates.append(global_path)
    # Project-local Claude Code settings
    local_path = Path.cwd() / ".claude" / "settings.json"
    if local_path != global_path:
        candidates.append(local_path)
    return candidates


def _read_settings(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _build_hook_command(event: str, redact: bool = True) -> str:
    cmd = f"agent-strace hook {event}"
    if redact:
        cmd += " --redact"
    return cmd


HOOK_EVENTS = [
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "Stop",
]


def _hooks_already_configured(settings: dict) -> bool:
    """Return True if agent-strace hooks are already in settings."""
    hooks = settings.get("hooks", {})
    for event in HOOK_EVENTS:
        for entry in hooks.get(event, []):
            # Claude Code format: {"matcher": "", "hooks": [{"type": "command", "command": "..."}]}
            for hook in entry.get("hooks", []):
                if "agent-strace" in hook.get("command", ""):
                    return True
    return False


def _patch_settings(settings: dict, redact: bool = True) -> dict:
    """Add agent-strace hooks to settings dict in Claude Code format. Non-destructive."""
    hooks = settings.setdefault("hooks", {})
    for event in HOOK_EVENTS:
        existing = hooks.setdefault(event, [])
        cmd = _build_hook_command(event, redact=redact)
        # Don't duplicate — check inside nested hooks arrays
        already = any(
            any("agent-strace" in h.get("command", "") for h in entry.get("hooks", []))
            for entry in existing
        )
        if not already:
            existing.append({
                "matcher": "",
                "hooks": [{"type": "command", "command": cmd}],
            })
    return settings


def _write_settings(path: Path, settings: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n")


def _create_traces_dir() -> Path:
    traces_dir = Path.cwd() / ".agent-traces"
    traces_dir.mkdir(exist_ok=True)
    return traces_dir


def _check_gitignore() -> None:
    """Ensure .agent-traces/ is NOT in .gitignore (traces are useful to keep)."""
    gitignore = Path.cwd() / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if ".agent-traces" in content:
            sys.stdout.write(
                "  ⚠  .gitignore contains .agent-traces — traces won't be committed.\n"
                "     Remove that line if you want traces shared with your team.\n"
            )


def cmd_init(args) -> None:
    """Zero-config setup: auto-detect Claude Code and patch settings."""
    redact = getattr(args, "redact", True)
    scope = getattr(args, "scope", "global")  # "global" or "local"

    sys.stdout.write("Initializing agent-strace...\n\n")

    # 1. Find settings file
    candidates = _find_claude_settings()
    if scope == "local":
        target = Path.cwd() / ".claude" / "settings.json"
    else:
        target = candidates[0]  # global

    settings = _read_settings(target)

    # 2. Check if already configured
    if _hooks_already_configured(settings):
        sys.stdout.write(f"✓ Hooks already configured in {target}\n")
    else:
        settings = _patch_settings(settings, redact=redact)
        _write_settings(target, settings)
        sys.stdout.write(f"✓ Hooks added to {target}\n")
        if redact:
            sys.stdout.write("  (secret redaction enabled)\n")

    # 3. Create .agent-traces/ directory
    traces_dir = _create_traces_dir()
    sys.stdout.write(f"✓ Trace directory ready: {traces_dir}\n")

    # 4. Check .gitignore
    _check_gitignore()

    # 5. Final message
    sys.stdout.write("\n")
    sys.stdout.write("Ready! Use Claude Code normally — traces are captured automatically.\n")
    sys.stdout.write("\n")
    sys.stdout.write("Quick start:\n")
    sys.stdout.write("  agent-strace view          # view latest session\n")
    sys.stdout.write("  agent-strace dashboard     # all sessions at a glance\n")
    sys.stdout.write("  agent-strace explain       # plain-English breakdown\n")
    sys.stdout.write("\n")

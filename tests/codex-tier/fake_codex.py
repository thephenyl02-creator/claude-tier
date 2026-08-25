#!/usr/bin/env python3
"""Small deterministic Codex CLI double for integration tests."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


EXEC_HELP = """
Usage: codex exec [OPTIONS] [PROMPT]
  --cd <path>
  --model <string>
  --config <key=value>
  --json
  --output-last-message <path>
  --sandbox <read-only|workspace-write|danger-full-access>
"""


def argument_value(arguments: list[str], flag: str) -> str | None:
    try:
        return arguments[arguments.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def run_exec(arguments: list[str]) -> int:
    if "--help" in arguments:
        print(EXEC_HELP)
        return 0
    model = argument_value(arguments, "--model") or ""
    config = argument_value(arguments, "--config") or ""
    sandbox = argument_value(arguments, "--sandbox") or "read-only"
    repo = Path(argument_value(arguments, "--cd") or os.getcwd())
    output = argument_value(arguments, "--output-last-message")
    effort_match = re.search(r'model_reasoning_effort="([^"]+)"', config)
    effort = effort_match.group(1) if effort_match else ""
    packet = sys.stdin.read()

    rejected = os.environ.get("FAKE_CODEX_REJECT_PAIR")
    if rejected == f"{model}/{effort}":
        print(json.dumps({"type": "turn.failed", "error": {"message": "model or effort unavailable"}}))
        print("selected model or effort unavailable", file=sys.stderr)
        return 41
    if "FORCE_FAILURE" in packet:
        print(json.dumps({"type": "turn.failed", "error": {"message": "forced worker failure"}}))
        print("forced worker failure", file=sys.stderr)
        return 42

    sentinel_match = re.search(r"WRITE_SENTINEL=([^\s]+)", packet)
    if sentinel_match and sandbox == "workspace-write":
        target = (repo / sentinel_match.group(1)).resolve()
        if repo.resolve() not in target.parents:
            print("sentinel escaped repository", file=sys.stderr)
            return 43
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("written by fake codex\n", encoding="utf-8")

    final = (
        f"MODEL={model} EFFORT={effort} SANDBOX={sandbox}\n"
        "SUMMARY\nCOUNTS\nEXCLUSIONS\n"
    )
    if output:
        Path(output).write_text(final, encoding="utf-8")
    effort_tokens = {
        "low": 10,
        "medium": 20,
        "high": 30,
        "xhigh": 40,
        "max": 50,
        "ultra": 60,
    }.get(effort, 5)
    print(json.dumps({"type": "thread.started", "thread_id": "fake-thread"}))
    print(
        json.dumps(
            {
                "type": "item.completed",
                "item": {"id": "message", "type": "agent_message", "text": final},
            }
        )
    )
    print(
        json.dumps(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 100,
                    "cached_input_tokens": 20,
                    "output_tokens": 30,
                    "reasoning_output_tokens": effort_tokens,
                    "credits": 0.25,
                },
            }
        )
    )
    return 0


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments:
        print("fake codex")
        return 0
    if arguments == ["--version"]:
        print("codex-cli 1.0.0-test")
        return 0
    if arguments[0] == "exec":
        return run_exec(arguments[1:])
    if arguments[0] == "plugin":
        if len(arguments) >= 2 and arguments[1] == "--help":
            print("Usage: codex plugin <add|list|remove|marketplace>")
            return 0
        if "list" in arguments and "--json" in arguments:
            print(json.dumps({"installed": [], "available": []}))
            return 0
        return 1
    print("unsupported fake command", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

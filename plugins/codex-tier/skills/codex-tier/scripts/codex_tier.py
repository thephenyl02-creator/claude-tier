#!/usr/bin/env python3
"""Deterministic routing, bounded worker execution, and JSONL usage logging."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = SKILL_ROOT / "references"
REGISTRY_PATH = REFERENCE_DIR / "model-registry.json"
FRONTIERS_PATH = REFERENCE_DIR / "frontiers.json"
MEASURED_FRONTIERS_PATH = REFERENCE_DIR / "measured-frontiers.json"
CANDIDATE_MATRIX_PATH = REFERENCE_DIR / "candidate-matrix.json"

COMPLEXITY_ALIASES = {
    "deterministic": "deterministic",
    "mechanical": "mechanical",
    "routine": "routine",
    "substantial": "substantial",
    "frontier": "frontier",
    "ambiguous": "frontier",
    "frontier-ambiguous": "frontier",
}
VOLUME_ALIASES = {
    "tiny": "tiny",
    "one-operation": "tiny",
    "small": "small",
    "few-operations": "small",
    "moderate": "moderate",
    "many-files-items": "large",
    "large": "large",
    "repetitive": "repetitive-high-volume",
    "high-volume": "repetitive-high-volume",
    "repetitive-high-volume": "repetitive-high-volume",
    "long-repetitive-workflow": "repetitive-high-volume",
}
RISK_ALIASES = {
    "low": "low",
    "harmless": "low",
    "harmless-reversible": "low",
    "ordinary": "ordinary",
    "correctness-sensitive": "correctness-sensitive",
    "security-sensitive": "security-sensitive",
    "production-critical": "production-critical",
    "irreversible": "irreversible",
    "destructive-irreversible": "irreversible",
}
CONTEXT_ALIASES = {
    "minimal": "minimal",
    "one-file": "minimal",
    "local": "local",
    "small-local-slice": "local",
    "multi-file": "multi-file",
    "repository-wide": "repository-wide",
    "broad-repository-understanding": "repository-wide",
    "large-context": "large-context",
    "long-multi-turn-reasoning-context": "large-context",
}

COMPLEXITY_FLOOR = {
    "deterministic": 0,
    "mechanical": 42,
    "routine": 60,
    "substantial": 77,
    "frontier": 86,
}
RISK_FLOOR = {
    "low": 40,
    "ordinary": 55,
    "correctness-sensitive": 75,
    "security-sensitive": 84,
    "production-critical": 86,
    "irreversible": 88,
}
CONTEXT_FLOOR = {
    "minimal": 35,
    "local": 45,
    "multi-file": 55,
    "repository-wide": 60,
    "large-context": 70,
}
DEFAULT_MARGIN = {
    "low": 2,
    "ordinary": 4,
    "correctness-sensitive": 6,
    "security-sensitive": 8,
    "production-critical": 9,
    "irreversible": 9,
}

EVENT_FIELDS = (
    "run_id",
    "timestamp",
    "work_class",
    "execution_mode",
    "selected_model",
    "selected_effort",
    "parent_model",
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "codex_usage_credits",
    "worker_count",
    "retry_count",
    "verification_failures",
    "duration_seconds",
    "verification_result",
    "escalated_from",
    "escalated_to",
    "success",
    "error_type",
)


class TierError(RuntimeError):
    """Expected user-facing configuration or execution error."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise TierError(f"Could not load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TierError(f"{path} must contain a JSON object")
    return value


def models_cache_path(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit.expanduser()
    override = os.environ.get("CODEX_TIER_MODELS_CACHE")
    if override:
        return Path(override).expanduser()
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return codex_home / "models_cache.json"


def apply_client_model_cache(
    registry: dict[str, Any], cache_path: Path | None = None
) -> dict[str, Any]:
    """Overlay the current Codex client catalog onto the maintained registry."""

    active = copy.deepcopy(registry)
    path = models_cache_path(cache_path)
    runtime: dict[str, Any] = {
        "source": "registry-snapshot",
        "path": str(path),
        "cache_available": False,
        "fetched_at": None,
        "client_version": None,
    }
    if not path.exists():
        for model in active.get("models", []):
            model["active_available"] = model.get("availability") != "unavailable"
            model["availability_evidence"] = "registry-snapshot"
        active["runtime_discovery"] = runtime
        return active

    try:
        cache = load_json(path)
        listed = {
            item.get("slug"): item
            for item in cache.get("models", [])
            if isinstance(item, dict) and item.get("visibility") == "list" and item.get("slug")
        }
    except TierError as exc:
        runtime["error"] = sanitize_error(str(exc))
        for model in active.get("models", []):
            model["active_available"] = model.get("availability") != "unavailable"
            model["availability_evidence"] = "registry-snapshot-after-cache-error"
        active["runtime_discovery"] = runtime
        return active

    excluded = set(active.get("discovery", {}).get("excluded_efforts", ["none"]))
    known_efforts = set(active.get("effort_order", []))
    runtime.update(
        {
            "source": "codex-model-cache",
            "cache_available": True,
            "fetched_at": cache.get("fetched_at"),
            "client_version": cache.get("client_version"),
        }
    )
    for model in active.get("models", []):
        advertised = listed.get(model.get("id"))
        if not advertised:
            model["active_available"] = False
            model["supported_efforts"] = []
            model["availability_evidence"] = "absent-from-client-cache"
            continue
        efforts = []
        for item in advertised.get("supported_reasoning_levels", []):
            effort = item.get("effort") if isinstance(item, dict) else item
            if effort and effort not in excluded and effort in known_efforts and effort not in efforts:
                efforts.append(effort)
        model["active_available"] = bool(efforts)
        model["supported_efforts"] = efforts
        model["availability_evidence"] = "advertised-by-client-cache"
        model["client_default_effort"] = advertised.get("default_reasoning_level")
        model["client_priority"] = advertised.get("priority")
        model["client_supported_in_api"] = advertised.get("supported_in_api")
    active["runtime_discovery"] = runtime
    return active


def active_candidate_matrix(registry: dict[str, Any]) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    probe_statuses = registry.get("runtime_probe_status", {})
    for model in registry.get("models", []):
        if not model.get("active_available", True):
            continue
        for effort in model.get("supported_efforts", []):
            pair = pair_name(model["id"], effort)
            probe_status = probe_statuses.get(pair)
            matrix.append(
                {
                    "model": model["id"],
                    "effort": effort,
                    "pair": pair,
                    "availability": (
                        "executed"
                        if probe_status == "executed"
                        else "unavailable"
                        if probe_status == "unavailable"
                        else "advertised"
                    ),
                    "evidence": (
                        "real-launch-probe"
                        if probe_status in {"executed", "unavailable"}
                        else model.get("availability_evidence")
                    ),
                }
            )
    return matrix


def candidate_matrix_hash(matrix: list[dict[str, Any]]) -> str:
    pairs = sorted(str(item["pair"]) for item in matrix)
    return hashlib.sha256("\n".join(pairs).encode("utf-8")).hexdigest()


def apply_launch_probe_results(registry: dict[str, Any]) -> dict[str, Any]:
    """Apply real launch-probe status only when it matches the active matrix."""

    active = copy.deepcopy(registry)
    if not CANDIDATE_MATRIX_PATH.exists():
        return active
    try:
        report = load_json(CANDIDATE_MATRIX_PATH)
    except TierError:
        return active
    report_discovery = report.get("model_discovery", {})
    runtime_discovery = active.get("runtime_discovery", {})
    if report_discovery.get("path") != runtime_discovery.get("path"):
        active["runtime_probe_evidence"] = {
            "status": "different-client-scope",
            "path": str(CANDIDATE_MATRIX_PATH),
        }
        return active
    current_hash = candidate_matrix_hash(active_candidate_matrix(active))
    if report.get("candidate_matrix_hash") != current_hash:
        active["runtime_probe_evidence"] = {
            "status": "stale",
            "path": str(CANDIDATE_MATRIX_PATH),
        }
        return active
    statuses = {
        item["pair"]: item.get("status")
        for item in report.get("candidates", [])
        if isinstance(item, dict)
        and item.get("pair")
        and item.get("status") in {"executed", "unavailable"}
    }
    active["runtime_probe_status"] = statuses
    active["runtime_unavailable_pairs"] = sorted(
        pair for pair, status in statuses.items() if status == "unavailable"
    )
    active["runtime_probe_evidence"] = {
        "status": "current",
        "path": str(CANDIDATE_MATRIX_PATH),
        "codex_cli_version": report.get("codex_cli_version"),
        "generated_at": report.get("generated_at"),
        "executed": sum(status == "executed" for status in statuses.values()),
        "unavailable": sum(status == "unavailable" for status in statuses.values()),
    }
    return active


def merge_measured_frontiers(frontiers: dict[str, Any]) -> dict[str, Any]:
    if not MEASURED_FRONTIERS_PATH.exists():
        return frontiers
    measured = load_json(MEASURED_FRONTIERS_PATH)
    if measured.get("status") != "real-codex-measurement":
        return frontiers
    merged = copy.deepcopy(frontiers)
    for work_class, profile in measured.get("profiles", {}).items():
        if work_class not in merged.get("profiles", {}):
            continue
        current = merged["profiles"][work_class]
        routing_decision = profile.get("routing_decision")
        if routing_decision == "parent":
            current["candidates"] = []
            current.pop("availability_fallback_candidates", None)
            current["parent_only"] = True
        elif routing_decision == "validated_worker":
            current["candidates"] = copy.deepcopy(profile.get("candidates", []))
            current.pop("availability_fallback_candidates", None)
            current.pop("parent_only", None)
            current["validated_worker_only"] = True
        elif profile.get("candidates"):
            current["availability_fallback_candidates"] = copy.deepcopy(
                current.get("candidates", [])
            )
            current["candidates"] = copy.deepcopy(profile["candidates"])
        else:
            continue
        current["calibration"] = {
            "source": "real-codex-measurement",
            "measured_at": profile.get("measured_at", measured.get("measured_at")),
            "usage_metric": measured.get("usage_metric"),
            "fixture_id": profile.get("fixture_id"),
            "evidence_file": profile.get("evidence_file"),
            "evidence_sha256": profile.get("evidence_sha256"),
            "routing_decision": routing_decision,
        }
    return merged


def load_config(
    *, cache_path: Path | None = None, include_measured: bool = True
) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = apply_launch_probe_results(
        apply_client_model_cache(load_json(REGISTRY_PATH), cache_path)
    )
    frontiers = load_json(FRONTIERS_PATH)
    return registry, merge_measured_frontiers(frontiers) if include_measured else frontiers


def normalize(value: str) -> str:
    return re.sub(r"-+", "-", value.strip().lower().replace("_", "-").replace("/", "-"))


def normalize_dimension(value: str, aliases: dict[str, str], label: str) -> str:
    key = normalize(value)
    if key not in aliases:
        allowed = ", ".join(sorted(set(aliases.values())))
        raise TierError(f"Unsupported {label} '{value}'. Expected one of: {allowed}")
    return aliases[key]


def pair_name(model: str, effort: str) -> str:
    return f"{model}/{effort}"


def parse_pair(value: str) -> tuple[str, str]:
    if "/" not in value:
        raise TierError(f"Model/effort pair must use MODEL/EFFORT syntax: {value}")
    model, effort = value.rsplit("/", 1)
    if not model or not effort:
        raise TierError(f"Invalid model/effort pair: {value}")
    return model, effort


def registry_models(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in registry.get("models", [])}


def validate_config(registry: dict[str, Any], frontiers: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    models = registry_models(registry)
    effort_order = registry.get("effort_order", [])
    if not models:
        errors.append("registry contains no models")
    if len(effort_order) != len(set(effort_order)):
        errors.append("effort_order contains duplicates")
    if "none" in effort_order:
        errors.append("none is not exposed by the active Codex surface")
    for model_id, model in models.items():
        efforts = model.get("supported_efforts", [])
        configured_efforts = model.get("candidate_efforts", efforts)
        unknown = sorted(set(efforts) - set(effort_order))
        if unknown:
            errors.append(f"{model_id} has unknown efforts: {', '.join(unknown)}")
        configured_unknown = sorted(set(configured_efforts) - set(effort_order))
        if configured_unknown:
            errors.append(
                f"{model_id} has unknown candidate efforts: {', '.join(configured_unknown)}"
            )
        if "none" in configured_efforts:
            errors.append(f"{model_id} still advertises excluded effort none")
    profiles = frontiers.get("profiles", {})
    if not profiles:
        errors.append("frontiers contains no profiles")
    for work_class, profile in profiles.items():
        required = profile.get("required_quality")
        if not isinstance(required, (int, float)) or not 0 <= required <= 100:
            errors.append(f"{work_class} has invalid required_quality")
        if profile.get("parent_only") not in (None, True, False):
            errors.append(f"{work_class} has invalid parent_only flag")
        if profile.get("parent_only") and profile.get("candidates"):
            errors.append(f"{work_class} cannot be parent_only and define candidates")
        if profile.get("validated_worker_only") not in (None, True, False):
            errors.append(f"{work_class} has invalid validated_worker_only flag")
        if profile.get("validated_worker_only"):
            if profile.get("parent_only"):
                errors.append(
                    f"{work_class} cannot be parent_only and validated_worker_only"
                )
            if len(profile.get("candidates", [])) != 1:
                errors.append(
                    f"{work_class} validated_worker_only must define exactly one candidate"
                )
            if profile.get("availability_fallback_candidates"):
                errors.append(
                    f"{work_class} validated_worker_only cannot define availability fallbacks"
                )
        seen: set[str] = set()
        for candidate in profile.get("candidates", []):
            model_id = candidate.get("model")
            effort = candidate.get("effort")
            pair = pair_name(str(model_id), str(effort))
            if pair in seen:
                errors.append(f"{work_class} repeats {pair}")
            seen.add(pair)
            if model_id not in models:
                errors.append(f"{work_class} references unknown model {model_id}")
            elif effort not in models[model_id].get(
                "candidate_efforts", models[model_id].get("supported_efforts", [])
            ):
                errors.append(f"{work_class} references unsupported pair {pair}")
            quality = candidate.get("quality")
            usage = candidate.get("relative_usage")
            if not isinstance(quality, (int, float)) or not 0 <= quality <= 100:
                errors.append(f"{work_class} has invalid quality for {pair}")
            if not isinstance(usage, (int, float)) or usage <= 0:
                errors.append(f"{work_class} has invalid relative_usage for {pair}")
    return errors


def candidate_copy(candidate: dict[str, Any]) -> dict[str, Any]:
    result = dict(candidate)
    result["pair"] = pair_name(result["model"], result["effort"])
    return result


def route_work_unit(
    *,
    work_class: str,
    complexity: str,
    volume: str,
    risk: str,
    context: str,
    quality_margin: int | None = None,
    available_models: list[str] | None = None,
    unavailable_pairs: list[str] | None = None,
    escalate_from: str | None = None,
    parent_model: str | None = None,
    parent_effort: str | None = None,
) -> dict[str, Any]:
    registry, frontiers = load_config()
    errors = validate_config(registry, frontiers)
    if errors:
        raise TierError("Invalid routing configuration: " + "; ".join(errors))

    models = registry_models(registry)
    if (parent_model is None) != (parent_effort is None):
        raise TierError("parent model and effort must be supplied together")
    if parent_model is not None:
        if parent_model not in models:
            raise TierError(f"Unknown parent model: {parent_model}")
        if parent_effort not in models[parent_model].get("supported_efforts", []):
            raise TierError(
                f"Unsupported parent pair: {pair_name(parent_model, str(parent_effort))}"
            )

    profiles = frontiers["profiles"]
    if work_class not in profiles:
        allowed = ", ".join(sorted(profiles))
        raise TierError(f"Unknown work class '{work_class}'. Expected one of: {allowed}")

    complexity = normalize_dimension(complexity, COMPLEXITY_ALIASES, "complexity")
    volume = normalize_dimension(volume, VOLUME_ALIASES, "volume")
    risk = normalize_dimension(risk, RISK_ALIASES, "risk")
    context = normalize_dimension(context, CONTEXT_ALIASES, "context")
    margin = DEFAULT_MARGIN[risk] if quality_margin is None else quality_margin
    if not 0 <= margin <= 20:
        raise TierError("quality margin must be between 0 and 20")

    profile = profiles[work_class]
    required_quality = max(
        profile["required_quality"],
        COMPLEXITY_FLOOR[complexity],
        RISK_FLOOR[risk],
        CONTEXT_FLOOR[context],
    )
    threshold = required_quality + margin
    classification = {
        "complexity": complexity,
        "volume": volume,
        "risk": risk,
        "context": context,
    }
    base: dict[str, Any] = {
        "schema_version": 1,
        "work_class": work_class,
        "classification": classification,
        "required_quality": required_quality,
        "quality_margin": margin,
        "selection_threshold": threshold,
        "selected": None,
        "next_escalation": None,
        "alternatives": [],
        "requires_parent": False,
        "invoking_parent": (
            {
                "model": parent_model,
                "effort": parent_effort,
                "pair": pair_name(parent_model, str(parent_effort)),
            }
            if parent_model is not None
            else None
        ),
    }

    if complexity == "deterministic":
        return {
            **base,
            "execution_mode": "TOOL",
            "reason": "Deterministic commands can reliably prove the result.",
        }

    runtime_available = {
        model_id
        for model_id, model in models.items()
        if model.get("active_available", True) and model.get("supported_efforts")
    }
    available = set(available_models) if available_models is not None else runtime_available
    unknown_models = sorted(available - set(models))
    if unknown_models:
        raise TierError("Unknown available model(s): " + ", ".join(unknown_models))
    unavailable = set(registry.get("runtime_unavailable_pairs", []))
    unavailable.update(unavailable_pairs or [])
    for value in unavailable:
        model, effort = parse_pair(value)
        configured = (
            models.get(model, {}).get("candidate_efforts")
            or models.get(model, {}).get("supported_efforts", [])
        )
        if model not in models or effort not in configured:
            raise TierError(f"Unknown unavailable pair: {value}")

    def available_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            candidate_copy(item)
            for item in items
            if item["model"] in available
            and item["effort"] in models[item["model"]].get("supported_efforts", [])
            and pair_name(item["model"], item["effort"]) not in unavailable
        ]

    if profile.get("validated_worker_only"):
        configured = [candidate_copy(item) for item in profile.get("candidates", [])]
        expected = configured[0]
        expected_pair = expected["pair"]
        if escalate_from:
            if escalate_from != expected_pair:
                raise TierError(f"{escalate_from} is not calibrated for {work_class}")
            return {
                **base,
                "execution_mode": "DIRECT",
                "requires_parent": True,
                "alternatives": [expected],
                "reason": (
                    f"Validated pinned worker {expected_pair} failed verification and no "
                    "alternative route is authorized; keep the unit on the current parent."
                ),
            }
        validated = available_candidates(profile.get("candidates", []))
        if not validated:
            return {
                **base,
                "execution_mode": "DIRECT",
                "requires_parent": True,
                "alternatives": [expected],
                "reason": (
                    f"Validated pinned worker {expected_pair} is unavailable; do not "
                    "substitute an unvalidated worker and keep the unit on the current parent."
                ),
            }
        return {
            **base,
            "execution_mode": "WORKER",
            "selected": validated[0],
            "reason": (
                f"Selected benchmark-validated pinned worker {expected_pair}; the invoking "
                "parent model and effort are not inherited."
            ),
        }

    direct_eligible = (
        volume == "tiny"
        and complexity in {"mechanical", "routine"}
        and risk in {"low", "ordinary"}
        and context in {"minimal", "local"}
        and required_quality <= 68
        and escalate_from is None
    )
    if direct_eligible:
        return {
            **base,
            "execution_mode": "DIRECT",
            "reason": "Worker startup and context packaging would cost more than this tiny unit.",
        }

    if profile.get("parent_only"):
        return {
            **base,
            "execution_mode": "DIRECT",
            "requires_parent": True,
            "reason": "Measured tuning found no cheaper quality-preserving worker; keep the work on the parent.",
        }

    candidates = available_candidates(profile.get("candidates", []))
    used_availability_fallback = False
    if not candidates and profile.get("availability_fallback_candidates"):
        candidates = available_candidates(profile["availability_fallback_candidates"])
        used_availability_fallback = bool(candidates)
    if not candidates:
        return {
            **base,
            "execution_mode": "DIRECT",
            "requires_parent": True,
            "reason": "No calibrated worker pair is available; keep the work on the parent.",
        }

    current_quality = -1
    if escalate_from:
        current_model, current_effort = parse_pair(escalate_from)
        matching = [
            item
            for item in profile.get("candidates", [])
            if item["model"] == current_model and item["effort"] == current_effort
        ]
        if not matching:
            raise TierError(f"{escalate_from} is not calibrated for {work_class}")
        current_quality = matching[0]["quality"]

    viable = [
        item
        for item in candidates
        if item["quality"] >= threshold and item["quality"] > current_quality
    ]
    viable.sort(key=lambda item: (item["relative_usage"], -item["quality"]))
    if not viable:
        strongest = max(candidates, key=lambda item: (item["quality"], -item["relative_usage"]))
        reason = (
            "No stronger calibrated worker remains after the failed candidate."
            if escalate_from
            else "No available calibrated worker clears the quality bar plus confidence margin."
        )
        return {
            **base,
            "execution_mode": "DIRECT",
            "requires_parent": True,
            "reason": reason,
            "alternatives": [strongest],
        }

    selected = viable[0]
    stronger = [
        item
        for item in candidates
        if item["quality"] > selected["quality"]
    ]
    stronger.sort(key=lambda item: (item["relative_usage"], -item["quality"]))
    return {
        **base,
        "execution_mode": "WORKER",
        "selected": selected,
        "next_escalation": stronger[0] if stronger else None,
        "alternatives": viable[1:4],
        "reason": (
            "Selected the cheapest stronger calibrated candidate after verification failed."
            if escalate_from
            else "Selected a prior candidate because every measured-frontier candidate is unavailable."
            if used_availability_fallback
            else "Selected the cheapest calibrated candidate that clears the quality bar and margin."
        ),
    }


def default_log_path() -> Path:
    explicit = os.environ.get("CODEX_TIER_LOG")
    if explicit:
        return Path(explicit).expanduser()
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home).expanduser() if codex_home else Path.home() / ".codex"
    return base / "codex-tier" / "usage.jsonl"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_event(event: dict[str, Any], path: Path | None = None) -> Path:
    target = path or default_log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized: dict[str, Any] = {}
    for field in EVENT_FIELDS:
        value = event.get(field)
        normalized[field] = sanitize_error(value) if isinstance(value, str) else value
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n")
    return target


def sanitize_error(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[REDACTED_KEY]", value)
    text = re.sub(
        r"(?i)\b(api[_-]?key|authorization|password|passwd|token|secret|credential)"
        r"(\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+",
        r"\1\2[REDACTED]",
        text,
    )
    text = re.sub(r"(?i)\bbearer\s+[^\s,;]+", "Bearer [REDACTED]", text)
    return " ".join(text.split())[:1000]


def command_prefix(binary: Path) -> list[str]:
    if binary.suffix.lower() == ".py":
        return [sys.executable, str(binary)]
    if os.name == "nt" and binary.suffix.lower() in {".cmd", ".bat"}:
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", str(binary)]
    return [str(binary)]


def resolve_codex_binary(explicit: str | None = None) -> Path:
    candidate = explicit or os.environ.get("CODEX_TIER_CODEX_BIN") or shutil.which("codex")
    if candidate:
        return Path(candidate).expanduser()
    common = [
        Path.home() / ".local" / "bin" / "codex",
        Path.home() / ".local" / "bin" / "codex.exe",
        Path(os.environ.get("APPDATA", "")) / "npm" / "codex.cmd",
    ]
    for path in common:
        if str(path) and path.exists():
            return path
    raise TierError(
        "A callable Codex CLI was not found. Install the official CLI with "
        "'npm install --global @openai/codex' or use native pinned subagents."
    )


def read_packet(path_value: str) -> str:
    if path_value == "-":
        packet = sys.stdin.read()
    else:
        try:
            packet = Path(path_value).read_text(encoding="utf-8")
        except OSError as exc:
            raise TierError(f"Could not read work packet {path_value}: {exc}") from exc
    if not packet.strip():
        raise TierError("Work packet is empty")
    return packet


def parse_json_events(stdout: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events: list[dict[str, Any]] = []
    usage: dict[str, Any] = {}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        events.append(event)
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
    return events, usage


def summarize_events(events: list[dict[str, Any]]) -> dict[str, int]:
    retry_count = 0
    error_events = 0
    tool_items = 0
    for event in events:
        event_type = event.get("type")
        if event_type == "error":
            error_events += 1
            message = str(event.get("message") or "").lower()
            if "reconnect" in message or "retry" in message:
                retry_count += 1
        item = event.get("item")
        if event_type == "item.completed" and isinstance(item, dict):
            if item.get("type") == "error":
                error_events += 1
            elif item.get("type") not in {"agent_message", "reasoning"}:
                tool_items += 1
    return {
        "retry_count": retry_count,
        "error_event_count": error_events,
        "tool_item_count": tool_items,
    }


def cmd_route(args: argparse.Namespace) -> int:
    decision = route_work_unit(
        work_class=args.work_class,
        complexity=args.complexity,
        volume=args.volume,
        risk=args.risk,
        context=args.context,
        quality_margin=args.quality_margin,
        available_models=args.available_model,
        unavailable_pairs=args.unavailable_pair,
        escalate_from=args.escalate_from,
        parent_model=args.parent_model,
        parent_effort=args.parent_effort,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    registry, frontiers = load_config()
    errors = validate_config(registry, frontiers)
    matrix = active_candidate_matrix(registry)
    result = {
        "valid": not errors,
        "errors": errors,
        "models": len(registry.get("models", [])),
        "active_models": len({item["model"] for item in matrix}),
        "active_candidates": len(matrix),
        "candidate_matrix_hash": candidate_matrix_hash(matrix),
        "model_discovery": registry.get("runtime_discovery"),
        "work_classes": len(frontiers.get("profiles", {})),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 2


def cmd_matrix(args: argparse.Namespace) -> int:
    registry, _ = load_config(
        cache_path=Path(args.models_cache).expanduser() if args.models_cache else None,
        include_measured=False,
    )
    matrix = active_candidate_matrix(registry)
    result = {
        "model_discovery": registry.get("runtime_discovery"),
        "models": [
            {
                "id": model["id"],
                "active_available": model.get("active_available", True),
                "supported_efforts": model.get("supported_efforts", []),
                "availability_evidence": model.get("availability_evidence"),
                "client_default_effort": model.get("client_default_effort"),
            }
            for model in registry.get("models", [])
        ],
        "candidate_count": len(matrix),
        "candidate_matrix_hash": candidate_matrix_hash(matrix),
        "candidates": matrix,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def run_probe(command: list[str], timeout: int = 15) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout[:4000],
            "stderr": sanitize_error(completed.stderr),
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "command": command,
            "exit_code": None,
            "stdout": "",
            "stderr": sanitize_error(str(exc)),
        }


def read_current_config() -> dict[str, Any]:
    config_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    config_path = config_home / "config.toml"
    result: dict[str, Any] = {"path": str(config_path), "model": None, "model_reasoning_effort": None}
    if not config_path.exists():
        return result
    try:
        import tomllib

        with config_path.open("rb") as handle:
            parsed = tomllib.load(handle)
        result["model"] = parsed.get("model")
        result["model_reasoning_effort"] = parsed.get("model_reasoning_effort")
    except (OSError, ValueError) as exc:
        result["error"] = sanitize_error(str(exc))
    return result


def cmd_inspect(args: argparse.Namespace) -> int:
    registry, _ = load_config()
    result: dict[str, Any] = {
        "registry_checked_at": registry.get("checked_at"),
        "registry_models": [
            {
                "id": item["id"],
                "supported_efforts": item["supported_efforts"],
                "active_available": item.get("active_available", True),
                "availability": item["availability"],
                "availability_evidence": item.get("availability_evidence"),
            }
            for item in registry.get("models", [])
        ],
        "active_candidate_count": len(active_candidate_matrix(registry)),
        "model_discovery": registry.get("runtime_discovery"),
        "current_config": read_current_config(),
        "native_subagents": {
            "status": "verify-on-active-surface",
            "model_pin": "requires-active-spawn-tool-contract",
            "effort_pin": "requires-active-spawn-tool-contract",
            "documentation_support": True,
            "inheritance_warning": "Unpinned subagents inherit parent model and effort.",
        },
    }
    try:
        binary = resolve_codex_binary(args.codex_bin)
        prefix = command_prefix(binary)
        result["codex_binary"] = str(binary)
        result["version_probe"] = run_probe(prefix + ["--version"])
        result["exec_probe"] = run_probe(prefix + ["exec", "--help"])
        result["plugin_probe"] = run_probe(prefix + ["plugin", "--help"])
    except TierError as exc:
        result["codex_binary"] = None
        result["cli_error"] = str(exc)
    print(json.dumps(result, indent=2, sort_keys=True))
    probes = [result.get("version_probe"), result.get("exec_probe")]
    return 0 if all(probe and probe.get("exit_code") == 0 for probe in probes) else 2


def cmd_execute(args: argparse.Namespace) -> int:
    registry, _ = load_config()
    models = registry_models(registry)
    if args.model not in models:
        raise TierError(f"Unknown model: {args.model}")
    if args.effort not in models[args.model]["supported_efforts"]:
        raise TierError(f"{args.model} does not support effort {args.effort}")

    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        raise TierError(f"Repository directory does not exist: {repo}")
    packet = read_packet(args.packet_file)
    binary = resolve_codex_binary(args.codex_bin)
    run_id = args.run_id or str(uuid.uuid4())
    log_path = Path(args.log_file).expanduser() if args.log_file else default_log_path()

    cleanup_output = False
    if args.output_file:
        output_path = Path(args.output_file).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        temp = tempfile.NamedTemporaryFile(prefix="codex-tier-", suffix=".txt", delete=False)
        temp.close()
        output_path = Path(temp.name)
        cleanup_output = True

    command = command_prefix(binary)
    if args.approval_policy:
        command.extend(["--ask-for-approval", args.approval_policy])
    command.append("exec")
    if args.ignore_user_config:
        command.append("--ignore-user-config")
    if args.ignore_rules:
        command.append("--ignore-rules")
    command.extend(
        [
            "--cd",
            str(repo),
            "--model",
            args.model,
            "--config",
            f'model_reasoning_effort="{args.effort}"',
            "--sandbox",
            args.sandbox,
            "--json",
            "--ephemeral",
            "--output-last-message",
            str(output_path),
        ]
    )
    if args.skip_git_repo_check:
        command.append("--skip-git-repo-check")
    if args.output_schema:
        schema_path = Path(args.output_schema).expanduser().resolve()
        if not schema_path.is_file():
            raise TierError(f"Output schema does not exist: {schema_path}")
        command.extend(["--output-schema", str(schema_path)])
    command.append("-")
    started = time.monotonic()
    stdout = ""
    stderr = ""
    exit_code = 1
    error_type: str | None = None
    try:
        completed = subprocess.run(
            command,
            input=packet,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.timeout,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        exit_code = completed.returncode
        if exit_code != 0:
            error_type = "worker_failure"
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or "worker timed out"
        exit_code = 124
        error_type = "timeout"
    except OSError as exc:
        stderr = str(exc)
        exit_code = 126
        error_type = "launch_failure"
    duration = round(time.monotonic() - started, 6)

    events, usage = parse_json_events(stdout)
    event_metrics = summarize_events(events)
    final_message = ""
    try:
        if output_path.exists():
            final_message = output_path.read_text(encoding="utf-8")
    except OSError:
        final_message = ""
    if not final_message:
        for event in reversed(events):
            item = event.get("item")
            if (
                event.get("type") == "item.completed"
                and isinstance(item, dict)
                and item.get("type") == "agent_message"
            ):
                final_message = str(item.get("text") or "")
                break

    success = exit_code == 0
    event = {
        "run_id": run_id,
        "timestamp": utc_timestamp(),
        "work_class": args.work_class,
        "execution_mode": "WORKER",
        "selected_model": args.model,
        "selected_effort": args.effort,
        "parent_model": args.parent_model,
        "input_tokens": usage.get("input_tokens"),
        "cached_input_tokens": usage.get("cached_input_tokens"),
        "cache_write_input_tokens": usage.get("cache_write_input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "reasoning_tokens": usage.get("reasoning_output_tokens") or usage.get("reasoning_tokens"),
        "codex_usage_credits": usage.get("credits") or usage.get("usage_credits"),
        "worker_count": 1,
        "retry_count": event_metrics["retry_count"],
        "verification_failures": 1 if args.verification_result == "fail" else 0,
        "duration_seconds": duration,
        "verification_result": args.verification_result,
        "escalated_from": args.escalated_from,
        "escalated_to": pair_name(args.model, args.effort) if args.escalated_from else None,
        "success": success,
        "error_type": error_type,
    }
    written_log = write_event(event, log_path)
    summary = {
        "run_id": run_id,
        "success": success,
        "exit_code": exit_code,
        "selected_model": args.model,
        "selected_effort": args.effort,
        "sandbox": args.sandbox,
        "duration_seconds": duration,
        "usage": usage,
        "event_metrics": event_metrics,
        "final_message": final_message,
        "error": sanitize_error(stderr) if not success else None,
        "log_file": str(written_log),
        "pin_enforcement": {
            "model_argument": args.model,
            "effort_config": args.effort,
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if cleanup_output:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
    return 0 if success else exit_code


def cmd_record(args: argparse.Namespace) -> int:
    event = {
        "run_id": args.run_id or str(uuid.uuid4()),
        "timestamp": utc_timestamp(),
        "work_class": args.work_class,
        "execution_mode": args.execution_mode,
        "selected_model": args.selected_model,
        "selected_effort": args.selected_effort,
        "parent_model": args.parent_model,
        "input_tokens": args.input_tokens,
        "cached_input_tokens": args.cached_input_tokens,
        "cache_write_input_tokens": args.cache_write_input_tokens,
        "output_tokens": args.output_tokens,
        "reasoning_tokens": args.reasoning_tokens,
        "codex_usage_credits": args.codex_usage_credits,
        "worker_count": args.worker_count,
        "retry_count": args.retry_count,
        "verification_failures": args.verification_failures,
        "duration_seconds": args.duration_seconds,
        "verification_result": args.verification_result,
        "escalated_from": args.escalated_from,
        "escalated_to": args.escalated_to,
        "success": args.success,
        "error_type": args.error_type,
    }
    target = Path(args.log_file).expanduser() if args.log_file else default_log_path()
    written = write_event(event, target)
    print(json.dumps({"logged": True, "log_file": str(written), "run_id": event["run_id"]}, indent=2))
    return 0


def add_common_classification(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--work-class", required=True)
    parser.add_argument("--complexity", required=True)
    parser.add_argument("--volume", required=True)
    parser.add_argument("--risk", required=True)
    parser.add_argument("--context", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Codex Tier deterministic router and bounded worker executor"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate registry and frontiers")
    validate_parser.set_defaults(func=cmd_validate)

    matrix_parser = subparsers.add_parser(
        "matrix", help="Build the active candidate matrix from the Codex client model cache"
    )
    matrix_parser.add_argument("--models-cache")
    matrix_parser.set_defaults(func=cmd_matrix)

    route_parser = subparsers.add_parser("route", help="Choose TOOL, DIRECT, or a pinned worker")
    add_common_classification(route_parser)
    route_parser.add_argument("--quality-margin", type=int)
    route_parser.add_argument("--available-model", action="append")
    route_parser.add_argument("--unavailable-pair", action="append")
    route_parser.add_argument("--escalate-from")
    route_parser.add_argument(
        "--parent-model",
        help="Optional invoking parent model for auditable route traces; never inherited by a WORKER.",
    )
    route_parser.add_argument(
        "--parent-effort",
        help="Optional invoking parent effort for auditable route traces; supply with --parent-model.",
    )
    route_parser.set_defaults(func=cmd_route)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect the local Codex execution surface")
    inspect_parser.add_argument("--codex-bin")
    inspect_parser.set_defaults(func=cmd_inspect)

    execute_parser = subparsers.add_parser("execute", help="Run one bounded codex exec worker")
    execute_parser.add_argument("--repo", required=True)
    execute_parser.add_argument("--model", required=True)
    execute_parser.add_argument("--effort", required=True)
    execute_parser.add_argument("--packet-file", default="-")
    execute_parser.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write", "danger-full-access"],
        default="read-only",
    )
    execute_parser.add_argument(
        "--approval-policy",
        choices=["untrusted", "on-request", "never"],
        help="Explicit Codex approval policy; calibration uses never inside read-only fixtures.",
    )
    execute_parser.add_argument("--codex-bin")
    execute_parser.add_argument("--timeout", type=int, default=1800)
    execute_parser.add_argument("--output-file")
    execute_parser.add_argument("--output-schema")
    execute_parser.add_argument("--ignore-user-config", action="store_true")
    execute_parser.add_argument("--ignore-rules", action="store_true")
    execute_parser.add_argument("--skip-git-repo-check", action="store_true")
    execute_parser.add_argument("--log-file")
    execute_parser.add_argument("--run-id")
    execute_parser.add_argument("--work-class", default="unclassified")
    execute_parser.add_argument("--parent-model")
    execute_parser.add_argument("--escalated-from")
    execute_parser.add_argument("--verification-result", default="not-run")
    execute_parser.set_defaults(func=cmd_execute)

    record_parser = subparsers.add_parser("record", help="Record a TOOL, DIRECT, or native worker event")
    record_parser.add_argument("--execution-mode", choices=["TOOL", "DIRECT", "WORKER"], required=True)
    record_parser.add_argument("--work-class", required=True)
    record_parser.add_argument("--selected-model")
    record_parser.add_argument("--selected-effort")
    record_parser.add_argument("--parent-model")
    record_parser.add_argument("--input-tokens", type=int)
    record_parser.add_argument("--cached-input-tokens", type=int)
    record_parser.add_argument("--cache-write-input-tokens", type=int)
    record_parser.add_argument("--output-tokens", type=int)
    record_parser.add_argument("--reasoning-tokens", type=int)
    record_parser.add_argument("--codex-usage-credits", type=float)
    record_parser.add_argument("--worker-count", type=int, default=0)
    record_parser.add_argument("--retry-count", type=int, default=0)
    record_parser.add_argument("--verification-failures", type=int, default=0)
    record_parser.add_argument("--duration-seconds", type=float)
    record_parser.add_argument("--verification-result", default="not-run")
    record_parser.add_argument("--escalated-from")
    record_parser.add_argument("--escalated-to")
    record_parser.add_argument("--success", action=argparse.BooleanOptionalAction, default=True)
    record_parser.add_argument("--error-type")
    record_parser.add_argument("--log-file")
    record_parser.add_argument("--run-id")
    record_parser.set_defaults(func=cmd_record)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except TierError as exc:
        print(json.dumps({"error": str(exc), "success": False}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

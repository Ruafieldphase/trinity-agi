from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import pandas as pd


def _strip_json_comments(raw_text: str) -> str:
    """Remove // and /* */ style comments from JSON-like text.

    This keeps quoted strings untouched so paths/URLs containing // remain valid.
    """
    result: List[str] = []
    it = iter(range(len(raw_text)))
    i = 0
    in_string = False
    escape = False
    quote_char = ""
    length = len(raw_text)

    while i < length:
        ch = raw_text[i]
        if in_string:
            result.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote_char:
                in_string = False
            i += 1
            continue

        if ch in {"\"", "'"}:
            in_string = True
            quote_char = ch
            result.append(ch)
            i += 1
            continue

        if ch == "/" and i + 1 < length:
            nxt = raw_text[i + 1]
            if nxt == "/":
                i += 2
                while i < length and raw_text[i] not in "\r\n":
                    i += 1
                continue
            if nxt == "*":
                i += 2
                while i + 1 < length and not (raw_text[i] == "*" and raw_text[i + 1] == "/"):
                    i += 1
                i += 2
                continue

        result.append(ch)
        i += 1

    return "".join(result)


def load_json(path: Path, *, allow_comments: bool = False) -> Any:
    text = path.read_text(encoding="utf-8")
    if allow_comments:
        text = _strip_json_comments(text)
    return json.loads(text)


@dataclass
class ScenarioRun:
    name: str
    description: Optional[str]
    affect: Optional[float]
    boundary_low: Optional[float]
    boundary_high: Optional[float]
    freedom: Optional[float]
    stability: Optional[float]
    loop_count: Optional[int]
    json_out: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioRun":
        return cls(
            name=data.get("name", ""),
            description=data.get("description"),
            affect=data.get("affect"),
            boundary_low=data.get("boundary_low"),
            boundary_high=data.get("boundary_high"),
            freedom=data.get("freedom"),
            stability=data.get("stability"),
            loop_count=data.get("loop_count"),
            json_out=data.get("json_out"),
        )


def load_runs(config_path: Path) -> List[ScenarioRun]:
    config = load_json(config_path, allow_comments=True)
    runs = config.get("runs") or []
    return [ScenarioRun.from_dict(run) for run in runs]


def summarise_runs(runs: Sequence[ScenarioRun], defaults: Dict[str, Any]) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for run in runs:
        record = {
            "scenario": run.name,
            "description": run.description,
            "affect": run.affect if run.affect is not None else defaults.get("affect"),
            "boundary_low": run.boundary_low if run.boundary_low is not None else defaults.get("boundary_low"),
            "boundary_high": run.boundary_high if run.boundary_high is not None else defaults.get("boundary_high"),
            "freedom": run.freedom if run.freedom is not None else defaults.get("freedom"),
            "stability": run.stability if run.stability is not None else defaults.get("stability"),
            "loop_count": run.loop_count,
            "timeline_file": run.json_out,
        }
        records.append(record)
    return pd.DataFrame(records)


def load_defaults(config_path: Path) -> Dict[str, Any]:
    config = load_json(config_path, allow_comments=True)
    defaults = config.get("defaults") or {}
    return defaults


def load_summaries(summary_path: Path) -> pd.DataFrame:
    payload = load_json(summary_path)
    scenarios = payload.get("scenarios") or []
    return pd.DataFrame(scenarios)


def _load_timeline_file(path: Path) -> Dict[str, Any]:
    try:
        return load_json(path)
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse timeline JSON: {path}") from exc


def _flatten_state(state: Dict[str, Any]) -> Dict[str, Any]:
    flattened: Dict[str, Any] = {}
    for key, value in state.items():
        if isinstance(value, list):
            flattened[key] = "|".join(str(v) for v in value)
        else:
            flattened[key] = value
    return flattened


def build_timeline_records(scenario: str, timeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    initial_state = timeline_data.get("initial_state") or {}
    final_state = timeline_data.get("final_state") or {}
    timeline_steps = timeline_data.get("timeline") or []

    if initial_state:
        record = {"scenario": scenario, "step": 0, "node": "initial"}
        record.update(_flatten_state(initial_state))
        records.append(record)

    for step in timeline_steps:
        record = {
            "scenario": scenario,
            "step": step.get("step"),
            "node": step.get("node"),
        }
        state = step.get("state") or {}
        record.update(_flatten_state(state))
        delta = step.get("delta") or {}
        record["delta_keys"] = "|".join(sorted(delta.keys())) if delta else ""
        records.append(record)

    if final_state and (not records or records[-1].get("step") != "final"):
        record = {"scenario": scenario, "step": sys.maxsize, "node": "final"}
        record.update(_flatten_state(final_state))
        records.append(record)

    return records


def resolve_timeline_paths(
    runs: Sequence[ScenarioRun],
    supplied_paths: Optional[Sequence[Path]],
    root_dir: Path,
) -> Dict[str, Path]:
    resolved: Dict[str, Path] = {}
    if supplied_paths:
        for path in supplied_paths:
            resolved[path.stem] = path

    for run in runs:
        if run.json_out:
            timeline_path = (root_dir / run.json_out).resolve()
            resolved.setdefault(run.name, timeline_path)
    return resolved


def build_timeline_frame(timeline_map: Dict[str, Path]) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for scenario, path in timeline_map.items():
        if not path.exists():
            continue
        timeline_data = _load_timeline_file(path)
        records.extend(build_timeline_records(scenario, timeline_data))
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    numeric_columns = ["affect_amplitude", "freedom_level", "stability_level", "loop_count"]
    for column in numeric_columns:
        if column in df.columns:
            try:
                df[column] = pd.to_numeric(df[column])
            except (ValueError, TypeError):
                # Mixed types (e.g., null/strings) can be left as-is for manual inspection.
                continue
    return df


def ensure_output_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_frame(df: pd.DataFrame, path: Path) -> None:
    if df.empty:
        return
    df.to_csv(path, index=False)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Phase Injection analysis datasets.")
    parser.add_argument("--config", type=Path, default=Path("batch_config.json"), help="Path to batch configuration JSON.")
    parser.add_argument("--summary", type=Path, default=Path("batch_summary.json"), help="Path to batch summary JSON.")
    parser.add_argument(
        "--timeline",
        type=Path,
        nargs="*",
        help="Explicit timeline JSON files (defaults to json_out declared in config runs).",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("outputs/phase_injection"),
        help="Directory to store generated datasets.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    config_path: Path = args.config
    summary_path: Path = args.summary

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary file not found: {summary_path}")

    defaults = load_defaults(config_path)
    runs = load_runs(config_path)

    runs_frame = summarise_runs(runs, defaults)
    summary_frame = load_summaries(summary_path)

    parent_dir = config_path.parent.resolve()
    timeline_map = resolve_timeline_paths(runs, args.timeline, parent_dir)
    timeline_frame = build_timeline_frame(timeline_map)

    ensure_output_directory(args.outdir)
    write_frame(runs_frame, args.outdir / "phase_runs.csv")
    write_frame(summary_frame, args.outdir / "phase_summaries.csv")
    write_frame(timeline_frame, args.outdir / "phase_timeline.csv")


if __name__ == "__main__":
    main()

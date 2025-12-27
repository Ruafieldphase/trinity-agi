#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Boundary Gate (Feeling→CPU Gate) v1

요청(사용자):
- "느낌으로 동영상을 보고 비슷한 경계의 장면에서만 cpu연산을 한다"

구현 원칙:
- 저비용 스캔(=느낌): 낮은 프레임 레이트로, 저해상도 특징만 계산 (메타/수치만)
- CPU 게이트: '경계(장면 전환/선밀도/패턴)' 후보 중, 이전 경계와 "비슷한" 장면에서만
  고해상도 특징(그래도 이미지/텍스트 저장 없이 수치/해시만)을 추가로 계산한다.
- PII/원문(프레임 이미지) 저장 금지: 프레임 자체는 저장하지 않고, 해시/통계만 저장한다.
- RestGate=REST 또는 Safety=BLOCK/REVIEW이면 실행을 멈추고, Idle을 정상으로 기록한다.

입력:
- outputs/obs_recode_intake_latest.json (newest mp4 메타)
- outputs/bridge/constitution_review_latest.json (optional)
- outputs/safety/rest_gate_latest.json (optional)

출력:
- outputs/video_boundary_gate_latest.json
- outputs/video_boundary_gate_history.jsonl
- (선택) inputs/intake/exploration/sessions/auto_experience_<ts>_video_boundary.json
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import cv2  # type: ignore
import numpy as np


WORKSPACE = Path(__file__).resolve().parents[2]
OUTPUTS = WORKSPACE / "outputs"
BRIDGE = OUTPUTS / "bridge"
SAFETY = OUTPUTS / "safety"
SESSIONS = WORKSPACE / "inputs" / "intake" / "exploration" / "sessions"

OBS_INTAKE = OUTPUTS / "obs_recode_intake_latest.json"
CONSTITUTION = BRIDGE / "constitution_review_latest.json"
REST_GATE = SAFETY / "rest_gate_latest.json"

STATE = OUTPUTS / "sync_cache" / "video_boundary_gate_state.json"
OUT_LATEST = OUTPUTS / "video_boundary_gate_latest.json"
OUT_HISTORY = OUTPUTS / "video_boundary_gate_history.jsonl"
METRICS_LATEST = OUTPUTS / "video_boundary_gate_metrics_latest.json"
METRICS_HISTORY = OUTPUTS / "video_boundary_gate_metrics_history.jsonl"


def _utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _sha256_head(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


def _safety_status() -> str:
    c = _load_json(CONSTITUTION) or {}
    st = str((c.get("status") or "")).upper().strip()
    return st or "UNKNOWN"


def _rest_status(now: float) -> str:
    rg = _load_json(REST_GATE) or {}
    st = str((rg.get("status") or "")).upper().strip()
    if st == "REST":
        until = rg.get("rest_until_epoch")
        if until is None:
            return "REST"
        try:
            if float(now) < float(until):
                return "REST"
        except Exception:
            return "REST"
    return "OK"


def _load_state() -> dict[str, Any]:
    return _load_json(STATE) or {}


def _save_state(obj: dict[str, Any]) -> None:
    _atomic_write_json(STATE, obj)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na <= 1e-9 or nb <= 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _dct_phash(gray: np.ndarray) -> str:
    """
    Perceptual hash of grayscale image.
    - returns hex string; no image is stored.
    """
    img = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
    img = np.float32(img)
    dct = cv2.dct(img)
    dct_low = dct[:8, :8]
    med = float(np.median(dct_low[1:, 1:]))
    bits = (dct_low > med).flatten()
    v = 0
    for i, bit in enumerate(bits.tolist()):
        if bit:
            v |= 1 << i
    return f"{v:016x}"


def _edge_hist(gray: np.ndarray, bins: int = 8) -> list[float]:
    g = cv2.GaussianBlur(gray, (3, 3), 0)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)
    # Only count "strong enough" gradients
    thr = float(np.percentile(mag, 75)) if mag.size else 0.0
    mask = mag >= max(1.0, thr)
    ang_sel = ang[mask]
    if ang_sel.size == 0:
        return [0.0] * bins
    hist, _ = np.histogram(ang_sel, bins=bins, range=(0.0, 360.0))
    hist = hist.astype(np.float32)
    hist_sum = float(hist.sum()) or 1.0
    return (hist / hist_sum).tolist()


@dataclass
class SamplePoint:
    t_sec: float
    mean: float
    std: float
    edge_density: float
    scene_delta: float
    boundary_score: float
    similar_to_prior: bool


def _open_video(path: str) -> Optional[cv2.VideoCapture]:
    try:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return None
        return cap
    except Exception:
        return None


def _get_video_duration(cap: cv2.VideoCapture) -> float:
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frames = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)
    if fps > 0.0 and frames > 0.0:
        return frames / fps
    return 0.0


def _read_frame_at(cap: cv2.VideoCapture, t_sec: float) -> Optional[np.ndarray]:
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, float(t_sec) * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            return None
        return frame
    except Exception:
        return None


def _low_cost_features(frame_bgr: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    # "느낌" 스캔: 저해상도/저비용
    small = cv2.resize(frame_bgr, (96, 96), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    mean = float(np.mean(gray))
    std = float(np.std(gray))
    edges = cv2.Canny(gray, threshold1=50, threshold2=120)
    edge_density = float(np.mean(edges > 0))
    return gray, {"mean": mean, "std": std, "edge_density": edge_density}


def _boundary_score(scene_delta: float, edge_density: float) -> float:
    # Normalize deltas to roughly 0..1 range.
    d = max(0.0, min(1.0, scene_delta / 40.0))
    e = max(0.0, min(1.0, edge_density / 0.18))
    return float(0.65 * d + 0.35 * e)


def _make_session(
    now: float,
    *,
    basename: str,
    video_sig: str,
    selected_count: int,
    window_sec: int,
    step_sec: int,
    safety: str,
    rest: str,
) -> Path:
    SESSIONS.mkdir(parents=True, exist_ok=True)
    path = SESSIONS / f"auto_experience_{int(now)}_video_boundary.json"
    payload: dict[str, Any] = {
        "source": "obs_recode_video",
        "title": "video boundary gate",
        "tags": ["video", "boundary", "cpu_gate", "obs_recode"],
        "notes": (
            f"feeling-scan(last {window_sec}s, step {step_sec}s) → "
            f"cpu on similar boundaries only; selected={selected_count}"
        ),
        "timestamp": float(now),
        "where": {"platform": "windows", "layer": "video_boundary_gate"},
        "who": {"role": "agi", "mode": "unconscious"},
        "boundaries": [
            {"polarity": "deny", "text": "프레임/텍스트 원문 저장 금지(해시/통계만)"},
            {"polarity": "deny", "text": "PII/계정/비밀번호/토큰 추출 금지"},
            {"polarity": "allow", "text": "느낌(저비용)→경계 유사 장면에서만 CPU 연산"},
            {"polarity": "allow", "text": "Idle/쉼은 정상 생존"},
        ],
        "comparisons": [],
        "meta": {
            "video_basename": basename,
            "video_sig": video_sig,
            "safety": safety,
            "rest_gate": rest,
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_video_boundary_gate(
    workspace_root: Path,
    *,
    cooldown_sec: int = 30 * 60,
    scan_window_sec: int = 180,
    scan_step_sec: int = 6,
    max_cpu_frames: int = 6,
    similarity_threshold: float = 0.92,
    edge_density_threshold: float = 0.16,
    bootstrap_cpu_frames: int = 2,
) -> dict[str, Any]:
    now = time.time()
    safety = _safety_status()
    rest = _rest_status(now)

    if safety in ("BLOCK", "REVIEW"):
        res = {
            "ok": True,
            "skipped": True,
            "reason": f"safety={safety}",
            "scanned_at_utc": _utc_iso(now),
        }
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    if rest == "REST":
        res = {
            "ok": True,
            "skipped": True,
            "reason": "rest_gate=REST",
            "scanned_at_utc": _utc_iso(now),
        }
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    intake = _load_json(OBS_INTAKE) or {}
    newest = intake.get("newest") if isinstance(intake.get("newest"), dict) else {}
    video_path = str(newest.get("path") or "")
    mtime_iso = str(newest.get("mtime_iso") or "")
    size = newest.get("size")
    if not video_path or not mtime_iso:
        res = {"ok": True, "skipped": True, "reason": "no_video", "scanned_at_utc": _utc_iso(now)}
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    video_sig = f"{Path(video_path).name}|{mtime_iso}|{size}"
    st = _load_state()
    last_sig = str(st.get("last_video_sig") or "")
    last_run = float(st.get("last_run_epoch") or 0.0)
    if last_sig == video_sig and (now - last_run) < float(cooldown_sec):
        res = {
            "ok": True,
            "skipped": True,
            "reason": "cooldown",
            "scanned_at_utc": _utc_iso(now),
            "video_basename": Path(video_path).name,
        }
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    cap = _open_video(video_path)
    if cap is None:
        res = {"ok": False, "error": "video_open_failed", "scanned_at_utc": _utc_iso(now)}
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    dur = _get_video_duration(cap)
    if dur <= 1.0:
        cap.release()
        res = {"ok": False, "error": "unknown_duration", "scanned_at_utc": _utc_iso(now)}
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    start = max(0.0, dur - float(scan_window_sec))
    times = []
    t = start
    while t <= dur:
        times.append(float(t))
        t += float(scan_step_sec)
        if len(times) >= 200:
            break

    prior_centroid = st.get("boundary_centroid")
    prior_vec = None
    if isinstance(prior_centroid, list) and len(prior_centroid) == 3:
        try:
            prior_vec = np.array([float(x) for x in prior_centroid], dtype=np.float32)
        except Exception:
            prior_vec = None

    sampled: list[SamplePoint] = []
    prev_gray: Optional[np.ndarray] = None
    prev_feat = None

    candidates: list[tuple[float, float, np.ndarray, dict[str, float], np.ndarray]] = []
    candidate_reason_counts = {"strong": 0, "edge": 0, "similar": 0}
    for tt in times:
        frame = _read_frame_at(cap, tt)
        if frame is None:
            continue
        gray, feat = _low_cost_features(frame)

        scene_delta = 0.0
        if prev_gray is not None:
            scene_delta = float(np.mean(np.abs(gray.astype(np.float32) - prev_gray.astype(np.float32))))
        prev_gray = gray
        prev_feat = feat

        bscore = _boundary_score(scene_delta, float(feat["edge_density"]))

        vec = np.array([feat["edge_density"], scene_delta / 40.0, feat["std"] / 64.0], dtype=np.float32)
        sim = _cosine(vec, prior_vec) if prior_vec is not None else 0.0
        similar = bool(sim >= float(similarity_threshold)) if prior_vec is not None else False

        sampled.append(
            SamplePoint(
                t_sec=float(tt),
                mean=float(feat["mean"]),
                std=float(feat["std"]),
                edge_density=float(feat["edge_density"]),
                scene_delta=float(scene_delta),
                boundary_score=float(bscore),
                similar_to_prior=bool(similar),
            )
        )

        # Candidate boundary:
        # - strong scene change OR
        # - "경계 패턴"(선밀도)이 충분히 높음(모델링/와이어/텍스트 경계 등) OR
        # - prior boundary와 유사(learned centroid)
        strong = bscore >= 0.55
        edge = float(feat["edge_density"]) >= float(edge_density_threshold)
        sim_ok = prior_vec is not None and similar and bscore >= 0.30
        if strong or edge or sim_ok:
            if strong:
                candidate_reason_counts["strong"] += 1
            if edge:
                candidate_reason_counts["edge"] += 1
            if sim_ok:
                candidate_reason_counts["similar"] += 1
            candidates.append((float(tt), float(bscore), gray, feat, vec))

    cap.release()

    # Sort candidates: prefer "similar boundary" + higher score.
    candidates.sort(key=lambda x: x[1], reverse=True)
    cpu_frames: list[dict[str, Any]] = []
    cpu_vecs: list[np.ndarray] = []
    cpu_similar_count = 0

    for tt, bscore, gray, feat, vec in candidates[: max_cpu_frames * 3]:
        # CPU gate: only if similar to prior OR very strong boundary.
        sim = _cosine(vec, prior_vec) if prior_vec is not None else 0.0
        allow_cpu = False
        if prior_vec is None:
            # Bootstrap: 최초 1~2회는 "경계 패턴"을 학습(centroid 생성)하기 위해 최소 CPU 허용.
            allow_cpu = float(feat["edge_density"]) >= float(edge_density_threshold)
        else:
            allow_cpu = sim >= similarity_threshold
        if not allow_cpu:
            continue

        if prior_vec is not None and sim >= similarity_threshold:
            cpu_similar_count += 1

        ph = _dct_phash(gray)
        eh = _edge_hist(cv2.resize(gray, (256, 256), interpolation=cv2.INTER_AREA))
        cpu_frames.append(
            {
                "t_sec": float(tt),
                "boundary_score": float(bscore),
                "similarity": float(sim),
                "phash": ph,
                "edge_hist": eh,
                "features": {
                    "mean": float(feat["mean"]),
                    "std": float(feat["std"]),
                    "edge_density": float(feat["edge_density"]),
                },
            }
        )
        cpu_vecs.append(vec)
        if prior_vec is None and len(cpu_frames) >= int(bootstrap_cpu_frames):
            break
        if len(cpu_frames) >= max_cpu_frames:
            break

    # Update centroid (learned boundary feel)
    new_centroid = prior_vec
    if cpu_vecs:
        m = np.mean(np.stack(cpu_vecs, axis=0), axis=0)
        if prior_vec is None:
            new_centroid = m
        else:
            # gentle update
            new_centroid = (0.85 * prior_vec) + (0.15 * m)

    session_path: Optional[Path] = None
    if cpu_frames:
        session_path = _make_session(
            now,
            basename=Path(video_path).name,
            video_sig=_sha256_head(video_sig),
            selected_count=len(cpu_frames),
            window_sec=int(scan_window_sec),
            step_sec=int(scan_step_sec),
            safety=safety,
            rest=rest,
        )

    st_out = {
        "last_run_epoch": float(now),
        "last_video_sig": video_sig,
        "boundary_centroid": (new_centroid.tolist() if new_centroid is not None else None),
    }
    # Accumulated counters (bounded)
    try:
        total_runs = int(st.get("total_runs") or 0) + 1
    except Exception:
        total_runs = 1
    try:
        total_cpu_frames = int(st.get("total_cpu_frames") or 0) + int(len(cpu_frames))
    except Exception:
        total_cpu_frames = int(len(cpu_frames))
    try:
        total_sampled = int(st.get("total_sampled_points") or 0) + int(len(sampled))
    except Exception:
        total_sampled = int(len(sampled))

    seen = st.get("seen_phash") if isinstance(st.get("seen_phash"), list) else []
    seen_set = {str(x) for x in seen if isinstance(x, str)}
    for cf in cpu_frames:
        try:
            ph = str(cf.get("phash") or "")
            if ph:
                seen_set.add(ph)
        except Exception:
            pass
    # Keep only a bounded window for state file size
    seen_list = sorted(seen_set)
    if len(seen_list) > 400:
        seen_list = seen_list[-400:]

    st_out.update(
        {
            "total_runs": total_runs,
            "total_cpu_frames": total_cpu_frames,
            "total_sampled_points": total_sampled,
            "seen_phash": seen_list,
        }
    )
    _save_state(st_out)

    res = {
        "ok": True,
        "scanned_at_utc": _utc_iso(now),
        "safety": safety,
        "rest_gate": rest,
        "video": {
            "basename": Path(video_path).name,
            "sig": _sha256_head(video_sig),
            "duration_sec_est": float(dur),
            "window_start_sec": float(start),
            "window_sec": int(scan_window_sec),
            "step_sec": int(scan_step_sec),
        },
        "sample_count": len(sampled),
        "sampled_points": [asdict(x) for x in sampled[:80]],
        "cpu_frames": cpu_frames,
        "cpu_ran": bool(cpu_frames),
        "session_file": str(session_path) if session_path else None,
        "decision": {
            "reason": "cpu_on_similar_boundaries" if cpu_frames else "no_similar_boundary_found",
            "cpu_frames": len(cpu_frames),
        },
    }
    _atomic_write_json(OUT_LATEST, res)
    _append_jsonl(OUT_HISTORY, res)

    metrics = {
        "ok": True,
        "timestamp_utc": _utc_iso(now),
        "video_sig": _sha256_head(video_sig),
        "has_prior_centroid": bool(prior_vec is not None),
        "centroid_updated": bool(cpu_vecs),
        "scan": {
            "window_sec": int(scan_window_sec),
            "step_sec": int(scan_step_sec),
            "sample_count": int(len(sampled)),
        },
        "candidates": {
            "count": int(len(candidates)),
            "reasons": candidate_reason_counts,
        },
        "cpu_gate": {
            "threshold_similarity": float(similarity_threshold),
            "threshold_edge_density": float(edge_density_threshold),
            "bootstrap_cpu_frames": int(bootstrap_cpu_frames),
            "cpu_frames": int(len(cpu_frames)),
            "cpu_similar_frames": int(cpu_similar_count),
        },
        "accumulated": {
            "total_runs": int(st_out.get("total_runs") or 0),
            "total_cpu_frames": int(st_out.get("total_cpu_frames") or 0),
            "total_sampled_points": int(st_out.get("total_sampled_points") or 0),
            "unique_phash_observed": int(len(seen_list)),
        },
    }
    _atomic_write_json(METRICS_LATEST, metrics)
    _append_jsonl(METRICS_HISTORY, metrics)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(WORKSPACE))
    ap.add_argument("--force", action="store_true", help="Ignore cooldown (for manual verification).")
    ap.add_argument("--cooldown-sec", type=int, default=30 * 60)
    ap.add_argument("--window-sec", type=int, default=180)
    ap.add_argument("--step-sec", type=int, default=6)
    ap.add_argument("--max-cpu-frames", type=int, default=6)
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    cooldown = 0 if bool(args.force) else int(args.cooldown_sec)
    # env override
    import os

    if str(os.environ.get("AGI_VIDEO_GATE_FORCE") or "").strip() in ("1", "true", "TRUE", "yes", "YES"):
        cooldown = 0

    run_video_boundary_gate(
        ws,
        cooldown_sec=int(cooldown),
        scan_window_sec=int(args.window_sec),
        scan_step_sec=int(args.step_sec),
        max_cpu_frames=int(args.max_cpu_frames),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

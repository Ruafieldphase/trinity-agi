#!/usr/bin/env python
"""
acoustic_probe.py

Conceptual acoustic "sonar-like" probing utility for a physical space or (in simulation mode) a hypothetical system structure.

Features:
- Generate logarithmic or linear frequency sweep (chirp) signal.
- (Optional) Playback sweep and record response (requires sounddevice).
- Simulation mode: synthesize an impulse response with configurable resonant peaks.
- Deconvolution (estimate impulse response) via FFT division.
- Peak detection on estimated impulse response / frequency response.
- Output JSON (machine readable) and Markdown (human readable) reports under outputs/.

This is a conceptual diagnostic tool – real acoustic probing requires controlled environment,
calibration, proper hardware, and signal processing refinements (windowing, compensation,
noise handling, time-alignment, etc.). Use this as a starting point / PoC.

Usage examples:
  python scripts/acoustic_probe.py --simulate --peaks 120,440,880
  python scripts/acoustic_probe.py --simulate --hours 24 --log-sweep
  python scripts/acoustic_probe.py --record-seconds 5 --playback --device 1
  python scripts/acoustic_probe.py --playback --record-seconds 8 --log-sweep --f-start 40 --f-end 12000

If sounddevice is not installed or no audio hardware is present, only simulation mode will work.

Limitations / Simple Approach:
- Basic FFT based deconvolution; no regularization.
- Simple peak pick (local maxima above threshold).
- Fallback pure-Python DFT/IDFT if numpy is unavailable (slower, acceptable for short signals).
"""
from __future__ import annotations
import argparse
import math
import json
import time
import os
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

# Attempt to import numpy; provide minimal fallbacks if missing.
try:
    import numpy as np
except Exception:
    np = None  # type: ignore

# Try optional audio dependency.
try:
    import sounddevice as sd  # type: ignore
except Exception:
    sd = None  # type: ignore

OUTPUT_DIR = os.path.join(os.getcwd(), 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def _ensure_np_array(x):
    if np is not None:
        return np.array(x, dtype=float)
    # Fallback: keep as list
    return list(map(float, x))

def _linspace(start: float, stop: float, num: int):
    if np is not None:
        return np.linspace(start, stop, num)
    step = (stop - start) / (num - 1)
    return [start + i * step for i in range(num)]

def _fft(x):
    if np is not None:
        return np.fft.rfft(x)
    # naive DFT (real -> complex) for rfft equivalent (returns N//2+1 bins)
    N = len(x)
    out = []
    for k in range(N // 2 + 1):
        re = 0.0
        im = 0.0
        for n, xn in enumerate(x):
            angle = 2 * math.pi * k * n / N
            re += xn * math.cos(-angle)
            im += xn * math.sin(-angle)
        out.append(complex(re, im))
    return out

def _ifft_rfft(X, N):
    if np is not None:
        # Need full spectrum for irfft. Reconstruct symmetric.
        full = np.zeros(N, dtype=complex)
        full[:len(X)] = X
        # Mirror (excluding DC and Nyquist if present)
        for k in range(1, len(X)-1):
            full[N-k] = np.conjugate(X[k])
        return np.fft.ifft(full).real
    # naive inverse
    out = []
    for n in range(N):
        val = 0j
        for k in range(len(X)):
            angle = 2 * math.pi * k * n / N
            val += X[k] * complex(math.cos(angle), math.sin(angle))
        # For mirrored part
        for k in range(1, len(X)-1):
            angle = 2 * math.pi * (N-k) * n / N
            val += complex(X[k].real, -X[k].imag) * complex(math.cos(angle), math.sin(angle))
        out.append(val.real / N)
    return out

@dataclass
class ProbeConfig:
    sample_rate: int = 44100
    duration: float = 5.0
    f_start: float = 40.0
    f_end: float = 16000.0
    log_sweep: bool = False
    playback: bool = False
    record_seconds: float = 0.0
    device: Optional[int] = None
    simulate: bool = False
    sim_peaks: List[float] = None
    sim_q: float = 50.0  # Controls resonance sharpness
    peak_threshold: float = 0.15
    hours: Optional[int] = None  # For conceptual long window simulation labeling

@dataclass
class ProbeResult:
    mode: str
    timestamp: str
    config: ProbeConfig
    detected_peaks: List[Tuple[float, float]]  # (frequency, magnitude)
    notes: List[str]
    impulse_response_summary: dict
    frequency_response_peaks: List[Tuple[float, float]]


def generate_sweep(cfg: ProbeConfig):
    N = int(cfg.sample_rate * cfg.duration)
    t = _linspace(0.0, cfg.duration, N)
    sweep = []
    if cfg.log_sweep:
        # logarithmic chirp
        K = cfg.duration
        w1 = 2 * math.pi * cfg.f_start
        w2 = 2 * math.pi * cfg.f_end
        B = K / math.log(w2 / w1)
        for tt in t:
            phase = w1 * B * (math.exp(tt / B) - 1.0)
            sweep.append(math.sin(phase))
    else:
        # linear chirp
        for tt in t:
            f = cfg.f_start + (cfg.f_end - cfg.f_start) * (tt / cfg.duration)
            sweep.append(math.sin(2 * math.pi * f * tt))
    # Amplitude fade in/out (Hann edges) to reduce clicks
    for i in range(N):
        edge = min(i / (N * 0.02 + 1e-9), (N - i - 1) / (N * 0.02 + 1e-9), 1.0)
        sweep[i] *= edge
    return _ensure_np_array(sweep)


def simulate_response(cfg: ProbeConfig, sweep):
    # Create synthetic impulse response containing resonant peaks.
    if cfg.sim_peaks is None or len(cfg.sim_peaks) == 0:
        sim_peaks = [120.0, 440.0, 880.0]  # default resonances
    else:
        sim_peaks = cfg.sim_peaks
    N = len(sweep)
    sr = cfg.sample_rate
    # start with small random noise baseline
    if np is not None:
        ir = np.random.randn(N) * 0.001
    else:
        import random
        ir = [ (random.random() * 2 - 1) * 0.001 for _ in range(N) ]
    # Add decaying resonant sinusoids
    for f in sim_peaks:
        decay = math.exp(-f / (cfg.sim_q * 10.0))
        for n in range(N):
            tt = n / sr
            amp = math.exp(-tt * f / cfg.sim_q)
            val = math.sin(2 * math.pi * f * tt) * amp * decay
            if np is not None:
                ir[n] += val
            else:
                ir[n] = ir[n] + val
    # Convolve sweep with impulse response (circular approx)
    if np is not None:
        S = np.fft.rfft(sweep)
        H = np.fft.rfft(ir)
        R = np.fft.irfft(S * H, n=len(sweep))
        return R, ir
    else:
        # naive convolution (short) – for speed we limit length
        R = [0.0] * N
        max_len = min(N, 5000)  # crude limit
        for i in range(max_len):
            for j in range(max_len - i):
                if i + j < N:
                    R[i + j] += sweep[i] * ir[j]
        return R, ir


def record_response(cfg: ProbeConfig, sweep):
    if sd is None:
        raise RuntimeError("sounddevice not available. Install with: pip install sounddevice")
    sr = cfg.sample_rate
    if cfg.playback:
        sd.play(sweep, sr)
    duration = cfg.record_seconds if cfg.record_seconds > 0 else cfg.duration
    rec = sd.rec(int(sr * duration), samplerate=sr, channels=1, dtype='float32')
    sd.wait()
    if cfg.playback:
        sd.stop()
    return rec.flatten()


def estimate_impulse_response(cfg: ProbeConfig, sweep, response):
    # Deconvolution via FFT division.
    N = len(sweep)
    S = _fft(sweep)
    R = _fft(response)
    # Avoid divide by zero.
    H = []
    for k in range(len(S)):
        denom = S[k]
        if abs(denom) < 1e-9:
            H.append(0j)
        else:
            H.append(R[k] / denom)
    ir = _ifft_rfft(H, N)
    # Simple normalization
    if np is not None:
        ir_arr = np.array(ir)
        peak = max(abs(ir_arr.max()), abs(ir_arr.min()), 1e-9)
        ir_arr /= peak
        return ir_arr
    else:
        peak = max(max(ir), -min(ir), 1e-9)
        return [v / peak for v in ir]


def detect_peaks(signal, sample_rate, cfg: ProbeConfig, max_peaks=20):
    # Very simple local maxima detection.
    peaks = []
    N = len(signal)
    if np is not None:
        arr = np.array(signal)
        # Consider absolute
        abs_arr = np.abs(arr)
        threshold = cfg.peak_threshold * abs_arr.max()
        for i in range(1, N - 1):
            if abs_arr[i] > threshold and abs_arr[i] > abs_arr[i-1] and abs_arr[i] > abs_arr[i+1]:
                t = i / sample_rate
                # Convert time location to approximate frequency if resonance (rough heuristic)
                # Using distance between peaks isn't trivial; here assume early peaks correlate with resonances.
                freq_est = 1.0 / (t + 1e-6)
                peaks.append((freq_est, float(abs_arr[i])))
                if len(peaks) >= max_peaks:
                    break
    else:
        abs_arr = [abs(v) for v in signal]
        mval = max(abs_arr)
        threshold = cfg.peak_threshold * mval
        for i in range(1, N - 1):
            if abs_arr[i] > threshold and abs_arr[i] > abs_arr[i-1] and abs_arr[i] > abs_arr[i+1]:
                t = i / sample_rate
                freq_est = 1.0 / (t + 1e-6)
                peaks.append((freq_est, abs_arr[i]))
                if len(peaks) >= max_peaks:
                    break
    return peaks


def format_markdown(result: ProbeResult) -> str:
    lines = []
    cfg = result.config
    lines.append(f"# Acoustic Probe Report ({result.mode})\n")
    lines.append(f"Timestamp: {result.timestamp}\n")
    lines.append("## Configuration\n")
    for k, v in asdict(cfg).items():
        lines.append(f"- **{k}**: {v}")
    lines.append("\n## Detected Time-Domain Peaks (Impulse Response heuristic)\n")
    if result.detected_peaks:
        for f, mag in result.detected_peaks:
            lines.append(f"- freq_est ≈ {f:.2f} Hz (mag {mag:.3f})")
    else:
        lines.append("(none above threshold)")
    lines.append("\n## Frequency Response Peaks (simple mapping)\n")
    if result.frequency_response_peaks:
        for f, mag in result.frequency_response_peaks:
            lines.append(f"- {f:.2f} Hz (mag {mag:.3f})")
    else:
        lines.append("(none)")
    lines.append("\n## Impulse Response Summary\n")
    for k, v in result.impulse_response_summary.items():
        lines.append(f"- {k}: {v}")
    lines.append("\n## Notes\n")
    for n in result.notes:
        lines.append(f"- {n}")
    return "\n".join(lines) + "\n"


def summarize_impulse_response(ir):
    if np is not None:
        arr = np.array(ir)
        return {
            'length': int(len(arr)),
            'max': float(arr.max()),
            'min': float(arr.min()),
            'mean_abs': float(np.mean(np.abs(arr))),
        }
    else:
        return {
            'length': len(ir),
            'max': max(ir),
            'min': min(ir),
            'mean_abs': sum(abs(v) for v in ir) / len(ir),
        }


def main():
    ap = argparse.ArgumentParser(description="Acoustic sonar-like probing tool (conceptual)")
    ap.add_argument('--sample-rate', type=int, default=44100)
    ap.add_argument('--duration', type=float, default=5.0)
    ap.add_argument('--f-start', type=float, default=40.0)
    ap.add_argument('--f-end', type=float, default=16000.0)
    ap.add_argument('--log-sweep', action='store_true')
    ap.add_argument('--playback', action='store_true')
    ap.add_argument('--record-seconds', type=float, default=0.0)
    ap.add_argument('--device', type=int, default=None)
    ap.add_argument('--simulate', action='store_true')
    ap.add_argument('--peaks', type=str, default="")
    ap.add_argument('--sim-q', type=float, default=50.0)
    ap.add_argument('--peak-threshold', type=float, default=0.15)
    ap.add_argument('--hours', type=int, default=None, help='Conceptual window labeling for resonance mapping')
    ap.add_argument('--out-prefix', type=str, default='acoustic_probe')
    args = ap.parse_args()

    sim_peaks = []
    if args.peaks:
        for p in args.peaks.split(','):
            p = p.strip()
            if p:
                try:
                    sim_peaks.append(float(p))
                except ValueError:
                    print(f"Warning: invalid peak '{p}' ignored", file=sys.stderr)
    cfg = ProbeConfig(
        sample_rate=args.sample_rate,
        duration=args.duration,
        f_start=args.f_start,
        f_end=args.f_end,
        log_sweep=args.log_sweep,
        playback=args.playback,
        record_seconds=args.record_seconds,
        device=args.device,
        simulate=args.simulate,
        sim_peaks=sim_peaks,
        sim_q=args.sim_q,
        peak_threshold=args.peak_threshold,
        hours=args.hours
    )

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    notes = []

    if cfg.playback or cfg.record_seconds > 0:
        if sd is None:
            notes.append("sounddevice not available; playback/record disabled")
            cfg.playback = False
            cfg.record_seconds = 0
        elif cfg.device is not None:
            try:
                sd.default.device = cfg.device
                notes.append(f"Using audio device index {cfg.device}")
            except Exception as e:
                notes.append(f"Failed to set device {cfg.device}: {e}")

    sweep = generate_sweep(cfg)
    if cfg.simulate:
        response, true_ir = simulate_response(cfg, sweep)
        mode = 'simulation'
        notes.append("Simulation mode: synthetic resonances injected.")
    else:
        if cfg.record_seconds > 0 or cfg.playback:
            try:
                response = record_response(cfg, sweep)
                true_ir = None
                mode = 'live'
            except Exception as e:
                notes.append(f"Recording failed: {e}")
                response = sweep  # fallback
                true_ir = None
                mode = 'fallback-self'
        else:
            notes.append("No playback/record requested; using sweep as self-response fallback.")
            response = sweep
            true_ir = None
            mode = 'self'

    est_ir = estimate_impulse_response(cfg, sweep, response)
    ir_summary = summarize_impulse_response(est_ir)
    # Time-domain peaks
    td_peaks = detect_peaks(est_ir, cfg.sample_rate, cfg)

    # Frequency response: FFT magnitude of impulse response
    IR_F = _fft(est_ir)
    fr_peaks = []
    # Simple mapping using magnitude threshold
    mags = [abs(c) for c in IR_F]
    if mags:
        maxmag = max(mags)
        thr = cfg.peak_threshold * maxmag
        for i, m in enumerate(mags):
            if m >= thr:
                # Map bin to frequency
                freq = i * cfg.sample_rate / (2 * (len(mags) - 1))  # approximate for rfft bins
                fr_peaks.append((freq, float(m)))
        # Sort by magnitude desc and keep top 25
        fr_peaks.sort(key=lambda x: x[1], reverse=True)
        fr_peaks = fr_peaks[:25]

    result = ProbeResult(
        mode=mode,
        timestamp=timestamp,
        config=cfg,
        detected_peaks=td_peaks,
        notes=notes,
        impulse_response_summary=ir_summary,
        frequency_response_peaks=fr_peaks,
    )

    json_path = os.path.join(OUTPUT_DIR, f"{args.out_prefix}_{timestamp}.json")
    md_path = os.path.join(OUTPUT_DIR, f"{args.out_prefix}_{timestamp}.md")

    with open(json_path, 'w', encoding='utf-8') as f:
        # Convert dataclasses to serializable
        data = asdict(result)
        data['config'] = asdict(result.config)
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(format_markdown(result))

    print(f"JSON report written: {json_path}")
    print(f"Markdown report written: {md_path}")
    print("Peak summary (time-domain heuristic):")
    for f, m in td_peaks[:10]:
        print(f"  ~{f:.1f} Hz (mag {m:.3f})")
    print("Frequency response top peaks:")
    for f, m in fr_peaks[:10]:
        print(f"  {f:.1f} Hz (mag {m:.3f})")

    if true_ir is not None:
        print("(Simulation) True IR first 10 samples:", true_ir[:10])

if __name__ == '__main__':
    main()

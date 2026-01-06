import math
import random
import statistics
import sys


def generate_seasonal_series(days=7, interval_minutes=5, amplitude=10.0, noise_sigma=0.8):
    points_per_day = (24 * 60) // interval_minutes
    n = days * points_per_day
    series = []
    for t in range(n):
        # Daily seasonality as a sine wave [0..2pi) per day
        phase = 2 * math.pi * (t % points_per_day) / points_per_day
        baseline = amplitude * math.sin(phase)
        noise = random.gauss(0.0, noise_sigma)
        series.append(baseline + noise)
    return series, points_per_day


def inject_anomaly(series, points_per_day, day=5, minute=12 * 60, spike=8.0):
    idx = day * points_per_day + (minute // 5)
    if 0 <= idx < len(series):
        series[idx] += spike
    return idx


def seasonal_zscore_detect(series, period, z_thresh=4.0):
    """Leave-one-out seasonal z-score detection.
    For each position-in-period, compute mean/std excluding the current sample
    to avoid the anomaly inflating its own baseline.
    """
    # Pre-bucket values by position
    buckets = [[] for _ in range(period)]
    for i, v in enumerate(series):
        buckets[i % period].append(v)

    # Precompute sums and squared sums for fast leave-one-out stats
    sums = [sum(b) for b in buckets]
    sumsqs = [sum(x * x for x in b) for b in buckets]
    counts = [len(b) for b in buckets]

    detections = []
    tiny = 1e-9
    for i, v in enumerate(series):
        pos = i % period
        n = counts[pos]
        if n <= 1:
            continue
        n1 = n - 1
        sum_ex = sums[pos] - v
        sumsq_ex = sumsqs[pos] - v * v
        mu = sum_ex / n1
        var = max((sumsq_ex / n1) - (mu * mu), tiny)
        sd = math.sqrt(var)
        z = (v - mu) / sd
        if abs(z) >= z_thresh:
            detections.append((i, z))
    return detections


def main():
    random.seed(42)
    series, period = generate_seasonal_series()
    anomaly_idx = inject_anomaly(series, period, day=5, minute=12 * 60, spike=8.0)
    detections = seasonal_zscore_detect(series, period, z_thresh=4.0)

    hit = any(abs(i - anomaly_idx) <= 1 for (i, _) in detections)
    print(f"series_len={len(series)} period={period} anomalies_found={len(detections)} anomaly_idx={anomaly_idx}")
    if hit:
        print("PASS: Seasonality violation detected near injected anomaly.")
        sys.exit(0)
    else:
        print("FAIL: No seasonality violation detected near injected anomaly.")
        sys.exit(1)


if __name__ == "__main__":
    main()

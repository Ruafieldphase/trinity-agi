import argparse
from datetime import datetime, timedelta, timezone
import sys


def compute_next_runs(now: datetime, hour: int, minute: int, days: int):
    # Start from today at target time; if already passed, start tomorrow
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)
    runs = []
    for i in range(days):
        runs.append(target + timedelta(days=i))
    return runs


def validate_daily_cadence(runs):
    if len(runs) < 2:
        return True, []
    deltas = []
    for i in range(1, len(runs)):
        dt = runs[i] - runs[i - 1]
        hours = dt.total_seconds() / 3600.0
        deltas.append(hours)
        # Allow DST/boundary tolerance 22.5h..25.5h
        if not (22.5 <= hours <= 25.5):
            return False, deltas
    return True, deltas


def main():
    parser = argparse.ArgumentParser(description="Scheduler daily cadence dry-run")
    parser.add_argument("--hour", type=int, default=3, help="Hour of day (0-23)")
    parser.add_argument("--minute", type=int, default=0, help="Minute of hour (0-59)")
    parser.add_argument("--days", type=int, default=7, help="Number of future runs to simulate")
    parser.add_argument("--tzutc", action="store_true", help="Use UTC instead of local time")
    args = parser.parse_args()

    now = datetime.now(timezone.utc) if args.tzutc else datetime.now()
    runs = compute_next_runs(now, args.hour, args.minute, args.days)
    ok, deltas = validate_daily_cadence(runs)

    print(f"now={now.isoformat()} hour={args.hour} minute={args.minute} days={args.days}")
    for i, ts in enumerate(runs):
        print(f"run[{i}]={ts.isoformat()}")
    if deltas:
        print("interval_hours=", ", ".join(f"{h:.2f}" for h in deltas))

    if ok and len(runs) == args.days:
        print("PASS: Daily cadence validated within tolerance.")
        sys.exit(0)
    else:
        print("FAIL: Cadence intervals out of tolerance or count mismatch.")
        sys.exit(1)


if __name__ == "__main__":
    main()

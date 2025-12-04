#!/usr/bin/env python3
"""
Convert a 'dream' idea into a tracked goal using the goal tracker CLI.

Creates a proposed goal and can optionally start it (in_progress).

Usage:
  py -3 scripts/dream_to_goal.py --title "TITLE" --priority 12 --days 2 --start

"""
import argparse
import json
import subprocess
import shlex
import sys
from pathlib import Path


def run_cmd(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr)
        raise SystemExit(p.returncode)
    return p.stdout


def add_goal(title, priority, days, description):
    cmd = f'py -3 fdo_agi_repo/scripts/goal_tracker.py add "{title}" --priority {priority} --days {days} --description "{description}"'
    print("➕ Adding goal:", title)
    out = run_cmd(cmd)
    print(out)


def find_goal_id_by_title(title):
    cmd = 'py -3 fdo_agi_repo/scripts/goal_tracker.py list --status proposed'
    out = run_cmd(cmd)
    # The CLI prints JSON for each found goal; try to parse the last JSON object
    objs = []
    for chunk in out.strip().split('\n\n'):
        try:
            objs.append(json.loads(chunk))
        except Exception:
            # Some outputs are not JSON blocks - skip
            continue

    for obj in objs:
        if obj.get('title', '') == title:
            return obj.get('id')
    return None


def start_goal(goal_id):
    cmd = f'py -3 fdo_agi_repo/scripts/goal_tracker.py start {goal_id}'
    print("▶ Starting goal:", goal_id)
    out = run_cmd(cmd)
    print(out)


def make_note(title, description):
    path = Path(__file__).parent.parent / 'outputs' / 'dream_to_goal_note.md'
    path.parent.mkdir(exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f"- {title}  \n  {description}\n  - added at: {__import__('datetime').datetime.utcnow().isoformat()}Z\n\n")
    print(f"✍️ Note written to: {path}")


def main():
    parser = argparse.ArgumentParser(description="Create a goal from a musical dream")
    parser.add_argument('--title', required=True)
    parser.add_argument('--description', default="")
    parser.add_argument('--priority', type=int, default=12)
    parser.add_argument('--days', type=float, default=2.0)
    parser.add_argument('--start', action='store_true', help='Start the goal after creating')

    args = parser.parse_args()

    add_goal(args.title, args.priority, args.days, args.description)
    goal_id = find_goal_id_by_title(args.title)
    if not goal_id:
        print("❌ Could not find the created goal; check output from the CLI")
        sys.exit(1)

    if args.start:
        start_goal(goal_id)

    # Add a quick note to the outputs folder
    make_note(args.title, args.description)


if __name__ == '__main__':
    main()

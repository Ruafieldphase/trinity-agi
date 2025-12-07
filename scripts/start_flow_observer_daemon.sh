#!/bin/bash
# Start Flow Observer Daemon for Linux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_EXEC="$HOME/.agi_venv/bin/python"
DAEMON_SCRIPT="$SCRIPT_DIR/flow_observer_daemon_loop.py"
INTERVAL_SECONDS=${1:-300}

# Check if Python exists
if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="python3"
    echo "⚠️ Virtual env not found, using system python3"
fi

echo "🚀 Starting Flow Observer Daemon..."
echo "   Analysis Interval: $INTERVAL_SECONDS seconds"
echo "   Python: $PYTHON_EXEC"
echo ""
echo "📊 Monitoring:"
echo "   • Desktop activity (5s interval)"
echo "   • Flow state analysis (${INTERVAL_SECONDS}s interval)"
echo "   • Perspective switching detection"
echo "   • Stagnation alerts"
echo ""
echo "📁 Outputs:"
echo "   • outputs/telemetry/stream_observer_*.jsonl"
echo "   • outputs/flow_observer_report_latest.json"
echo "   • outputs/flow_observer_daemon.log"
echo ""
echo "💡 To stop: Press Ctrl+C or kill the process"
echo ""

# Run in foreground (user can background with & or nohup)
"$PYTHON_EXEC" "$DAEMON_SCRIPT" "$INTERVAL_SECONDS"

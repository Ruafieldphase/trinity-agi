#!/bin/bash
# Helper script to run all Rhythm & Resonance components

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="$HOME/.agi_venv/bin/python"

echo "🎵 Starting Rhythm & Resonance System"
echo "======================================"
echo ""

# 1. Start telemetry collector
echo "1. Starting telemetry collector..."
nohup "$PYTHON" "$SCRIPT_DIR/linux_telemetry_collector.py" > /dev/null 2>&1 &
TELEMETRY_PID=$!
echo "   ✅ Telemetry PID: $TELEMETRY_PID"

# 2. Start WebSocket server
echo "2. Starting WebSocket server (port 8096)..."
nohup "$PYTHON" "$SCRIPT_DIR/flow_websocket_server.py" --interval 10 > "$BASE_DIR/outputs/flow_websocket.log" 2>&1 &
WEBSOCKET_PID=$!
echo "   ✅ WebSocket PID: $WEBSOCKET_PID"

# 3. Start Flow Observer daemon (optional)
# echo "3. Starting Flow Observer daemon..."
# nohup "$SCRIPT_DIR/start_flow_observer_daemon.sh" > /dev/null 2>&1 &

echo ""
echo "✅ All services started!"
echo ""
echo "📊 Dashboard: Connect to ws://localhost:8096/flow"
echo "📁 Logs:"
echo "   - WebSocket: outputs/flow_websocket.log"
echo "   - Telemetry: outputs/telemetry/stream_observer_*.jsonl"
echo ""
echo "💡 To stop all services:"
echo "   kill $TELEMETRY_PID $WEBSOCKET_PID"
echo ""

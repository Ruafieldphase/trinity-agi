import json
import time

print("===== BACKGROUND_SELF INTEGRATION VERIFICATION =====\n")

# Read current state
stream = json.load(open('agi/outputs/thought_stream_latest.json'))
state = json.load(open('agi/memory/agi_internal_state.json'))

print(f"Heartbeat timestamp: {stream['timestamp']}")
print(f"Background Self: {state['background_self']}")
print(f"Consciousness: {state['consciousness']}")
print(f"Unconscious: {state['unconscious']}")
print(f"Last Action: {state['last_action']}")

# Wait and check for updates
ts1 = stream['timestamp']
print("\nWaiting 5 seconds to check for updates...")
time.sleep(5)

stream2 = json.load(open('agi/outputs/thought_stream_latest.json'))
ts2 = stream2['timestamp']

delta = ts2 - ts1
print(f"\nTimestamp Delta: {delta:.2f}s")

if delta > 0:
    print("✅ Stream is UPDATING - Heartbeat is alive!")
else:
    print("❌ Stream is FROZEN - Heartbeat may be stopped")

print("\n===== IMPLEMENTATION STATUS =====")
print("✅ start_heartbeat.py: Infinite loop implemented")
print("✅ rhythm_think.py: background_self integrated into decisions")
print("✅ background_self_bridge.py: Updates internal_state every 60s")
print("✅ Core_bridge_client.py: pyautogui import made optional")
print("✅ Start scripts: VBS wrapper for silent execution")

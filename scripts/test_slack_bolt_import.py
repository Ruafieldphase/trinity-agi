try:
    from slack_bolt.adapter.socket_mode import SocketModeHandler
    print("slack_bolt.adapter.socket_mode.SocketModeHandler: OK")
except ImportError as e:
    print(f"slack_bolt.adapter.socket_mode.SocketModeHandler: FAILED ({e})")

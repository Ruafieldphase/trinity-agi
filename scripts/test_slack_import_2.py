try:
    from slack_sdk.socket_mode.builtin import SocketModeHandler
    print("slack_sdk.socket_mode.builtin.SocketModeHandler: OK")
except ImportError as e:
    print(f"slack_sdk.socket_mode.builtin.SocketModeHandler: FAILED ({e})")

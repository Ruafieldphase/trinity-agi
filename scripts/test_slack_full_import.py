try:
    from slack_sdk import WebClient
    print("WebClient: OK")
except ImportError as e:
    print(f"WebClient: FAILED ({e})")

try:
    from slack_sdk.socket_mode.builtin import SocketModeHandler
    print("SocketModeHandler: OK")
except ImportError as e:
    print(f"SocketModeHandler: FAILED ({e})")

try:
    from slack_sdk.socket_mode.response import SocketModeResponse
    print("SocketModeResponse: OK")
except ImportError as e:
    print(f"SocketModeResponse: FAILED ({e})")

try:
    from slack_sdk.socket_mode.request import SocketModeRequest
    print("SocketModeRequest: OK")
except ImportError as e:
    print(f"SocketModeRequest: FAILED ({e})")

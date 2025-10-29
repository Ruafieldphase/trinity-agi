#!/usr/bin/env python3
# OBS WebSocket control helper (v5 protocol via obsws-python)
# Commands: start, stop, switch, list, status, ping
# Config via CLI or ENV:
#   OBS_WS_HOST (default 127.0.0.1)
#   OBS_WS_PORT (default 4455)
#   OBS_WS_PASSWORD (required if OBS requires auth)

import os
import sys
import argparse
from typing import Optional, Any


def parse_args():
    p = argparse.ArgumentParser(
        description="Control OBS via WebSocket (requires obsws-python for v5)")
    p.add_argument("command", choices=[
        "start", "stop", "switch", "list", "status", "ping"
    ], help="Action to perform")
    p.add_argument("value", nargs="?", help="Command value (e.g., scene name for 'switch')")
    p.add_argument("--host", dest="host", default=os.environ.get("OBS_WS_HOST", "127.0.0.1"))
    p.add_argument("--port", dest="port", type=int, default=int(os.environ.get("OBS_WS_PORT", 4455)))
    p.add_argument("--password", dest="password", default=os.environ.get("OBS_WS_PASSWORD"))
    p.add_argument("--timeout", dest="timeout", type=float, default=5.0, help="Connect timeout seconds")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def _connect(host: str, port: int, password: Optional[str], timeout: float):
    """Create a ReqClient connection using obsws_python >=1.x API.

    Newer obsws_python exposes ReqClient/EventClient instead of obsws + requests.
    The ReqClient connects on construction; .disconnect() exists, but .connect() does not.
    """
    try:
        import obsws_python as obsp  # type: ignore
    except Exception:
        print("obsws-python not installed. Install with: pip install obsws-python", file=sys.stderr)
        raise ImportError("obsws-python missing")
    # Connect on construction
    client = obsp.ReqClient(host=host, port=port, password=password, timeout=timeout)
    return client


def do_ping(host: str, port: int):
    import socket
    s = socket.socket()
    s.settimeout(1.0)
    try:
        s.connect((host, port))
        s.close()
        print(f"PING OK: {host}:{port}")
        return 0
    except Exception as e:
        print(f"PING FAIL: {host}:{port} -> {e}", file=sys.stderr)
        return 2


def main():
    args = parse_args()

    if args.command == "ping":
        sys.exit(do_ping(args.host, args.port))

    # commands below require obsws-python; import lazily in _connect
    try:
        client = _connect(args.host, args.port, args.password, args.timeout)
    except ImportError:
        # already printed hint above
        sys.exit(2)
    except Exception as e:
        print(f"Failed to connect to OBS at {args.host}:{args.port} -> {e}", file=sys.stderr)
        sys.exit(2)

    try:
        if args.command == "start":
            client.start_stream()
            print("StartStream: OK")
        elif args.command == "stop":
            client.stop_stream()
            print("StopStream: OK")
        elif args.command == "switch":
            if not args.value:
                print("Scene name required for 'switch'", file=sys.stderr)
                sys.exit(2)
            # v5: set current program scene
            client.set_current_program_scene(scene_name=args.value)
            print(f"SwitchScene: '{args.value}' -> OK")
        elif args.command == "list":
            resp = client.get_scene_list()
            # Normalize various possible shapes
            scenes: Any = None
            if isinstance(resp, dict):
                scenes = resp.get("scenes")
            if scenes is None:
                scenes = getattr(resp, "scenes", None)
                if callable(scenes):
                    scenes = scenes()
            if isinstance(scenes, (list, tuple)):
                for s in scenes:
                    if isinstance(s, dict):
                        name = s.get("sceneName") or s.get("scene_name") or s.get("name")
                    else:
                        name = getattr(s, "sceneName", None) or getattr(s, "name", None)
                    print(name if name is not None else s)
            else:
                print(resp)
        elif args.command == "status":
            resp = client.get_stream_status()
            # Try common fields with flexible case/shape
            def _from(obj, *names):
                for n in names:
                    if isinstance(obj, dict):
                        if n in obj:
                            return obj[n]
                    val = getattr(obj, n, None)
                    if val is not None:
                        return val
                return None
            active = _from(resp, "outputActive", "active", "stream_active")
            timecode = _from(resp, "outputTimecode", "timecode")
            dropped = _from(resp, "outputSkippedFrames", "dropped_frames")
            print({"active": active, "timecode": timecode, "dropped_frames": dropped})
        else:
            print("Unknown command", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)
    finally:
        try:
            client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    main()

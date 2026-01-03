import os
import subprocess
import sys
import json
import time
from pathlib import Path
from workspace_root import get_workspace_root

def main():
    # Use the provided args from persona_registry.json
    # args in registry are ["exec"]
    # We want to run: codex.cmd exec [input_from_stdin]
    
    cmd = ["codex.cmd"]
    
    # Environment variable set by agi_session_start.ps1
    session_id = os.environ.get("CODEX_SESSION_ID")

    workspace_root = get_workspace_root()
    state_path = workspace_root / "outputs" / "sync_cache" / "codex_session_state.json"
    bootstrap_marker = "CODEX_CONTINUITY_SNAPSHOT"
    bootstrap_candidates = [
        workspace_root / "outputs" / "sync_cache" / "codex_continuity_snapshot.md",
        workspace_root / "outputs" / "coordination" / "agent_brief_latest.md",
        workspace_root / "outputs" / "session_continuity_latest.md",
        workspace_root / "outputs" / ".copilot_context_summary.md",
    ]
    max_bootstrap_chars = int(os.environ.get("CODEX_CONTINUITY_MAX_CHARS", "4000"))
    skip_window_sec = int(os.environ.get("CODEX_SESSION_SKIP_WINDOW_SEC", "3600"))
    
    # We assume the first argument is 'exec' as per persona_registry.json
    # If session_id exists, we insert it after 'exec'
    
    base_args = sys.argv[1:]
    
    final_args = []
    if base_args and base_args[0] == "exec":
        final_args.append("exec")
        if session_id:
            final_args.extend(["--session", session_id])
        final_args.extend(base_args[1:])
    else:
        final_args.extend(base_args)
        if session_id:
            final_args.extend(["--session", session_id])

    # Combine into full command
    full_cmd = cmd + final_args

    def _read_state() -> dict:
        try:
            if not state_path.exists():
                return {}
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_state(data: dict) -> None:
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_bootstrap() -> str:
        for path in bootstrap_candidates:
            try:
                if path.exists():
                    text = path.read_text(encoding="utf-8", errors="replace").strip()
                    if text:
                        snippet = text[:max_bootstrap_chars]
                        state["last_bootstrap"] = snippet
                        state["last_bootstrap_at"] = time.time()
                        _write_state(state)
                        return snippet
            except Exception:
                continue
        fallback = state.get("last_bootstrap") if isinstance(state, dict) else ""
        if isinstance(fallback, str) and fallback:
            return fallback[:max_bootstrap_chars]
        return ""

    def _compose_payload(user_input: str, bootstrap: str) -> str:
        if not bootstrap:
            return user_input
        if bootstrap_marker in user_input:
            return user_input
        header = f"<<{bootstrap_marker}>>\n{bootstrap}\n<</{bootstrap_marker}>>\n\n"
        return header + user_input

    def _emit_result(result: subprocess.CompletedProcess) -> None:
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)

    def _looks_like_session_error(text: str) -> bool:
        t = (text or "").lower()
        needles = [
            "session",
            "invalid session",
            "session not found",
            "unauthorized",
            "forbidden",
            "not logged in",
            "auth",
            "login",
            "401",
            "403",
        ]
        return any(n in t for n in needles)

    input_data = ""
    try:
        if not sys.stdin.isatty():
            input_data = sys.stdin.read()
    except Exception:
        input_data = ""

    state = _read_state()
    session_usable = state.get("session_usable", True)
    last_error_at = float(state.get("last_error_at", 0) or 0)
    if not session_usable and (time.time() - last_error_at) < skip_window_sec:
        session_id = None

    def _run_with_args(args: list[str], payload: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            args,
            input=payload,
            text=True,
            capture_output=True,
            shell=True,
        )
    
    try:
        # Attempt with session if available, otherwise bootstrap context
        payload = input_data
        if not session_id:
            bootstrap = _load_bootstrap()
            payload = _compose_payload(input_data, bootstrap)
        result = _run_with_args(full_cmd, payload)
        if result.returncode == 0:
            if session_id:
                state.update({
                    "last_session_id": session_id,
                    "last_success_at": time.time(),
                    "session_usable": True,
                    "last_error": None,
                })
            else:
                state.update({
                    "last_success_at": time.time(),
                    "last_error": None,
                })
            _write_state(state)
            _emit_result(result)
            sys.exit(0)

        combined_err = (result.stderr or "") + "\n" + (result.stdout or "")
        if session_id and _looks_like_session_error(combined_err):
            state.update({
                "session_usable": False,
                "last_error_at": time.time(),
                "last_error": combined_err[:400],
            })
            _write_state(state)

            # Retry without session and with continuity bootstrap
            retry_args = cmd + [a for a in final_args if a not in ("--session", session_id)]
            bootstrap = _load_bootstrap()
            retry_payload = _compose_payload(input_data, bootstrap)
            retry_result = _run_with_args(retry_args, retry_payload)
            if retry_result.returncode == 0:
                _emit_result(retry_result)
                sys.exit(0)
            _emit_result(retry_result)
            sys.exit(retry_result.returncode)

        _emit_result(result)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error in codex wrapper: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGI Chat Window (local, Tkinter, file-based)

의도
- 웹서버/포트/CORS 없이 "대화창 느낌"을 제공한다.
- 실제로는 file-based inbox/outbox:
  - 사용자 → signals/binoche_note.json
  - AGI → outputs/bridge/agi_message_latest.txt|json

원칙
- 네트워크 호출 없음(이 UI 자체는 로컬만)
- PII/URL/경로 등은 저장 전에 마스킹 + 길이 제한
- 사용자가 원할 때만 실행(상시 팝업/자동 실행 없음)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import ttk, font

ROOT = Path(__file__).resolve().parents[1]
SIGNALS = ROOT / "signals"
OUTPUTS = ROOT / "outputs"
BRIDGE = OUTPUTS / "bridge"

INBOX_SIGNAL = SIGNALS / "binoche_note.json"
TRIGGER_SIGNAL = SIGNALS / "lua_trigger.json"
AGI_MSG_JSON = BRIDGE / "agi_message_latest.json"
AGI_MSG_TXT = BRIDGE / "agi_message_latest.txt"

HISTORY = BRIDGE / "agi_chat_history.jsonl"


def _utc_local() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _redact(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    # URL Masking
    s = re.sub(r"https?://[^\s)\]]+", "[REDACTED_URL]", s)
    # Email Masking
    s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", s)
    # Windows Path Masking (simple heuristic)
    s = re.sub(r"\b[A-Za-z]:\\[^\s]+", "[REDACTED_PATH]", s)
    return s


def _cap(s: str, n: int = 800) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"


def _append_history(obj: dict[str, Any]) -> None:
    try:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        with HISTORY.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _safe_load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _write_note_signal(text: str) -> bool:
    try:
        SIGNALS.mkdir(parents=True, exist_ok=True)
        payload = {"text": text, "timestamp": time.time(), "origin": "binoche"}
        INBOX_SIGNAL.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _try_write_trigger(action: str, *, reason: str) -> bool:
    """
    채팅창에서 메모 전송 후, '메모 인테이크'를 빠르게 처리하기 위한 최소 트리거.
    - 기존 트리거가 있으면 덮어쓰지 않는다(우선권 침해 방지).
    """
    try:
        SIGNALS.mkdir(parents=True, exist_ok=True)
        if TRIGGER_SIGNAL.exists():
            return False
        payload = {
            "action": str(action),
            "params": {"reason": str(reason)},
            "timestamp": float(time.time()),
            "origin": "binoche_ui",
        }
        _atomic_write_json(TRIGGER_SIGNAL, payload)
        return True
    except Exception:
        return False


def _kick_run_trigger_once() -> None:
    """
    GUI가 켜져 있을 때만(=사용자 의도) 1회 처리로 '즉시 반응'을 유도한다.
    """
    try:
        script = ROOT / "scripts" / "run_trigger_once.py"
        if not script.exists():
            return
        kwargs: dict[str, Any] = {"cwd": str(ROOT)}
        if sys.platform.startswith("win"):
            kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        subprocess.Popen([sys.executable, str(script)], **kwargs)  # noqa: S603,S607
    except Exception:
        return


class ChatUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AGI Chat (Local) - Binoche Note")
        self.root.geometry("600x850")
        
        # Style & Fonts
        self.default_font = ("Malgun Gothic", 12)  # Readable standard font
        self.header_font = ("Malgun Gothic", 12, "bold")
        self.history_font = ("Malgun Gothic", 11)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TButton", font=self.default_font, padding=6)
        style.configure("TLabel", font=self.default_font)
        style.configure("TLabelframe.Label", font=self.header_font)

        # 1. Top: Latest AGI Message (Prominent)
        self.top_frame = ttk.LabelFrame(root, text=" 📢 최근 AGI 메시지 ", padding=10)
        self.top_frame.pack(side="top", fill="x", padx=10, pady=10)

        self.latest_text = tk.Text(self.top_frame, height=8, wrap="word", font=self.default_font, bg="#f0f8ff", relief="flat")
        self.latest_text.pack(side="left", fill="both", expand=True)
        self.latest_text.insert("1.0", "(아직 메시지 없음)")
        self.latest_text.configure(state="disabled")

        # 2. Middle: History Log (Scrollable)
        self.mid_frame = ttk.LabelFrame(root, text=" 📜 대화 기록 ", padding=10)
        self.mid_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        self.history_text = tk.Text(self.mid_frame, wrap="word", font=self.history_font, state="disabled")
        self.history_scroll = ttk.Scrollbar(self.mid_frame, orient="vertical", command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=self.history_scroll.set)
        
        self.history_text.pack(side="left", fill="both", expand=True)
        self.history_scroll.pack(side="right", fill="y")

        # 3. Bottom: Input & Controls
        self.bottom_frame = ttk.Frame(root, padding=10)
        self.bottom_frame.pack(side="bottom", fill="x")

        # Toolbar
        self.toolbar = ttk.Frame(self.bottom_frame)
        self.toolbar.pack(side="top", fill="x", pady=(0, 5))
        
        self.btn_refresh = ttk.Button(self.toolbar, text="🔄 새로고침", command=self.manual_refresh)
        self.btn_refresh.pack(side="left", padx=(0, 5))

        self.btn_copy = ttk.Button(self.toolbar, text="📋 최근 메시지 복사", command=self.copy_latest)
        self.btn_copy.pack(side="left", padx=(0, 5))

        self.status_label = ttk.Label(self.toolbar, text="준비됨", foreground="gray")
        self.status_label.pack(side="right")

        # Input Area
        self.input_text = tk.Text(self.bottom_frame, height=4, wrap="word", font=self.default_font)
        self.input_text.pack(side="left", fill="both", expand=True, pady=(5, 0))
        self.input_text.bind("<Return>", self.on_enter_pressed)
        
        self.btn_send = ttk.Button(self.bottom_frame, text="전송 (Enter)", command=self.on_send)
        self.btn_send.pack(side="right", fill="y", padx=(5, 0), pady=(5, 0))

        # Initial State
        self.last_agi_sig = ""
        self.root.after(600, self.poll_agi_message)

        # Welcome msg
        self.append_history("system", "AGI 대화창이 시작되었습니다.")
        self.load_latest_agi_message(force=True)

    def append_history(self, who: str, msg: str) -> None:
        ts = _utc_local()
        line = f"[{ts}] {who}:\n{msg}\n\n"
        self.history_text.configure(state="normal")
        self.history_text.insert("end", line)
        self.history_text.see("end")
        self.history_text.configure(state="disabled")

    def update_latest_view(self, msg: str) -> None:
        self.latest_text.configure(state="normal")
        self.latest_text.delete("1.0", "end")
        self.latest_text.insert("1.0", msg)
        self.latest_text.configure(state="disabled")

    def copy_latest(self) -> None:
        content = self.latest_text.get("1.0", "end").strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.status_label.configure(text="복사 완료!", foreground="green")
            self.root.after(2000, lambda: self.status_label.configure(text="준비됨", foreground="gray"))

    def manual_refresh(self) -> None:
        self.poll_agi_message()
        self.status_label.configure(text="새로고침 완료", foreground="blue")
        self.root.after(1000, lambda: self.status_label.configure(text="준비됨", foreground="gray"))

    def on_enter_pressed(self, event) -> str | None:
        if event.state & 0x0001:  # Shift key pressed
            return None  # Let the newline happen
        self.on_send()
        return "break"  # Prevent default newline

    def on_send(self) -> None:
        raw = self.input_text.get("1.0", "end").strip()
        if not raw:
            return

        # Clear input immediately
        self.input_text.delete("1.0", "end")
        
        # Process content
        txt = _cap(_redact(raw), 800)
        if not txt:
            return # Should probably warn user if redacted to empty, but keeping it simple

        ok = _write_note_signal(txt)
        if ok:
            self.append_history("YOU", txt)
            _append_history({"ts": time.time(), "who": "you", "text": txt})
            self.status_label.configure(text="메모 전송됨 ✅", foreground="green")

            # 메모 인테이크를 빠르게 반영: binoche_note 트리거(없을 때만) + 1회 처리 킥
            if _try_write_trigger("binoche_note", reason="binoche_note_ui"):
                self.status_label.configure(text="메모 전송됨 ✅ (처리 요청됨)", foreground="green")
                _kick_run_trigger_once()
        else:
            self.status_label.configure(text="전송 실패 ❌", foreground="red")
            # Restore text if failed (optional, but good UX)
            self.input_text.insert("1.0", raw)

    def poll_agi_message(self) -> None:
        self.load_latest_agi_message()
        self.root.after(1200, self.poll_agi_message)

    def load_latest_agi_message(self, force: bool = False) -> None:
        try:
            data = _safe_load_json(AGI_MSG_JSON)
            msg = ""
            sig = ""
            
            if isinstance(data, dict):
                sig = str(data.get("generated_at_utc") or "") + "|" + str(data.get("mode") or "")
                lines = data.get("lines") if isinstance(data.get("lines"), list) else []
                # Join lines for display
                if lines:
                    msg = "\n".join([str(x) for x in lines])
            
            # Fallback to text file if JSON is empty/missing
            if not msg and AGI_MSG_TXT.exists():
                msg = AGI_MSG_TXT.read_text(encoding="utf-8", errors="replace").strip()
                # Use mtime as signature equivalent for text file
                sig = f"txt_{AGI_MSG_TXT.stat().st_mtime}"

            if not msg:
                return

            if force or (sig and sig != self.last_agi_sig):
                self.last_agi_sig = sig
                self.update_latest_view(msg)
                self.append_history("AGI", msg)
                _append_history({"ts": time.time(), "who": "agi", "text": msg})
                # Visual cue in window title or status?
                self.status_label.configure(text="새 메시지 도착!", foreground="blue")
                
        except Exception:
            pass


def main() -> int:
    root = tk.Tk()
    ChatUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

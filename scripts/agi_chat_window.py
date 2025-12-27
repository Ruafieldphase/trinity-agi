#!/usr/bin/env python3
import os
import time
import tkinter as tk
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "inputs" / "agi_chat.txt"
OUTPUT_PATH = ROOT / "outputs" / "agi_chat_response.txt"


class AGIChatWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AGI Chat")
        self.geometry("720x520")

        INPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        self.last_response_mtime = 0.0

        self._build_ui()
        self._poll_response()

    def _build_ui(self) -> None:
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.chat = tk.Text(self, wrap="word", state="disabled")
        self.chat.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)

        self.entry = tk.Entry(self)
        self.entry.grid(row=1, column=0, sticky="ew", padx=8)
        self.entry.bind("<Return>", self._on_send)
        self.columnconfigure(0, weight=1)

        send_btn = tk.Button(self, text="Send", command=self._send_message)
        send_btn.grid(row=1, column=1, sticky="e", padx=8)

        self.status = tk.Label(
            self,
            text=f"Input: {INPUT_PATH} | Output: {OUTPUT_PATH} | Use prefix: ari: or trinity: to force",
            anchor="w",
        )
        self.status.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 6))

    def _append_chat(self, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", text + "\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _send_message(self) -> None:
        message = self.entry.get().strip()
        if not message:
            return
        payload = message

        try:
            INPUT_PATH.write_text(payload, encoding="utf-8")
        except Exception as exc:
            self._append_chat(f"[error] failed to write input: {exc}")
            return

        self._append_chat(f"You: {message}")
        self.entry.delete(0, "end")

    def _on_send(self, _event: tk.Event) -> None:
        self._send_message()

    def _poll_response(self) -> None:
        try:
            if OUTPUT_PATH.exists():
                mtime = OUTPUT_PATH.stat().st_mtime
                if mtime > self.last_response_mtime:
                    response = OUTPUT_PATH.read_text(encoding="utf-8").strip()
                    if response:
                        self._append_chat(f"AGI: {response}")
                    self.last_response_mtime = mtime
        except Exception as exc:
            self._append_chat(f"[error] failed to read output: {exc}")

        self.after(700, self._poll_response)


def main() -> int:
    app = AGIChatWindow()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

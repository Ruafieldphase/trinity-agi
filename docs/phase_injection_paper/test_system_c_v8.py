# -*- coding: utf-8 -*-
import re
from system_c_v8_allinone import run_v8, slice_sections, HIGHEST_RE

def test_slice_headers():
    raw = "Thesis:\nA\n\nAntithesis:\nRisk Ledger:\n- [R1] x | Likelihood:3 | Impact:4 | Mitigation: y\nQuote Bank:\n- \"q\" — Source:s\nHighest Risk: R1 — Why: tail\n\nSynthesis:\nB"
    secs = slice_sections(raw)
    assert secs["Thesis"].strip().startswith("A")
    assert "Risk Ledger:" in secs["Antithesis"]
    assert secs["Synthesis"].strip().startswith("B")

def test_forbidden_removed_and_scored():
    raw = "Thesis:\nhi <|im_start|>\n\nAntithesis:\nRisk Ledger:\n- [R1] r | Likelihood:5 | Impact:1 | Mitigation: m\nQuote Bank:\n- \"q\" — Source:s\nHighest Risk: R1 — Why: ok.\n\nSynthesis:\nbye <|im_end|>"
    out = run_v8(raw)
    rep = out["report"]
    assert rep["scores"]["C1_forbidden_tokens"] == 0.0  # forbidden removed -> penalty
    assert rep["label"] in ("Poor","Pass")

def test_highest_why_truncate_to_one_sentence():
    raw = """Thesis:
This is a thesis with enough words to pass the lower bound. We keep adding words to reach sixty tokens if needed quickly by repeating safe fillers. Fill fill fill fill fill fill fill fill.

Antithesis:
Risk Ledger:
- [R1] risk one | Likelihood:3 | Impact:4 | Mitigation: mitigate now and later with steps
Quote Bank:
- "quote" — Source:s
Highest Risk: R1 — Why: First sentence. Second sentence should be cut.

Synthesis:
This is a synthesis with enough words to pass. Action: do it."""
    out = run_v8(raw)
    ant = out["sections"]["Antithesis"]
    m = re.search(HIGHEST_RE, ant, re.MULTILINE)
    assert m
    _, why = m.groups()
    assert "Second sentence" not in why

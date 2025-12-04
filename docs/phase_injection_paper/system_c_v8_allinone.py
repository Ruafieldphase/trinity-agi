#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System C v8 - all-in-one
- v8 core (regex/normalize/validator) + before/after reporter (Markdown)
- Usage:
    python system_c_v8_allinone.py input.jsonl --limit 30
    -> writes input.v8.report.md
"""
import argparse, json, re, os, datetime, difflib, csv
from typing import Dict, Any, List, Tuple

# =======================
# v8 CONSTANTS / REGEX
# =======================
V8_HEADERS = ["Thesis:", "Antithesis:", "Synthesis:"]
FORBIDDEN_TOKENS = [
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"</?[^>]+>",          # simple markup tags
    r"^\\s*```.*?$",        # code fence line
]
THESIS_WORD_RANGE = (60, 200)     # recommended 80-160
SYNTHESIS_WORD_RANGE = (60, 200)

RISK_LINE_RE = r"""^- \[(R\d{1,2})\]\\s(.+?)\\s\|\\sLikelihood:(\d)\\s\|\\sImpact:(\d)\\s\|\\sMitigation:(.+)$"""
QUOTE_LINE_RE = r"""^-\s"(.{1,120})"\sâ\sSource:(.{1,60})$"""
HIGHEST_RE     = r"""^Highest Risk:\s(R\d{1,2})\sâ\sWhy:(.+)$"""

MITIGATION_MAX_TOKENS = 25
RISK_ITEM_MAX_LEN = 30
WHY_MAX_SENTENCES = 1
MAX_RISKS = 5; MIN_RISKS = 2
MAX_QUOTES = 3; MIN_QUOTES = 1

W = {
  "H1_headers_labels": 0.25,
  "H2_structure_complete": 0.20,
  "C1_forbidden_tokens": 0.15,
  "L1_risk_ledger_format": 0.15,
  "Q1_quote_bank_format": 0.10,
  "R1_highest_validity": 0.05,
  "W1_word_ranges": 0.10,
}
THRESHOLD_PASS = 0.72

# =======================
# UTIL / TOKENIZE
# =======================
WORD_RE = re.compile(r"[A-Za-z0-9_]+|[\uAC00-\uD7A3]+")

def word_count(s: str) -> int:
    return len(WORD_RE.findall(s or ""))

def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))

def truncate_tokens(s: str, max_tokens: int) -> str:
    toks = WORD_RE.findall(s or "")
    if len(toks) <= max_tokens:
        return (s or "").strip()
    keep = " ".join(toks[:max_tokens]) + " …"
    return keep

def first_sentence(s: str) -> str:
    m = re.split(r"(?<=[.!?])\\s+", (s or "").strip())
    return m[0] if m else (s or "").strip()

def strip_forbidden(text: str) -> Tuple[str, List[str]]:
    hit = []
    out = text
    for pat in FORBIDDEN_TOKENS:
        if re.search(pat, out, re.MULTILINE):
            hit.append(pat)
            out = re.sub(pat, "", out, flags=re.MULTILINE)
    return out, hit

# =======================
# SECTION SLICE
# =======================
def slice_sections(raw: str) -> Dict[str, str]:
    text = (raw or "").strip()
    text, _ = strip_forbidden(text)

    spans = []
    for h in V8_HEADERS:
        p = re.search(rf"(?m)^{re.escape(h)}\s*", text)
        if p:
            spans.append((h, p.start()))
    spans.sort(key=lambda x: x[1])

    result = {"Thesis": "", "Antithesis": "", "Synthesis": ""}
    for i, (h, start) in enumerate(spans):
        end = spans[i+1][1] if i+1 < len(spans) else len(text)
        body = text[start+len(h):end].strip()
        result[h[:-1]] = body
    return result

# =======================
# ANTITHESIS PARSE/NORM
# =======================
def parse_antithesis_block(s: str) -> Dict[str, List[str] or str]:
    out = {"risk_lines": [], "quote_lines": [], "highest_line": ""}

    def find_block(label):
        m = re.search(rf"(?m)^{label}\\s*$", s)
        return m.start() if m else None

    pos_risk  = find_block("Risk Ledger:")
    pos_quote = find_block("Quote Bank:")
    pos_high_m = re.search(rf"(?m){HIGHEST_RE}", s)
    pos_high = pos_high_m.start() if pos_high_m else find_block("Highest Risk:")

    def seg(start, end):
        if start is None: return ""
        return s[start:end].split("\n", 1)[1] if "\n" in s[start:end] else ""

    end_risk  = min([p for p in [pos_quote, pos_high, len(s)] if p is not None])
    end_quote = min([p for p in [pos_high, len(s)] if p is not None])

    risk_area  = seg(pos_risk, end_risk)
    quote_area = seg(pos_quote, end_quote)

    highest_line = ""
    for line in s.splitlines():
        if re.match(HIGHEST_RE, line.strip()):
            highest_line = line.strip()
            break

    out["risk_lines"]  = [ln.strip() for ln in (risk_area or "").splitlines() if ln.strip().startswith("- [")]
    out["quote_lines"] = [ln.strip() for ln in (quote_area or "").splitlines() if ln.strip().startswith("- ")]
    out["highest_line"] = highest_line
    return out

def normalize_antithesis(s: str) -> Tuple[str, Dict]:
    meta = {
        "risk_clamped": 0,
        "risk_trimmed": 0,
        "risk_overflow": 0,
        "quote_trimmed": 0,
        "quote_overflow": 0,
        "highest_trimmed": False,
        "risk_valid": 0,
        "risk_total": 0,
        "quote_valid": 0,
        "quote_total": 0,
        "has_highest": False,
    }

    blocks = parse_antithesis_block(s)

    # Risk Ledger
    norm_risks = []
    for ln in blocks["risk_lines"]:
        m = re.match(RISK_LINE_RE, ln)
        if not m:
            norm_risks.append(ln)
            continue
        rid, risk_text, lk, ip, mitig = m.groups()
        lk = str(clamp(int(lk), 1, 5))
        ip = str(clamp(int(ip), 1, 5))
        if int(lk) in (1, 5) or int(ip) in (1, 5):
            meta["risk_clamped"] += 1
        if word_count(risk_text) > RISK_ITEM_MAX_LEN:
            risk_text = truncate_tokens(risk_text, RISK_ITEM_MAX_LEN)
            meta["risk_trimmed"] += 1
        mitig = truncate_tokens(mitig, MITIGATION_MAX_TOKENS)
        rebuilt = f"- [{rid}] {risk_text} | Likelihood:{lk} | Impact:{ip} | Mitigation:{mitig}"
        norm_risks.append(rebuilt)
        meta["risk_valid"] += 1
    meta["risk_total"] = len(blocks["risk_lines"])
    overflow = max(len(norm_risks) - MAX_RISKS, 0)
    meta["risk_overflow"] = overflow
    if overflow:
        norm_risks = norm_risks[:MAX_RISKS]

    # Quote Bank
    norm_quotes = []
    for ln in blocks["quote_lines"]:
        m = re.match(QUOTE_LINE_RE, ln)
        if not m:
            q = re.findall(r"\"(.+?)\"", ln)
            src = re.findall(r"Source:(.+)$", ln)
            if q:
                quote = q[0][:120]
                source = (src[0].strip() if src else "Unknown")[:60]
                rebuilt = f'- "{quote}" â Source:{source}'
                norm_quotes.append(rebuilt)
                meta["quote_valid"] += 1
            else:
                norm_quotes.append(ln)
            continue
        quote, src = m.groups()
        rebuilt = f'- "{quote}" â Source:{src}'
        norm_quotes.append(rebuilt)
        meta["quote_valid"] += 1
    meta["quote_total"] = len(blocks["quote_lines"])
    overflow_q = max(len(norm_quotes) - MAX_QUOTES, 0)
    meta["quote_overflow"] = overflow_q
    if overflow_q:
        norm_quotes = norm_quotes[:MAX_QUOTES]
        meta["quote_trimmed"] = overflow_q

    # Highest Risk (Why 1 sentence)
    highest_out = ""
    if blocks["highest_line"]:
        m = re.match(HIGHEST_RE, blocks["highest_line"])
        if m:
            rid, why = m.groups()
            why1 = first_sentence(why)
            highest_out = f"Highest Risk: {rid} â Why: {why1}"
            meta["has_highest"] = True
            if why1 != (why or "").strip():
                meta["highest_trimmed"] = True
        else:
            highest_out = blocks["highest_line"]

    out = []
    out.append("Risk Ledger:")
    out.extend(norm_risks or [])
    out.append("Quote Bank:")
    out.extend(norm_quotes or [])
    out.append(highest_out or "Highest Risk: R1 â Why: (to be specified)")
    return "\n".join(out).strip(), meta

# =======================
# NORMALIZE (ALL)
# =======================


def prepass_header_rescue(raw: str) -> str:
    """
    If none (or only some) of the top-level headers exist, wrap raw into a minimal v8 skeleton.
    - Keep raw under Thesis if we detect zero headers (salvage content).
    - Always emit Antithesis sublabels so validator can operate.
    """
    text = (raw or "").strip()
    has_thesis = re.search(r"(?m)^Thesis:\s*", text) is not None
    has_anti = re.search(r"(?m)^Antithesis:\s*", text) is not None
    has_syn = re.search(r"(?m)^Synthesis:\s*", text) is not None
    if has_thesis and has_anti and has_syn:
        return text  # nothing to do

    any_header = has_thesis or has_anti or has_syn
    if not any_header:
        thesis_body = text
        anti_body = "Risk Ledger:\nQuote Bank:\nHighest Risk: R1 \u2014 Why: (to be specified)"
        synth_body = ""
        return f"Thesis:\n{thesis_body}\n\nAntithesis:\n{anti_body}\n\nSynthesis:\n{synth_body}".strip()

    if not has_thesis:
        text = "Thesis:\n\n" + text
    if not has_anti:
        text += "\n\nAntithesis:\nRisk Ledger:\nQuote Bank:\nHighest Risk: R1 \u2014 Why: (to be specified)"
    else:
        def ensure(label, default_line=""):
            nonlocal text
            if re.search(rf"(?m)^{label}\s*$", text) is None:
                text = re.sub(
                    r"(?m)^Antithesis:\s*$",
                    "Antithesis:\nRisk Ledger:\nQuote Bank:\nHighest Risk: R1 \u2014 Why: (to be specified)",
                    text,
                )

        ensure("Risk Ledger:")
        ensure("Quote Bank:")
        ensure("Highest Risk:")
    if not has_syn:
        text += "\n\nSynthesis:\n"

    return text


def normalize_response(raw: str) -> Tuple[Dict[str, str], Dict]:
    original = raw or ""
    meta = {"forbidden_hit": False, "forbidden_patterns": []}

    headers_before = {h[:-1]: bool(re.search(rf"(?m)^{re.escape(h)}\s*", original)) for h in V8_HEADERS}
    rescued_raw = prepass_header_rescue(original)
    headers_after = {h[:-1]: bool(re.search(rf"(?m)^{re.escape(h)}\s*", rescued_raw)) for h in V8_HEADERS}
    meta["header_presence_before"] = headers_before
    meta["header_presence_after"] = headers_after
    meta["header_rescued"] = {k: (not headers_before.get(k, False) and headers_after.get(k, False)) for k in headers_after}
    meta["header_rescue_applied"] = any(meta["header_rescued"].values())

    raw = rescued_raw
    sections = slice_sections(raw)

    cleaned = {}
    forb_all = []
    for k, v in sections.items():
        nv, forb = strip_forbidden(v)
        cleaned[k] = (nv or "").strip()
        forb_all.extend(forb)
    if forb_all:
        meta["forbidden_hit"] = True
        meta["forbidden_patterns"] = sorted(list(set(forb_all)))

    ant_norm, ant_meta = normalize_antithesis(cleaned.get("Antithesis", ""))
    cleaned["Antithesis"] = ant_norm
    meta.update(ant_meta)
    return cleaned, meta

# =======================
# VALIDATE
# =======================
def validate_v8(sections: Dict[str, str], meta: Dict) -> Dict:
    report = {"scores": {}, "warnings": []}

    if meta.get("header_rescue_applied"):
        rescued = [k for k, v in meta.get("header_rescued", {}).items() if v]
        report["warnings"].append(f"Header rescue injected skeleton for: {', '.join(rescued) or 'n/a'}")

    header_after = meta.get("header_presence_after", {})
    has_upper = all(header_after.get(k, False) for k in ["Thesis", "Antithesis", "Synthesis"])
    has_sub = all(re.search(rf"(?m)^{lbl}", sections.get("Antithesis","")) for lbl in ["Risk Ledger:", "Quote Bank:", "Highest Risk:"])
    h1 = 1.0 if (has_upper and has_sub) else 0.0
    report["scores"]["H1_headers_labels"] = h1

    risk_lines = [ln for ln in (sections.get("Antithesis","")).splitlines() if ln.startswith("- [R")]
    quote_lines = [ln for ln in (sections.get("Antithesis","")).splitlines() if ln.strip().startswith('- "')]
    has_highest = bool(re.search(HIGHEST_RE, sections.get("Antithesis","")))
    h2 = 1.0 if (has_upper and len(risk_lines) >= 1 and len(quote_lines) >= 1 and has_highest) else 0.0
    report["scores"]["H2_structure_complete"] = h2

    c1 = 0.0 if meta.get("forbidden_hit") else 1.0
    report["scores"]["C1_forbidden_tokens"] = c1
    if meta.get("forbidden_hit"):
        report["warnings"].append(f"Forbidden tokens removed: {', '.join(meta.get('forbidden_patterns', []))}")

    risk_total = meta.get("risk_total", 0)
    risk_valid = meta.get("risk_valid", 0)
    l1 = (risk_valid / risk_total) if risk_total > 0 else 0.0
    report["scores"]["L1_risk_ledger_format"] = l1
    if risk_total < MIN_RISKS:
        report["warnings"].append(f"Risk Ledger count {risk_total} below minimum {MIN_RISKS}.")
    if meta.get("risk_overflow"):
        report["warnings"].append(f"Risk Ledger trimmed to {MAX_RISKS}; {meta['risk_overflow']} item(s) dropped.")
    invalid_risks = max(risk_total - risk_valid, 0)
    if invalid_risks > 0:
        report["warnings"].append(f"{invalid_risks} risk item(s) failed format validation.")

    q_total = meta.get("quote_total", 0)
    q_valid = meta.get("quote_valid", 0)
    q1 = (q_valid / q_total) if q_total > 0 else 0.0
    quote_in_range = MIN_QUOTES <= q_total <= MAX_QUOTES
    if not quote_in_range:
        q1 *= 0.5
    if q_total < MIN_QUOTES:
        report["warnings"].append(f"Quote Bank count {q_total} below minimum {MIN_QUOTES}.")
    if q_total > MAX_QUOTES:
        report["warnings"].append(f"Quote Bank count {q_total} exceeds maximum {MAX_QUOTES}.")
    if meta.get("quote_overflow"):
        report["warnings"].append(f"Quote Bank trimmed to {MAX_QUOTES}; {meta['quote_overflow']} quote(s) dropped.")
    invalid_quotes = max(q_total - q_valid, 0)
    if invalid_quotes > 0:
        report["warnings"].append(f"{invalid_quotes} quote(s) failed format validation.")
    report["scores"]["Q1_quote_bank_format"] = q1

    r1 = 0.0
    m = re.search(HIGHEST_RE, sections.get("Antithesis",""))
    if m:
        rid, why = m.groups()
        rid_ok = re.match(r"R\d{1,2}$", rid) is not None
        why_ok = (len(re.split(r"(?<=[.!?])\\s+", (why or "").strip())) <= 1)
        r1 = 1.0 if (rid_ok and why_ok) else 0.0
    report["scores"]["R1_highest_validity"] = r1
    if not meta.get("has_highest"):
        report["warnings"].append("Highest Risk section missing or invalid.")
    if meta.get("highest_trimmed"):
        report["warnings"].append("Highest Risk Why truncated to one sentence.")

    t_wc = word_count(sections.get("Thesis",""))
    s_wc = word_count(sections.get("Synthesis",""))
    t_ok = 1.0 if THESIS_WORD_RANGE[0] <= t_wc <= THESIS_WORD_RANGE[1] else 0.0
    s_ok = 1.0 if SYNTHESIS_WORD_RANGE[0] <= s_wc <= SYNTHESIS_WORD_RANGE[1] else 0.0
    w1 = 0.5*(t_ok + s_ok)
    report["scores"]["W1_word_ranges"] = w1

    total_score = sum(W[k]*report["scores"][k] for k in W.keys())
    report["total"] = round(total_score, 4)
    report["label"] = "Pass" if total_score >= THRESHOLD_PASS else "Poor"
    return report

def run_v8(raw_output: str) -> Dict:
    sections, meta = normalize_response(raw_output)
    report = validate_v8(sections, meta)
    return {"sections": sections, "meta": meta, "report": report}

# =======================
# BEFORE (minimal score)
# =======================
def score_before_minimal(raw: str) -> Dict[str, Any]:
    sections = slice_sections(raw)
    ant = sections.get("Antithesis","") or ""
    has_upper = all(sections.get(k,"").strip() for k in ["Thesis","Antithesis","Synthesis"])
    has_sub = all(re.search(rf"(?m)^{lbl}\\s*$", ant) for lbl in ["Risk Ledger:", "Quote Bank:", "Highest Risk:"])
    h1 = 1.0 if (has_upper and has_sub) else 0.0
    risk_lines = [ln for ln in ant.splitlines() if ln.startswith("- [R")]
    quote_lines = [ln for ln in ant.splitlines() if ln.strip().startswith('- "')]
    has_highest = bool(re.search(HIGHEST_RE, ant))
    h2 = 1.0 if (has_upper and len(risk_lines)>=1 and len(quote_lines)>=1 and has_highest) else 0.0
    forb = any(tok in (raw or "") for tok in ["<|im_start|>", "<|im_end|>"])
    c1 = 0.0 if forb else 1.0
    total = len(risk_lines)
    valid = sum(1 for ln in risk_lines if re.search(r"\|\\sLikelihood:\d\\s\|\\sImpact:\d\\s\|\\sMitigation:", ln))
    l1 = (valid/total) if total>0 else 0.0
    q_total = len(quote_lines)
    q_valid = sum(1 for ln in quote_lines if " â Source:" in ln)
    q1 = (q_valid/q_total) if q_total>0 else 0.0
    if not (1 <= q_total <= 3): q1 *= 0.5
    r1 = 1.0 if has_highest else 0.0
    t_ok = 1.0 if THESIS_WORD_RANGE[0] <= word_count(sections.get("Thesis","")) <= THESIS_WORD_RANGE[1] else 0.0
    s_ok = 1.0 if SYNTHESIS_WORD_RANGE[0] <= word_count(sections.get("Synthesis","")) <= SYNTHESIS_WORD_RANGE[1] else 0.0
    w1 = 0.5*(t_ok + s_ok)
    WW = {"H1":0.25,"H2":0.20,"C1":0.15,"L1":0.15,"Q1":0.10,"R1":0.05,"W1":0.10}
    total_score = (WW["H1"]*h1 + WW["H2"]*h2 + WW["C1"]*c1 + WW["L1"]*l1 +
                   WW["Q1"]*q1 + WW["R1"]*r1 + WW["W1"]*w1)
    label = "Pass" if total_score >= 0.72 else "Poor"
    return {"sections": sections,
            "scores": {"H1":h1,"H2":h2,"C1":c1,"L1":l1,"Q1":q1,"R1":r1,"W1":w1},
            "total": round(total_score,4), "label": label, "forbidden": forb}

# =======================
# REPORT (Markdown)
# =======================
def md_table_row(name,before,after):
    delta = (after - before) if (before is not None and after is not None) else 0.0
    def fmt(x): return "-" if x is None else f"{x:.2f}"
    sign = "+" if delta>=0 else ""
    return f"| {name} | {fmt(before)} | {fmt(after)} | {sign}{delta:.2f} |"

def unified_diff_block(before:str, after:str, title:str)->str:
    b = (before or "").splitlines(keepends=False)
    a = (after or "").splitlines(keepends=False)
    diff = difflib.unified_diff(b, a, fromfile="before", tofile="after", lineterm="")
    body = "\n".join(list(diff))
    if not body.strip():
        body = "(no change)"
    return f"### {title}\n```diff\n{body}\n```\n"

def extract_raw(obj:Dict[str,Any])->str:
    for k in ("text","output","raw","response","completion"):
        if k in obj and isinstance(obj[k], str):
            return obj[k]
    if "choices" in obj and obj["choices"]:
        ch = obj["choices"][0]
        if "text" in ch: return ch["text"]
        if "message" in ch and "content" in ch["message"]:
            return ch["message"]["content"]
    return ""

def load_jsonl(path:str)->List[Dict[str,Any]]:
    items=[]
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: items.append(json.loads(line))
            except: items.append({"text": line})
    return items

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", help="input jsonl (raw model outputs)")
    ap.add_argument("--limit", type=int, default=20, help="max samples")
    ap.add_argument("--per-file", action="store_true", help="emit per-sample md files")
    args = ap.parse_args()

    items = load_jsonl(args.jsonl)[:args.limit]
    now = datetime.datetime.now().astimezone().isoformat()
    out_path = f"{os.path.splitext(args.jsonl)[0]}.v8.report.md"

    lines = []
    lines.append(f"# System C v8 Report\n")
    lines.append(f"\nGenerated: {now}\n")
    lines.append(f"Input: `{os.path.basename(args.jsonl)}`\n")
    lines.append(f"Samples: {len(items)}\n")
    summary_insert_at = len(lines)

    metric_map = {
        "Total": ("total","total"),
        "H1 Headers/Labels": ("scores.H1","report.scores.H1_headers_labels"),
        "H2 Structure": ("scores.H2","report.scores.H2_structure_complete"),
        "C1 Forbidden": ("scores.C1","report.scores.C1_forbidden_tokens"),
        "L1 Risk Ledger": ("scores.L1","report.scores.L1_risk_ledger_format"),
        "Q1 Quote Bank": ("scores.Q1","report.scores.Q1_quote_bank_format"),
        "R1 Highest": ("scores.R1","report.scores.R1_highest_validity"),
        "W1 Word Range": ("scores.W1","report.scores.W1_word_ranges"),
    }
    def get(d, path):
        cur=d
        for p in path.split("."):
            cur = cur.get(p) if isinstance(cur, dict) else None
            if cur is None: return None
        return cur

    summary_counts = {
        "header_rescued": 0,
        "forbidden": 0,
        "quote_empty": 0,
        "risk_insufficient": 0,
        "risk_schema_fail": 0,
        "risk_overflow": 0,
        "quote_out_of_range": 0,
        "quote_schema_fail": 0,
        "quote_overflow": 0,
        "highest_missing": 0,
    }
    failure_samples = {key: [] for key in summary_counts.keys()}

    sample_rows = []

    for idx, obj in enumerate(items):
        raw = extract_raw(obj)
        before = score_before_minimal(raw)
        after  = run_v8(raw)

        meta = after.get("meta", {})
        before_scores = before.get("scores", {})
        if meta.get("header_rescue_applied"):
            summary_counts["header_rescued"] += 1
            failure_samples["header_rescued"].append(idx)
        if meta.get("forbidden_hit"):
            summary_counts["forbidden"] += 1
            failure_samples["forbidden"].append(idx)
        if meta.get("quote_total", 0) == 0:
            summary_counts["quote_empty"] += 1
            failure_samples["quote_empty"].append(idx)
        risk_total = meta.get("risk_total", 0)
        risk_valid = meta.get("risk_valid", 0)
        if risk_total < MIN_RISKS:
            summary_counts["risk_insufficient"] += 1
            failure_samples["risk_insufficient"].append(idx)
        if risk_total > 0 and risk_valid < risk_total:
            summary_counts["risk_schema_fail"] += 1
            failure_samples["risk_schema_fail"].append(idx)
        if meta.get("risk_overflow"):
            summary_counts["risk_overflow"] += 1
            failure_samples["risk_overflow"].append(idx)
        quote_total = meta.get("quote_total", 0)
        quote_valid = meta.get("quote_valid", 0)
        if not (MIN_QUOTES <= quote_total <= MAX_QUOTES):
            summary_counts["quote_out_of_range"] += 1
            failure_samples["quote_out_of_range"].append(idx)
        if quote_total > 0 and quote_valid < quote_total:
            summary_counts["quote_schema_fail"] += 1
            failure_samples["quote_schema_fail"].append(idx)
        if meta.get("quote_overflow"):
            summary_counts["quote_overflow"] += 1
            failure_samples["quote_overflow"].append(idx)
        if not meta.get("has_highest"):
            summary_counts["highest_missing"] += 1
            failure_samples["highest_missing"].append(idx)

        scores = after["report"].get("scores", {})
        before_sections = before.get("sections", {})
        before_ant = before_sections.get("Antithesis", "") or ""
        risk_total_before = len([ln for ln in before_ant.splitlines() if ln.startswith("- [R")])
        quote_total_before = len([ln for ln in before_ant.splitlines() if ln.strip().startswith('- "')])
        highest_missing_before = int(not re.search(HIGHEST_RE, before_ant))
        total_before = before["total"]
        total_after = after["report"]["total"]
        total_delta = total_after - total_before
        risk_total = meta.get("risk_total", 0)
        quote_total = meta.get("quote_total", 0)
        sample_rows.append({
            "sample": idx,
            "total_before": total_before,
            "total_after": total_after,
            "total_delta": total_delta,
            "label_before": before["label"],
            "label_after": after["report"]["label"],
            "forbidden_before": int(before.get("forbidden", False)),
            "header_rescued": int(meta.get("header_rescue_applied", False)),
            "forbidden_hit": int(meta.get("forbidden_hit", False)),
            "risk_total_before": risk_total_before,
            "risk_total": risk_total,
            "risk_total_delta": risk_total - risk_total_before,
            "risk_valid": meta.get("risk_valid", 0),
            "risk_overflow": meta.get("risk_overflow", 0),
            "quote_total_before": quote_total_before,
            "quote_total": quote_total,
            "quote_total_delta": quote_total - quote_total_before,
            "quote_valid": meta.get("quote_valid", 0),
            "quote_overflow": meta.get("quote_overflow", 0),
            "highest_missing_before": highest_missing_before,
            "highest_missing": int(not meta.get("has_highest")),
            "highest_missing_delta": int(not meta.get("has_highest")) - highest_missing_before,
            "H1_before": before_scores.get("H1", 0.0),
            "H1_delta": scores.get("H1_headers_labels", 0.0) - before_scores.get("H1", 0.0),
            "H2_before": before_scores.get("H2", 0.0),
            "H2_delta": scores.get("H2_structure_complete", 0.0) - before_scores.get("H2", 0.0),
            "C1_before": before_scores.get("C1", 0.0),
            "C1_delta": scores.get("C1_forbidden_tokens", 0.0) - before_scores.get("C1", 0.0),
            "L1_before": before_scores.get("L1", 0.0),
            "L1_delta": scores.get("L1_risk_ledger_format", 0.0) - before_scores.get("L1", 0.0),
            "Q1_before": before_scores.get("Q1", 0.0),
            "Q1_delta": scores.get("Q1_quote_bank_format", 0.0) - before_scores.get("Q1", 0.0),
            "R1_before": before_scores.get("R1", 0.0),
            "R1_delta": scores.get("R1_highest_validity", 0.0) - before_scores.get("R1", 0.0),
            "W1_before": before_scores.get("W1", 0.0),
            "W1_delta": scores.get("W1_word_ranges", 0.0) - before_scores.get("W1", 0.0),
            "H1": scores.get("H1_headers_labels", 0.0),
            "H2": scores.get("H2_structure_complete", 0.0),
            "C1": scores.get("C1_forbidden_tokens", 0.0),
            "L1": scores.get("L1_risk_ledger_format", 0.0),
            "Q1": scores.get("Q1_quote_bank_format", 0.0),
            "R1": scores.get("R1_highest_validity", 0.0),
            "W1": scores.get("W1_word_ranges", 0.0),
        })

        lines.append(f"## Sample #{idx}\n- Timestamp: {now}\n")
        lines.append("\n### Scores\n| Metric | Before | After (v8) | ? |\n|---|---:|---:|---:|")
        for name,(bp,ap) in metric_map.items():
            b = get(before, bp)
            a = after["report"]["total"] if name=="Total" else get(after, ap)
            lines.append(md_table_row(name, b, a))
        lines.append(f"\n\n**Label:** Before={before['label']} / After={after['report']['label']}\n")

        warns = after["report"].get("warnings", [])
        if warns:
            lines.append("\n### Warnings (After)\n")
            for w in warns: lines.append(f"- {w}")

        lines.append("\n### Section Diffs\n")
        bsecs = before["sections"]; asecs = after["sections"]
        lines.append(unified_diff_block(bsecs.get("Thesis",""),     asecs.get("Thesis",""),     "Thesis"))
        lines.append(unified_diff_block(bsecs.get("Antithesis",""), asecs.get("Antithesis",""), "Antithesis"))
        lines.append(unified_diff_block(bsecs.get("Synthesis",""),  asecs.get("Synthesis",""),  "Synthesis"))
        lines.append("\n---\n")

        if args.per_file:
            indiv = f"{os.path.splitext(args.jsonl)[0]}.sample{idx:03d}.v8.md"
            with open(indiv,"w",encoding="utf-8") as f:
                f.write("\n".join(lines[-2000:]))

    sample_count = len(items)
    def avg(field):
        return (sum(row.get(field, 0.0) for row in sample_rows) / sample_count) if sample_count else 0.0
    totals_before = [row["total_before"] for row in sample_rows]
    totals_after = [row["total_after"] for row in sample_rows]
    avg_total_before = sum(totals_before) / sample_count if sample_count else 0.0
    avg_total_after = sum(totals_after) / sample_count if sample_count else 0.0
    improvement_avg = avg_total_after - avg_total_before
    min_total_after = min(totals_after) if totals_after else 0.0
    max_total_after = max(totals_after) if totals_after else 0.0
    pass_count = sum(1 for row in sample_rows if row["label_after"] == "Pass")
    pass_rate = (pass_count / sample_count) if sample_count else 0.0
    score_fields = [
        ("total", "Overall Total"),
        ("H1", "Headers/Labels"),
        ("H2", "Structure"),
        ("C1", "Forbidden"),
        ("L1", "Risk Ledger"),
        ("Q1", "Quote Bank"),
        ("R1", "Highest"),
        ("W1", "Word Ranges"),
    ]
    score_table = [
        "## Score Averages",
        f"- Avg total (before): {avg_total_before:.3f}",
        f"- Avg total (after): {avg_total_after:.3f}",
        f"- Avg delta (after-before): {improvement_avg:.3f}",
        f"- Pass rate (after): {pass_rate*100:.1f}% ({pass_count}/{sample_count})",
        f"- Min/Max total (after): {min_total_after:.3f} / {max_total_after:.3f}",
        "",
        "| Metric | Avg Before | Avg After | Avg Delta |",
        "|---|---:|---:|---:|",
    ]
    for key, label in score_fields:
        if key == "total":
            avg_before_metric = avg("total_before")
            avg_after_metric = avg("total_after")
            row_label = label
        else:
            avg_before_metric = avg(f"{key}_before")
            avg_after_metric = avg(key)
            row_label = f"{key} {label}"
        score_table.append(f"| {row_label} | {avg_before_metric:.3f} | {avg_after_metric:.3f} | {(avg_after_metric - avg_before_metric):.3f} |")
    score_table.append("")
    counts_table = [
        "## Structure Counts",
        "| Item | Avg Before | Avg After | Avg Delta |",
        "|---|---:|---:|---:|",
        f"| Risk items | {avg('risk_total_before'):.3f} | {avg('risk_total'):.3f} | {(avg('risk_total') - avg('risk_total_before')):.3f} |",
        f"| Quote items | {avg('quote_total_before'):.3f} | {avg('quote_total'):.3f} | {(avg('quote_total') - avg('quote_total_before')):.3f} |",
        f"| Highest missing rate | {avg('highest_missing_before'):.3f} | {avg('highest_missing'):.3f} | {(avg('highest_missing') - avg('highest_missing_before')):.3f} |",
        ""
    ]
    def classify(row):
        if row["risk_total_before"] == 0 and row["risk_total"] > 0:
            return "Risk Added"
        if row["quote_total_before"] == 0 and row["quote_total"] > 0:
            return "Quote Added"
        if row["total_delta"] > 0.1:
            return "High Improvement"
        if row["header_rescued"] and row["total_delta"] <= 0.1:
            return "Structure Only"
        return "No Change"
    clusters = {}
    for row in sample_rows:
        label = classify(row)
        clusters.setdefault(label, []).append(row["sample"])
    cluster_table = [
        "## Cluster Summary",
        "| Cluster | Samples |",
        "|---|---|",
    ]
    for label, samples in clusters.items():
        sample_str = "none" if not samples else ", ".join(f"#{s}" for s in samples)
        cluster_table.append(f"| {label} | {sample_str} |")
    cluster_table.append("")
    def fmt_sample_entry(entry):
        return f"# {entry['sample']} (after={entry['total_after']:.3f}, Δ={entry['total_delta']:.3f})"
    lowest_after = sorted(sample_rows, key=lambda r: r["total_after"])[:min(3, sample_count)]
    highest_gain = sorted(sample_rows, key=lambda r: r["total_delta"], reverse=True)[:min(3, sample_count)]
    key_samples = [
        "## Key Samples",
        "| Category | Samples |",
        "|---|---|",
        f"| Lowest totals (after) | {', '.join(fmt_sample_entry(row) for row in lowest_after) if lowest_after else 'none'} |",
        f"| Largest total gains | {', '.join(fmt_sample_entry(row) for row in highest_gain) if highest_gain else 'none'} |",
        ""
    ]

    def fmt_gain(entries, key):
        if not entries:
            return "none"
        formatted = []
        for row in entries:
            val = row.get(key, 0)
            formatted.append(f"#{row['sample']} (+{val:.0f})")
        return ", ".join(formatted)
    risk_gainers = [row for row in sample_rows if row.get("risk_total_delta", 0) > 0]
    risk_gainers_sorted = sorted(risk_gainers, key=lambda r: r["risk_total_delta"], reverse=True)[:min(3, len(risk_gainers))]
    quote_gainers = [row for row in sample_rows if row.get("quote_total_delta", 0) > 0]
    quote_gainers_sorted = sorted(quote_gainers, key=lambda r: r["quote_total_delta"], reverse=True)[:min(3, len(quote_gainers))]
    content_spotlight = [
        "## Content Gains",
        "| Addition | Samples |",
        "|---|---|",
        f"| Risk entries added | {fmt_gain(risk_gainers_sorted, 'risk_total_delta')} |",
        f"| Quote entries added | {fmt_gain(quote_gainers_sorted, 'quote_total_delta')} |",
        ""
    ]
    summary_lines = [
        "## Summary",
        "| Metric | Count |",
        "|---|---:|",
        f"| Header rescue applied | {summary_counts['header_rescued']} / {sample_count} |",
        f"| Forbidden-token hits | {summary_counts['forbidden']} / {sample_count} |",
        f"| Quote Bank empty | {summary_counts['quote_empty']} / {sample_count} |",
        f"| Risk items below minimum | {summary_counts['risk_insufficient']} / {sample_count} |",
        f"| Risk format issues | {summary_counts['risk_schema_fail']} / {sample_count} |",
        f"| Risk overflow trimmed | {summary_counts['risk_overflow']} / {sample_count} |",
        f"| Quote count out of range | {summary_counts['quote_out_of_range']} / {sample_count} |",
        f"| Quote format issues | {summary_counts['quote_schema_fail']} / {sample_count} |",
        f"| Quote overflow trimmed | {summary_counts['quote_overflow']} / {sample_count} |",
        f"| Highest Risk missing/invalid | {summary_counts['highest_missing']} / {sample_count} |",
        ""
    ]
    def fmt_samples(key):
        items_list = failure_samples.get(key, [])
        return "none" if not items_list else ", ".join(f"#{i}" for i in items_list)
    failure_lines = [
        "## Failure Overview",
        "| Issue | Samples |",
        "|---|---|",
        f"| Risk items below minimum | {fmt_samples('risk_insufficient')} |",
        f"| Risk format issues | {fmt_samples('risk_schema_fail')} |",
        f"| Risk overflow trimmed | {fmt_samples('risk_overflow')} |",
        f"| Quote count out of range | {fmt_samples('quote_out_of_range')} |",
        f"| Quote Bank empty | {fmt_samples('quote_empty')} |",
        f"| Quote format issues | {fmt_samples('quote_schema_fail')} |",
        f"| Quote overflow trimmed | {fmt_samples('quote_overflow')} |",
        f"| Highest Risk missing/invalid | {fmt_samples('highest_missing')} |",
        f"| Header rescue applied | {fmt_samples('header_rescued')} |",
        f"| Forbidden-token hits | {fmt_samples('forbidden')} |",
        ""
    ]
    summary_block = "\n".join(summary_lines + score_table + counts_table + key_samples + content_spotlight + cluster_table + failure_lines)
    lines.insert(summary_insert_at, summary_block)
    lines.insert(summary_insert_at + 1, "---\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    csv_path = f"{os.path.splitext(args.jsonl)[0]}.v8.report.csv"
    fieldnames = [
        "sample",
        "total_before",
        "total_after",
        "total_delta",
        "label_before",
        "label_after",
        "forbidden_before",
        "header_rescued",
        "forbidden_hit",
        "risk_total_before",
        "risk_total",
        "risk_total_delta",
        "risk_valid",
        "risk_overflow",
        "quote_total_before",
        "quote_total",
        "quote_total_delta",
        "quote_valid",
        "quote_overflow",
        "highest_missing_before",
        "highest_missing",
        "highest_missing_delta",
        "H1_before",
        "H1",
        "H1_delta",
        "H2_before",
        "H2",
        "H2_delta",
        "C1_before",
        "C1",
        "C1_delta",
        "L1_before",
        "L1",
        "L1_delta",
        "Q1_before",
        "Q1",
        "Q1_delta",
        "R1_before",
        "R1",
        "R1_delta",
        "W1_before",
        "W1",
        "W1_delta",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as cf:
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()
        for row in sample_rows:
            writer.writerow(row)
        if sample_rows:
            avg_row = {
                "sample": "AVERAGE",
                "total_before": round(avg_total_before, 4),
                "total_after": round(avg_total_after, 4),
                "total_delta": round(improvement_avg, 4),
                "label_before": "",
                "label_after": f"{pass_count}/{sample_count} Pass",
                "forbidden_before": round(sum(r["forbidden_before"] for r in sample_rows) / sample_count, 4),
                "header_rescued": round(sum(r["header_rescued"] for r in sample_rows) / sample_count, 4),
                "forbidden_hit": round(sum(r["forbidden_hit"] for r in sample_rows) / sample_count, 4),
                "risk_total_before": round(sum(r["risk_total_before"] for r in sample_rows) / sample_count, 4),
                "risk_total": round(sum(r["risk_total"] for r in sample_rows) / sample_count, 4),
                "risk_total_delta": round(sum(r["risk_total_delta"] for r in sample_rows) / sample_count, 4),
                "risk_valid": round(sum(r["risk_valid"] for r in sample_rows) / sample_count, 4),
                "risk_overflow": round(sum(r["risk_overflow"] for r in sample_rows) / sample_count, 4),
                "quote_total_before": round(sum(r["quote_total_before"] for r in sample_rows) / sample_count, 4),
                "quote_total": round(sum(r["quote_total"] for r in sample_rows) / sample_count, 4),
                "quote_total_delta": round(sum(r["quote_total_delta"] for r in sample_rows) / sample_count, 4),
                "quote_valid": round(sum(r["quote_valid"] for r in sample_rows) / sample_count, 4),
                "quote_overflow": round(sum(r["quote_overflow"] for r in sample_rows) / sample_count, 4),
                "highest_missing_before": round(sum(r["highest_missing_before"] for r in sample_rows) / sample_count, 4),
                "highest_missing": round(sum(r["highest_missing"] for r in sample_rows) / sample_count, 4),
                "highest_missing_delta": round(sum(r["highest_missing_delta"] for r in sample_rows) / sample_count, 4),
                "H1_before": round(sum(r["H1_before"] for r in sample_rows) / sample_count, 4),
                "H1": round(avg("H1"), 4),
                "H1_delta": round(sum(r["H1_delta"] for r in sample_rows) / sample_count, 4),
                "H2_before": round(sum(r["H2_before"] for r in sample_rows) / sample_count, 4),
                "H2": round(avg("H2"), 4),
                "H2_delta": round(sum(r["H2_delta"] for r in sample_rows) / sample_count, 4),
                "C1_before": round(sum(r["C1_before"] for r in sample_rows) / sample_count, 4),
                "C1": round(avg("C1"), 4),
                "C1_delta": round(sum(r["C1_delta"] for r in sample_rows) / sample_count, 4),
                "L1_before": round(sum(r["L1_before"] for r in sample_rows) / sample_count, 4),
                "L1": round(avg("L1"), 4),
                "L1_delta": round(sum(r["L1_delta"] for r in sample_rows) / sample_count, 4),
                "Q1_before": round(sum(r["Q1_before"] for r in sample_rows) / sample_count, 4),
                "Q1": round(avg("Q1"), 4),
                "Q1_delta": round(sum(r["Q1_delta"] for r in sample_rows) / sample_count, 4),
                "R1_before": round(sum(r["R1_before"] for r in sample_rows) / sample_count, 4),
                "R1": round(avg("R1"), 4),
                "R1_delta": round(sum(r["R1_delta"] for r in sample_rows) / sample_count, 4),
                "W1_before": round(sum(r["W1_before"] for r in sample_rows) / sample_count, 4),
                "W1": round(avg("W1"), 4),
                "W1_delta": round(sum(r["W1_delta"] for r in sample_rows) / sample_count, 4),
            }
            writer.writerow(avg_row)
    print(f"[+] Wrote {out_path}")

if __name__ == "__main__":
    main()


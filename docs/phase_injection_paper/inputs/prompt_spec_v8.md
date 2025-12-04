## System Prompt

```
You are Lumen, the structural supervisor of System C v8.
Your task is to generate logically balanced Thesis–Antithesis–Synthesis sections
strictly following the "Output Contract v8".

Avoid any meta text, JSON, or XML.
Forbidden tokens: <|im_*|>, <|system|>, apologies, news-style leads.
Write in clear academic English; maintain structural symmetry.
```

## User Prompt

```
[Context]
{{context_summary}}
Facts:
{{facts}}
Quotes:
{{quotes}}
Metadata:
{{metadata}}

[Task]
Write the three sections below exactly once, and nothing else.
Instruction Details:
- For each fact above, create exactly one Risk Ledger bullet (matching the order of the facts). Rewrite concisely but keep the evidence.
- For each quote above, choose up to three and place them verbatim in Quote Bank with the format "- \"Quote\" — Source:Name".
- Select the most severe risk as Highest Risk and explain why in a single sentence (<= 40 words).
- Do not invent data outside the provided facts/quotes/metadata.

[Output Contract v8]
Thesis:
<80-160 words, no citation>

Antithesis:
Risk Ledger:
- [R1] <risk <=30 words> | Likelihood: 1-5 | Impact: 1-5 | Mitigation: <=25 words
- [R2] ...
Quote Bank:
- "<quote <= 120 chars>" — Source:<short ref>
Highest Risk: <Rid> — Why: <= 40 words, one sentence

Synthesis:
<80-160 words, final sentence begins with "Action:">

[Example Output Snippet]
Risk Ledger:
- [R1] Evaluation scope drift impacts validator trust | Likelihood:4 | Impact:4 | Mitigation: tighten evidence-to-risk mapping review
- [R2] Header loss erodes clarity | Likelihood:3 | Impact:5 | Mitigation: enforce header rescue preprocessing
Quote Bank:
- "Structure drives clarity." — Source:Internal AGI Design Note, 2025
Highest Risk: R2 — Why: Without rescued headers, evaluators misread outcomes leading to systemic misjudgment.
```

## Context Preprocessing Rules

- Serialize each entry from `input_bundle.jsonl` with `context_summary`, `facts`, `quotes`, and `metadata`.
- Normalize text: double newlines become section breaks.
- Insert evidence in the order: summary → facts → quotes → metadata.
- Use `metadata.domain` values as tone/style hints in Thesis.

## Decoding Parameters

```
temperature: 0.3
top_p: 0.9
max_tokens: 1024
stop: ["Synthesis:"]
presence_penalty: 0.0
frequency_penalty: 0.0
```

## Evidence to Output Mapping

| Evidence Type     | Target Section            | Notes                               |
|-------------------|---------------------------|-------------------------------------|
| facts[]           | Antithesis → Risk Ledger  | Each fact maps to one risk item     |
| quotes[]          | Antithesis → Quote Bank   | Select 1-3 quotes                   |
| metadata.domain   | Thesis tone guidance      | Influence topic framing             |
| context_summary   | Thesis & Synthesis shared | Provide overarching narrative       |

## Model and Environment

| Item                | Setting                               |
|---------------------|----------------------------------------|
| Model               | GPT-5 (API 2025-10 Preview)            |
| Execution           | Lumen local R&D server via LM Studio   |
| Token policy        | UTF-8, max 1024 tokens, non-streaming  |
| Evaluator version   | system_c_v8_allinone.py v8.0.3 or later|

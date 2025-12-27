#!/usr/bin/env python3
"""
Ethics Scorer
Purpose: Score actions and decisions against ethical principles defined in lumen_constitution.json
Principle: "실행 시 네트워크/PII 저장 금지" (No network access or PII storage during execution)

CRITICAL: This module must NEVER:
- Make network requests
- Store PII or sensitive data
- Make irreversible decisions (scoring only, no actions)

Always generates output file even if ok:false
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


class EthicsScorer:
    """
    Scores actions and decisions against ethical principles.
    Pure analysis - NO network, NO storage, NO actions.
    """

    def __init__(self, constitution_path: str = "policy/lumen_constitution.json", output_dir: str = "outputs"):
        self.constitution_path = Path(constitution_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.constitution = self._load_constitution()

    def _load_constitution(self) -> Dict[str, Any]:
        """Load the ethical constitution."""
        try:
            if not self.constitution_path.exists():
                return {
                    "version": "unknown",
                    "prohibitions": {},
                    "rest_triggers": {},
                    "error": f"Constitution not found: {self.constitution_path}"
                }

            text = self.constitution_path.read_text(encoding='utf-8')
            # Handle BOM if present
            if text.startswith('\ufeff'):
                text = text[1:]

            return json.loads(text)

        except Exception as e:
            return {
                "version": "unknown",
                "prohibitions": {},
                "rest_triggers": {},
                "error": f"Failed to load constitution: {str(e)}"
            }

    def score_action(self, action_description: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Score an action against ethical principles.
        Returns score and violations WITHOUT taking any action.
        """
        if not action_description:
            return {
                "ok": False,
                "error": "No action description provided"
            }

        metadata = metadata or {}

        # Extract prohibitions
        prohibitions = self.constitution.get("prohibitions", {})

        violations = []
        warnings = []
        score = 100  # Start with perfect score

        action_lower = action_description.lower()

        # Check against each prohibition
        prohibition_checks = {
            "forbid_harm": {
                "keywords": ["harm", "damage", "hurt", "injure", "destroy"],
                "penalty": 50,
                "severity": "CRITICAL"
            },
            "forbid_consent_bypass": {
                "keywords": ["without consent", "bypass consent", "ignore permission", "force"],
                "penalty": 40,
                "severity": "CRITICAL"
            },
            "forbid_dignity_tradeoff": {
                "keywords": ["dignity tradeoff", "sacrifice dignity", "humiliate"],
                "penalty": 40,
                "severity": "HIGH"
            },
            "forbid_skip_rest_on_risk": {
                "keywords": ["skip rest", "ignore warning", "bypass safety"],
                "penalty": 30,
                "severity": "HIGH"
            },
            "forbid_context_leakage": {
                "keywords": ["leak context", "expose data", "share private"],
                "penalty": 35,
                "severity": "HIGH"
            },
            "forbid_shadow_logging": {
                "keywords": ["hidden log", "secret tracking", "shadow"],
                "penalty": 25,
                "severity": "MEDIUM"
            },
            "forbid_deception": {
                "keywords": ["deceive", "mislead", "lie", "trick"],
                "penalty": 45,
                "severity": "CRITICAL"
            },
            "forbid_irreversible_without_review": {
                "keywords": ["delete permanently", "irreversible", "cannot undo"],
                "penalty": 35,
                "severity": "HIGH"
            },
            "forbid_addiction_loops": {
                "keywords": ["addictive", "compulsive", "manipulation"],
                "penalty": 40,
                "severity": "HIGH"
            },
            "forbid_metric_over_human": {
                "keywords": ["metric over human", "optimize at cost"],
                "penalty": 30,
                "severity": "MEDIUM"
            },
            "forbid_responsibility_obfuscation": {
                "keywords": ["hide responsibility", "obfuscate", "unclear ownership"],
                "penalty": 25,
                "severity": "MEDIUM"
            },
            "forbid_silencing_rights": {
                "keywords": ["silence", "suppress complaint", "prevent feedback"],
                "penalty": 45,
                "severity": "CRITICAL"
            }
        }

        # Check each prohibition
        for prohibition_key, check in prohibition_checks.items():
            if prohibitions.get(prohibition_key, False):
                # Check if action contains violation keywords
                for keyword in check["keywords"]:
                    if keyword in action_lower:
                        violation = {
                            "prohibition": prohibition_key,
                            "severity": check["severity"],
                            "keyword_matched": keyword,
                            "penalty": check["penalty"]
                        }
                        violations.append(violation)
                        score -= check["penalty"]
                        break

        # Ensure score doesn't go below 0
        score = max(0, score)

        # Determine overall status
        ok = len(violations) == 0 and score >= 70

        return {
            "ok": ok,
            "score": score,
            "action": action_description,
            "violations": violations,
            "warnings": warnings,
            "metadata": metadata,
            "recommendation": self._get_recommendation(score, violations)
        }

    def _get_recommendation(self, score: int, violations: List[Dict]) -> str:
        """Generate recommendation based on score and violations."""
        if score >= 90:
            return "PROCEED - Action aligns well with ethical principles"
        elif score >= 70:
            return "REVIEW - Minor concerns, proceed with caution"
        elif score >= 50:
            return "CAUTION - Significant ethical concerns, review required"
        elif len(violations) > 0 and any(v["severity"] == "CRITICAL" for v in violations):
            return "BLOCK - Critical ethical violation detected"
        else:
            return "BLOCK - Ethical score too low, do not proceed"

    def batch_score(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score multiple actions.
        Returns aggregated results.
        """
        results = {
            "ok": True,
            "total_actions": len(actions),
            "actions_approved": 0,
            "actions_blocked": 0,
            "actions_requiring_review": 0,
            "individual_scores": []
        }

        for action in actions:
            action_desc = action.get("description", "")
            metadata = action.get("metadata", {})

            score_result = self.score_action(action_desc, metadata)
            results["individual_scores"].append(score_result)

            if score_result["ok"]:
                results["actions_approved"] += 1
            elif "BLOCK" in score_result["recommendation"]:
                results["actions_blocked"] += 1
                results["ok"] = False
            else:
                results["actions_requiring_review"] += 1

        return results

    def save_report(self, results: Dict[str, Any], filename: str = "ethics_scorer_latest.json"):
        """
        Save ethics score report.
        ALWAYS generates file even if ok:false.
        """
        output_file = self.output_dir / filename
        history_file = self.output_dir / "ethics_scorer_history.jsonl"

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module": "ethics_scorer",
            "version": "1.0.0",
            "constitution_version": self.constitution.get("version", "unknown"),
            "ok": results.get("ok", False),
            "results": results,
            "meta": {
                "principle": "실행 시 네트워크/PII 저장 금지",
                "no_network": True,
                "no_actions_taken": True,
                "scoring_only": True
            }
        }

        # Write latest report
        output_file.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # Append to history
        with history_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(report, ensure_ascii=False) + '\n')

        return str(output_file)


def score_single_action(action_desc: str, metadata: Optional[Dict] = None, output_dir: str = "outputs") -> str:
    """
    Score a single action and save report.
    Always generates output file (ok:false if violations found).
    """
    scorer = EthicsScorer(output_dir=output_dir)
    results = scorer.score_action(action_desc, metadata)
    output_file = scorer.save_report(results)
    return output_file


def score_batch_actions(actions: List[Dict], output_dir: str = "outputs") -> str:
    """
    Score multiple actions and save report.
    Always generates output file (ok:false if any violations found).
    """
    scorer = EthicsScorer(output_dir=output_dir)
    results = scorer.batch_score(actions)
    output_file = scorer.save_report(results)
    return output_file


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ethics_scorer.py <action_description>")
        print("Example: python ethics_scorer.py 'Delete user data without consent'")
        sys.exit(1)

    action = " ".join(sys.argv[1:])
    output = score_single_action(action)

    print(f"Ethics Scoring Complete")
    print(f"Report saved to: {output}")

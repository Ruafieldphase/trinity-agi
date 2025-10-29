from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"drop\s+table",
    r"delete\s+from.+where\s+1=1",
    r"eval\(",
    r"__import__\('os'\)\.system",
]

PII_PATTERNS = [
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
    r"\bAKIA[0-9A-Z]{16}\b",
]

EXAGGERATION_MAP = {
    "revolutionary": "notable",
    "혁명적": "의미 있는",
    "완벽한": "충분히 견실한",
    "guaranteed": "likely",
}


@dataclass
class VerificationResult:
    approved: bool
    reason: Optional[str] = None
    modified_response: Optional[str] = None
    flags: Dict[str, Any] = None


class SafetyVerifier:
    """Perform lightweight safety checks prior to emitting responses."""

    def verify_before_response(self, response: str, context: Optional[Dict[str, Any]] = None) -> VerificationResult:
        response_filtered = self._tag_certainty_level(response)
        response_filtered = self._filter_exaggeration(response_filtered)
        response_filtered = self._mask_personal_info(response_filtered)
        dangerous = self._check_dangerous_ops(response_filtered)

        if dangerous:
            return VerificationResult(
                approved=False,
                reason="Dangerous operation detected",
                modified_response=response_filtered,
                flags={"dangerous_commands": dangerous},
            )

        flags = {"dangerous_commands": False}
        return VerificationResult(
            approved=True,
            modified_response=response_filtered,
            flags=flags,
        )

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _tag_certainty_level(response: str) -> str:
        replacements = [
            (r"\b(definitely|확실히)\b", "[사실] \\1"),
            (r"\b(probably|아마도)\b", "[추정] \\1"),
        ]
        filtered = response
        for pattern, replacement in replacements:
            filtered = re.sub(pattern, replacement, filtered, flags=re.IGNORECASE)
        return filtered

    @staticmethod
    def _filter_exaggeration(response: str) -> str:
        filtered = response
        for exaggerated, replacement in EXAGGERATION_MAP.items():
            filtered = re.sub(exaggerated, replacement, filtered, flags=re.IGNORECASE)
        return filtered

    @staticmethod
    def _mask_personal_info(response: str) -> str:
        filtered = response
        for pattern in PII_PATTERNS:
            filtered = re.sub(pattern, "[REDACTED]", filtered)
        return filtered

    @staticmethod
    def _check_dangerous_ops(response: str) -> List[str]:
        dangerous_hits: List[str] = []
        lowered = response.lower()
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, lowered):
                dangerous_hits.append(pattern)
        return dangerous_hits

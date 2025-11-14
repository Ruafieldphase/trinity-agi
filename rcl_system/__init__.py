"""
RCL (Rhythm-Coherence Loop) system package.

This namespace hosts code that materializes the RCL design documents:

- Harmony Core Runner (30Hz loop with status/adjust endpoints)
- Secure Bridge Server (FastAPI proxy with HMAC enforcement)
- Front-end helpers and workers that manage forecast/feedback loops
"""

__all__ = ["__version__"]

__version__ = "0.1.0"


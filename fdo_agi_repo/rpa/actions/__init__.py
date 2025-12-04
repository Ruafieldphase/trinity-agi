"""
RPA Actions Package
Phase 2.5 Week 2 Day 11

실행 가능한 RPA 액션들
"""

from .base import Action, ActionResult
from .click import ClickAction
from .type import TypeAction
from .install import InstallAction

__all__ = [
    'Action',
    'ActionResult',
    'ClickAction',
    'TypeAction',
    'InstallAction',
]

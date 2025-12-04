"""Approval modules for human-in-the-loop patterns."""

from .slack import SlackApproval
from .itsm import ITSMApproval

__all__ = ["SlackApproval", "ITSMApproval"]

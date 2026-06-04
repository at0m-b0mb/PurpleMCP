"""PurpleMCP guardrails — the reusable hardening library.

These are the production-quality primitives the **defense** pillar is built on.
Import them into any MCP server you write:

    from purplemcp.guardrails import safe_resolve, safe_get, safe_run

Each module documents the exact attack it neutralizes.
"""

from .approval import ApprovalDenied, auto_allow, auto_deny, cli_confirm, require
from .descriptions import (
    ToolPinner,
    find_injection,
    has_hidden_unicode,
    sanitize_description,
    tool_fingerprint,
)
from .exec import CommandNotAllowed
from .exec import run as safe_run
from .net import SSRFError, assert_url_allowed, safe_get
from .paths import PathTraversalError, safe_resolve
from .ratelimit import RateLimiter, RateLimitExceeded
from .secrets import find_secrets, scrub

__all__ = [
    # paths
    "safe_resolve",
    "PathTraversalError",
    # net
    "safe_get",
    "assert_url_allowed",
    "SSRFError",
    # exec
    "safe_run",
    "CommandNotAllowed",
    # descriptions
    "sanitize_description",
    "find_injection",
    "has_hidden_unicode",
    "tool_fingerprint",
    "ToolPinner",
    # approval
    "require",
    "cli_confirm",
    "auto_allow",
    "auto_deny",
    "ApprovalDenied",
    # secrets
    "scrub",
    "find_secrets",
    # ratelimit
    "RateLimiter",
    "RateLimitExceeded",
]

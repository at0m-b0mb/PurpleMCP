"""PurpleMCP guardrails — the reusable hardening library.

These are the production-quality primitives the **defense** pillar is built on.
Import them into any MCP server you write:

    from purplemcp.guardrails import safe_resolve, safe_get, safe_run

Each module documents the exact attack it neutralizes.
"""

from .approval import ApprovalDenied, auto_allow, auto_deny, cli_confirm, require
from .authz import AuthorizationError, assert_owner, can_access, require_scope
from .descriptions import (
    ToolPinner,
    find_injection,
    has_hidden_unicode,
    sanitize_description,
    tool_fingerprint,
)
from .exec import CommandNotAllowed
from .exec import run as safe_run
from .framing import frame_untrusted, sanitize_output, strip_control
from .net import SSRFError, assert_url_allowed, safe_get
from .paths import PathTraversalError, safe_resolve
from .ratelimit import RateLimiter, RateLimitExceeded
from .registry import (
    ToolShadowingError,
    assert_no_shadowing,
    base_name,
    enforce_allowlist,
    find_collisions,
)
from .secrets import find_secrets, scrub
from .serialization import UnsafeDeserialization, looks_like_pickle, safe_loads
from .sqlsafe import SQLIdentifierError, like_escape, safe_identifier
from .templating import TemplateInjectionError, safe_format
from .tokens import constant_time_compare, new_hex_token, new_token

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
    # serialization
    "safe_loads",
    "looks_like_pickle",
    "UnsafeDeserialization",
    # templating
    "safe_format",
    "TemplateInjectionError",
    # sqlsafe
    "safe_identifier",
    "like_escape",
    "SQLIdentifierError",
    # registry (tool shadowing)
    "find_collisions",
    "enforce_allowlist",
    "assert_no_shadowing",
    "base_name",
    "ToolShadowingError",
    # authz (broken access control)
    "assert_owner",
    "can_access",
    "require_scope",
    "AuthorizationError",
    # tokens (weak randomness)
    "new_token",
    "new_hex_token",
    "constant_time_compare",
    # framing (output / log injection)
    "strip_control",
    "sanitize_output",
    "frame_untrusted",
]

"""
Role-based tool permissions for all platforms (Open WebUI + Slack + others).

Loads ~/.hermes/role_permissions.yaml and filters toolsets based on:
- User role (admin / user / pending)
- User email or platform user ID
- Platform-specific user_overrides (slack_users section)

Used by:
- gateway/platforms/api_server.py (Open WebUI via X-OpenWebUI-User-Role header)
- gateway/run.py (Slack and other messaging platforms via source.user_id)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Module-level cache
_cache: Optional[dict] = None
_cache_mtime: float = 0.0


def _get_perms_path() -> Path:
    from hermes_constants import get_hermes_home
    return get_hermes_home() / "role_permissions.yaml"


def load_role_permissions() -> dict:
    """Load role_permissions.yaml with mtime-based caching (auto-reloads on change)."""
    global _cache, _cache_mtime
    perms_path = _get_perms_path()
    if not perms_path.exists():
        _cache = None
        return {}
    try:
        mtime = perms_path.stat().st_mtime
        if _cache is not None and mtime == _cache_mtime:
            return _cache
        import yaml
        with open(perms_path) as f:
            data = yaml.safe_load(f) or {}
        _cache = data
        _cache_mtime = mtime
        logger.info("Loaded role permissions from %s", perms_path)
        return data
    except Exception as e:
        logger.warning("Failed to load role_permissions.yaml: %s", e)
        return {}


def _apply_role_config(role_cfg: dict, platform_toolsets: list) -> list:
    """Apply a single role config dict to filter toolsets."""
    if not role_cfg:
        return platform_toolsets

    allowed = role_cfg.get("allowed_toolsets", "all")
    if allowed == "all":
        result = list(platform_toolsets)
    elif isinstance(allowed, list):
        allowed_set = set(allowed)
        result = [ts for ts in platform_toolsets if ts in allowed_set]
    else:
        result = list(platform_toolsets)

    denied_toolsets = role_cfg.get("denied_toolsets", [])
    if denied_toolsets:
        denied_set = set(denied_toolsets)
        result = [ts for ts in result if ts not in denied_set]

    return sorted(result) if result else result


def resolve_role_toolsets(
    platform_toolsets: list,
    user_role: str = "",
    user_email: str = "",
    platform_user_id: str = "",
    platform: str = "",
) -> list:
    """
    Filter platform toolsets based on user role, email, or platform user ID.

    Lookup order:
    1. slack_users / platform-specific mapping (platform_user_id → role)
    2. user_overrides by email
    3. roles by role name
    4. roles.default fallback

    Returns the filtered list of enabled toolsets.
    If no role_permissions.yaml exists, returns platform_toolsets unchanged.
    """
    perms = load_role_permissions()
    if not perms:
        return platform_toolsets

    roles_config = perms.get("roles", {})
    user_overrides = perms.get("user_overrides", {})

    # 1. Platform-specific user ID lookup (e.g. slack_users)
    platform_users_key = f"{platform}_users" if platform else ""
    platform_users = perms.get(platform_users_key, {}) if platform_users_key else {}

    if platform_user_id and platform_users:
        mapping = platform_users.get(platform_user_id)
        if mapping is not None:
            if isinstance(mapping, str):
                # Maps to a role name
                role_cfg = roles_config.get(mapping, roles_config.get("default", {}))
                return _apply_role_config(role_cfg, platform_toolsets)
            elif isinstance(mapping, dict):
                # Inline custom config
                return _apply_role_config(mapping, platform_toolsets)

    # 2. Email-based override
    effective_role = user_role.lower().strip() if user_role else "default"
    if user_email and user_email.lower() in user_overrides:
        override = user_overrides[user_email.lower()]
        if isinstance(override, str):
            effective_role = override
        elif isinstance(override, dict):
            return _apply_role_config(override, platform_toolsets)

    # 3. Role lookup (fall back to "default")
    role_cfg = roles_config.get(effective_role, roles_config.get("default", {}))
    return _apply_role_config(role_cfg, platform_toolsets)


def get_denied_tools(
    user_role: str = "",
    user_email: str = "",
    platform_user_id: str = "",
    platform: str = "",
) -> list:
    """Get the list of individually denied tool names for a user."""
    perms = load_role_permissions()
    if not perms:
        return []

    roles_config = perms.get("roles", {})
    user_overrides = perms.get("user_overrides", {})

    # 1. Platform-specific user ID lookup
    platform_users_key = f"{platform}_users" if platform else ""
    platform_users = perms.get(platform_users_key, {}) if platform_users_key else {}

    if platform_user_id and platform_users:
        mapping = platform_users.get(platform_user_id)
        if isinstance(mapping, dict):
            return mapping.get("denied_tools", [])
        elif isinstance(mapping, str):
            role_cfg = roles_config.get(mapping, roles_config.get("default", {}))
            return role_cfg.get("denied_tools", [])

    # 2. Email-based override
    effective_role = user_role.lower().strip() if user_role else "default"
    if user_email and user_email.lower() in user_overrides:
        override = user_overrides[user_email.lower()]
        if isinstance(override, dict):
            return override.get("denied_tools", [])
        elif isinstance(override, str):
            effective_role = override

    # 3. Role lookup
    role_cfg = roles_config.get(effective_role, roles_config.get("default", {}))
    return role_cfg.get("denied_tools", [])

#!/usr/bin/env python3
"""
AWS Tool Module - Safe Read-Only AWS CLI Operations

Provides a single 'aws_query' tool that executes whitelisted read-only
AWS CLI commands via subprocess. Only explicitly allowed service/command
combinations are permitted -- all others are rejected.
"""

import json
import subprocess
import shutil
from typing import Dict, Any, Optional


# =============================================================================
# Whitelisted read-only commands per AWS service
# =============================================================================

ALLOWED_COMMANDS: Dict[str, list] = {
    "ecs": [
        "list-clusters", "list-services", "list-tasks",
        "describe-services", "describe-tasks", "describe-task-definition",
        "describe-clusters",
    ],
    "ec2": [
        "describe-instances", "describe-security-groups",
        "describe-vpcs", "describe-subnets",
    ],
    "s3": ["ls", "list-buckets"],
    "cloudwatch": [
        "get-metric-data", "list-metrics", "describe-alarms",
    ],
    "logs": [
        "describe-log-groups", "filter-log-events", "get-log-events",
    ],
    "rds": ["describe-db-instances", "describe-db-clusters"],
    "iam": ["list-roles", "list-users", "get-role"],
}

ALLOWED_SERVICES = set(ALLOWED_COMMANDS.keys())

DEFAULT_REGION = "ap-south-1"


# =============================================================================
# Core logic
# =============================================================================

def _summarize_output(raw: str, max_lines: int = 80) -> str:
    """Parse JSON output and return a readable summary. Falls back to raw text."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Not JSON (e.g. s3 ls output) -- just truncate if huge
        lines = raw.strip().splitlines()
        if len(lines) > max_lines:
            return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"
        return raw.strip()

    # For JSON, pretty-print but cap length
    formatted = json.dumps(data, indent=2, default=str)
    lines = formatted.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n... (output truncated, {len(lines)} total lines)"
    return formatted


def aws_query_handler(args: Dict[str, Any], **kwargs) -> str:
    """
    Execute a whitelisted read-only AWS CLI command.

    Args:
        args: dict with keys: service, command, args (optional), region (optional)

    Returns:
        Readable string with command output or error message.
    """
    service = str(args.get("service", "")).strip().lower()
    command = str(args.get("command", "")).strip().lower()
    cli_args: Dict[str, str] = args.get("args", {}) or {}
    region = str(args.get("region", DEFAULT_REGION)).strip()

    # --- Validation ---
    if service not in ALLOWED_SERVICES:
        return f"Error: Service '{service}' is not allowed. Allowed services: {', '.join(sorted(ALLOWED_SERVICES))}"

    if command not in ALLOWED_COMMANDS[service]:
        return (
            f"Error: Command '{command}' is not allowed for service '{service}'.\n"
            f"Allowed commands: {', '.join(ALLOWED_COMMANDS[service])}"
        )

    # Check aws CLI is available
    if not shutil.which("aws"):
        return "Error: AWS CLI ('aws') is not installed or not in PATH."

    # --- Build command ---
    cmd = ["aws", service, command, "--output", "json", "--region", region]

    # Append extra arguments safely
    for key, value in cli_args.items():
        key = str(key).strip()
        # Only allow --flag style arguments
        if not key.startswith("--"):
            return f"Error: Invalid argument '{key}'. All arguments must start with '--'."
        # Block dangerous flags
        if key in ("--cli-input-json", "--cli-input-yaml", "--generate-cli-skeleton"):
            return f"Error: Argument '{key}' is not allowed."
        cmd.append(key)
        if value is not None and str(value).strip():
            cmd.append(str(value).strip())

    # --- Execute ---
    header = f"$ aws {service} {command} --region {region}"
    if cli_args:
        extra = " ".join(f"{k} {v}" for k, v in cli_args.items() if v)
        header += f" {extra}"

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return f"{header}\n\nError: Command timed out after 30 seconds."
    except Exception as e:
        return f"{header}\n\nError executing command: {e}"

    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else "(no error output)"
        return f"{header}\n\nAWS CLI error (exit {result.returncode}):\n{stderr}"

    output = result.stdout or "(no output)"
    summary = _summarize_output(output)

    return f"{header}\n\n{summary}"


def check_aws_requirements() -> bool:
    """Check if AWS CLI is available."""
    return shutil.which("aws") is not None


# =============================================================================
# OpenAI Function-Calling Schema
# =============================================================================

AWS_QUERY_SCHEMA = {
    "name": "aws_query",
    "description": (
        "Execute a read-only AWS CLI command. Only whitelisted safe commands "
        "are allowed (describe-*, list-*, get-* style operations).\n\n"
        "Supported services: ecs, ec2, s3, cloudwatch, logs, rds, iam.\n"
        "Pass extra CLI flags via the 'args' object, e.g. "
        '{"--cluster": "my-cluster", "--service-name": "web"}.'
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "enum": ["ecs", "ec2", "s3", "cloudwatch", "logs", "rds", "iam"],
                "description": "AWS service to query.",
            },
            "command": {
                "type": "string",
                "description": (
                    "The AWS CLI subcommand to run (must be whitelisted read-only). "
                    "Examples: list-clusters, describe-instances, describe-alarms."
                ),
            },
            "args": {
                "type": "object",
                "description": (
                    "Optional dict of CLI arguments. Keys are flags like '--cluster', "
                    "values are their arguments. Example: {'--cluster': 'prod'}."
                ),
                "additionalProperties": {"type": "string"},
            },
            "region": {
                "type": "string",
                "description": "AWS region (default: ap-south-1).",
                "default": "ap-south-1",
            },
        },
        "required": ["service", "command"],
    },
}


# =============================================================================
# Registry
# =============================================================================

from tools.registry import registry

registry.register(
    name="aws_query",
    toolset="aws",
    schema=AWS_QUERY_SCHEMA,
    handler=aws_query_handler,
    check_fn=check_aws_requirements,
    emoji="☁️",
)

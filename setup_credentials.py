"""
Interactive credential setup for the IDMC MCP server.
Prompts for username and password (masked), then writes them
into .mcp.json so the MCP server picks them up automatically.

Usage:
    python setup_credentials.py
"""

import json
import getpass
import os
import sys

MCP_JSON_PATH = os.path.join(os.path.dirname(__file__), ".mcp.json")


def load_mcp_json() -> dict:
    with open(MCP_JSON_PATH, "r") as f:
        return json.load(f)


def save_mcp_json(data: dict) -> None:
    with open(MCP_JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main():
    print("=" * 50)
    print("  IDMC MCP Server — Credential Setup")
    print("=" * 50)
    print()

    username = input("  IDMC Username (email): ").strip()
    if not username:
        print("  ERROR: Username cannot be empty.")
        sys.exit(1)

    password = getpass.getpass("  IDMC Password:         ")
    if not password:
        print("  ERROR: Password cannot be empty.")
        sys.exit(1)

    confirm = getpass.getpass("  Confirm Password:      ")
    if password != confirm:
        print("  ERROR: Passwords do not match.")
        sys.exit(1)

    config = load_mcp_json()
    server = config.get("mcpServers", {}).get("idmc-rest-api", {})
    server.setdefault("env", {})
    server["env"]["IDMC_USERNAME"] = username
    server["env"]["IDMC_PASSWORD"] = password
    config["mcpServers"]["idmc-rest-api"] = server
    save_mcp_json(config)

    print()
    print(f"  Saved credentials for: {username}")
    print(f"  Config written to:     {MCP_JSON_PATH}")
    print()
    print("  Restart Claude Code for the changes to take effect.")
    print("=" * 50)


if __name__ == "__main__":
    main()

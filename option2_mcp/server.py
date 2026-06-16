"""
Option 2 – Informatica Profiling MCP Server
Exposes every API endpoint as an MCP tool so it is available directly
inside Claude Code (or Claude Desktop) via natural language.

Registration in .claude/settings.json:
    {
      "mcpServers": {
        "informatica-profiling": {
          "command": "python",
          "args": ["<absolute-path>/option2_mcp/server.py"]
        }
      }
    }
"""

import sys
import os
import json
import asyncio
import logging

# Allow importing the shared package from the parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.tools import TOOLS
from shared.tool_executor import ToolExecutor

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
log = logging.getLogger("informatica-profiling-mcp")

# ── Server ────────────────────────────────────────────────────────────────────

app = Server("informatica-profiling")
executor = ToolExecutor()


# ── List tools ────────────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """Convert our shared tool definitions into MCP Tool objects."""
    mcp_tools = []
    for t in TOOLS:
        ann = t.get("annotations", {})
        mcp_tools.append(
            types.Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["input_schema"],
                annotations=types.ToolAnnotations(
                    readOnlyHint=ann.get("read_only", False),
                    destructiveHint=ann.get("destructive", False),
                    idempotentHint=ann.get("idempotent", False),
                    openWorldHint=True,
                ),
            )
        )
    log.info("Listed %d tools", len(mcp_tools))
    return mcp_tools


# ── Call tool ─────────────────────────────────────────────────────────────────

_SENSITIVE_KEYS = {"password", "old_password", "new_password"}


def _redact(arguments: dict) -> dict:
    return {
        k: "***" if k in _SENSITIVE_KEYS else v
        for k, v in arguments.items()
    }


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute the requested tool and return the result as text."""
    log.info("call_tool: %s  args=%s", name, json.dumps(_redact(arguments), default=str)[:200])

    # Run the (potentially blocking) executor in a thread pool so we don't
    # block the asyncio event loop.
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, executor.execute, name, arguments)

    result_str = json.dumps(result, indent=2, default=str)
    log.info("result: %s...", result_str[:200])

    return [types.TextContent(type="text", text=result_str)]


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    log.info("Starting Informatica Profiling MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())

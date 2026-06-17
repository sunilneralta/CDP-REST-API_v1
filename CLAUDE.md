# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Model Context Protocol (MCP) server** that exposes Informatica Intelligent Data Management Cloud (IDMC) REST APIs as 101+ callable tools within Claude Code. It enables natural language interaction with IDMC for data profiling, administration, scheduling, and data integration workflows.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure credentials (interactive native OS dialog)
python setup_credentials.py
```

Credentials are stored in `.mcp.json` under `mcpServers.idmc-rest-api.env`. The MCP server auto-launches when Claude Code starts due to `.claude/settings.local.json`.

## Running the Server

```bash
# Direct launch for debugging (normally auto-launched by Claude Code via MCP)
python server.py
```

## Architecture

Three-tier layered design:

```
Claude Code → MCP Protocol → server.py
                                  ↓
                           tool_executor.py
                                  ↓
                            api_client.py
                                  ↓
                     Informatica Cloud REST APIs
```

**`server.py`** — MCP server entry point. Lists tools, routes calls to executor, redacts credentials in stderr logs.

**`tool_executor.py`** — Maps 151+ tool names to `api_client` methods. Builds complex nested payloads for profile creation, queries, and DI jobs. Central dispatcher for all tool calls.

**`api_client.py`** — REST client wrapper. Manages session state (`session_id`, `base_url`, `pod_region`). Supports API versions v1, v2, v3, and FRS. Handles two header formats (`IDS-SESSION-ID` vs `icSessionId`).

**`tools.py`** — JSON schema definitions for all tools. Single source of truth used by both `server.py` (for listing) and `tool_executor.py` (for dispatch).

**`credential_prompt.py`** — Tkinter native OS login dialog used by `setup_credentials.py`.

## Multi-Region Support

The `pod_region` parameter in `login` determines the base URL:
- `us` → `dm-us.informaticacloud.com`
- `eu` → `dm-eu.informaticacloud.com`
- `ap` → `dm-ap.informaticacloud.com`
- `em` → `dm-em.informaticacloud.com`

## API Versioning

Different IDMC service endpoints use different API versions:
- **v1** — Data profiling service (`profiling-service/api/v1/`)
- **v2** — DI platform, connections, jobs, agents (`api/v2/`, `saas/api/v2/`)
- **v3** — Licenses, object permissions (`public/core/v3/`)
- **FRS** — File Repository Service (`frs/v1/`, `frs-dqprofile`)

## Adding a New Tool

1. Add the JSON schema definition to `tools.py` in the `TOOLS` list
2. Add the executor mapping in `tool_executor.py` inside `_dispatch()`
3. Add the corresponding API method in `api_client.py`

The tool name in `tools.py` must exactly match the key used in `tool_executor.py`.

## Key Patterns

- **Session state**: Held in the `InformaticaAPIClient` instance; `login` must be called first to populate `session_id` and `base_url` before any other tool
- **Error handling**: API errors raise `InformaticaAPIError`; `tool_executor` catches them and returns `{"error": "..."}` JSON to the caller
- **Payload builders**: Complex nested request bodies are assembled in dedicated `_build_*_payload()` methods in `api_client.py` to keep `tool_executor` clean

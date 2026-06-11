# IDMC REST API — MCP Server

A **Model Context Protocol (MCP) server** that exposes **151 Informatica Intelligent Data Management Cloud (IDMC) REST API endpoints** as callable tools inside Claude Code. Interact with IDMC entirely through natural language — no manual API calls required.

---

## Introduction

Informatica IDMC provides a rich set of REST APIs for data profiling, data integration, user administration, scheduling, and more. This MCP server acts as a bridge between Claude Code and those APIs, translating your natural language requests into the correct API calls and returning structured results.

**What you can do:**

- Profile tables and columns, inspect data quality statistics
- Manage users, roles, groups, and permissions
- Start, stop, and monitor data integration jobs
- Create and manage connections, mappings, and taskflows
- Administer schedules, runtime environments, and secure agents
- Export/import assets, manage source control, handle SAML/SSO
- And much more — 151 tools in total

**How it works:**

```
Claude Code → MCP Protocol → option2_mcp/server.py
                                       ↓
                            shared/tool_executor.py
                                       ↓
                             shared/api_client.py
                                       ↓
                          Informatica Cloud REST APIs
```

The server auto-launches when Claude Code starts; you never need to run it manually.

---

## Installation

### Prerequisites

- Python 3.9 or later
- Claude Code (CLI, desktop app, or VS Code/JetBrains extension)
- An active Informatica IDMC account

### Step 1 — Clone / download the repository

```bash
git clone <repo-url> idmc-rest-api_endusers
cd idmc-rest-api_endusers
```

### Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

Dependencies:

| Package | Purpose |
|---|---|
| `requests>=2.31.0` | HTTP client for IDMC REST calls |
| `mcp>=1.0.0` | MCP server framework |

### Step 3 — Configure your IDMC credentials

Run the interactive setup script:

```bash
python setup_credentials.py
```

You will be prompted for:

1. **IDMC Username** — your Informatica account email
2. **IDMC Password** — entered securely (masked input, never echoed)
3. **Confirm Password** — re-enter to verify

The credentials are saved to `.mcp.json` under `mcpServers.idmc-rest-api.env`:

```json
{
  "mcpServers": {
    "idmc-rest-api": {
      "env": {
        "IDMC_USERNAME": "you@example.com",
        "IDMC_PASSWORD": "your-password"
      }
    }
  }
}
```

> **Headless / CI environments:** Skip the script and set `IDMC_USERNAME` and `IDMC_PASSWORD` as environment variables directly.

### Step 4 — Enable the MCP server in Claude Code

The `.claude/settings.local.json` file already contains the required configuration:

```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["idmc-rest-api"]
}
```

This tells Claude Code to automatically launch the MCP server when you open this project. No further configuration is needed.

### Step 5 — Restart Claude Code

Restart Claude Code (or reload the window in VS Code). The MCP server starts automatically in the background.

To verify it's running, open Claude Code and type:

```
What IDMC tools do you have available?
```

Claude will list all 151 tools if the server is connected.

### Optional — Manual server launch (debugging)

```bash
python option2_mcp/server.py
```

Logs are written to `stderr` with timestamps. Credentials are automatically redacted in logs.

---

## Multi-Region Support

When logging in, specify your pod region:

| Region | `pod_region` value | Base URL |
|---|---|---|
| North America | `us` | `dm-us.informaticacloud.com` |
| Europe | `eu` | `dm-eu.informaticacloud.com` |
| Asia Pacific | `ap` | `dm-ap.informaticacloud.com` |
| EMEA | `em` | `dm-em.informaticacloud.com` |

---

## Example: End-to-End Data Profiling via Natural Language

The following example shows how a complete data profiling workflow looks entirely through natural language in Claude Code — no code, no API calls.

---

**Step 1 — Log in**

> Log in to the IDMC EM pod.

Claude calls `idmc_login` with `pod_region=em` and returns your session info.

---

**Step 2 — Find your connection**

> List all available connections.

Claude calls `idmc_list_connections` and displays connection names and IDs.

---

**Step 3 — Explore the source**

> Show me the tables available in the connection named "Oracle_Prod".

Claude calls `idmc_get_connection_objects` with the matching connection ID.

---

**Step 4 — Inspect columns**

> What columns does the CUSTOMERS table have?

Claude calls `idmc_get_object_fields` for the CUSTOMERS object.

---

**Step 5 — Create and run a profile**

> Create a data profile for the CUSTOMERS table in the "Data Quality" project and run it immediately.

Claude calls `idmc_list_projects` to find the project ID, then `idmc_create_profile` to create the profile, then `idmc_run_profile` to execute it.

---

**Step 6 — Review results**

> Show me the null percentage and distinct value count for each column in the profile results.

Claude calls `idmc_list_columns` and presents the statistics in a readable table.

---

**Step 7 — Drill into a specific column**

> What are the top 10 most frequent values in the EMAIL column?

Claude calls `idmc_get_value_frequencies` with `top_n=10`.

---

**Step 8 — Export the results**

> Export the profile results to Excel.

Claude calls `idmc_export_profile_results` and decodes the base64 response to save the file.

---

The entire workflow above requires zero knowledge of the IDMC REST API — Claude handles endpoint selection, parameter mapping, session state, and error handling automatically.

---

## All Available Tools

### Authentication

| Tool | Description |
|---|---|
| `idmc_login` | Login to Informatica Intelligent Cloud Services. Must be called first before any other tool. Returns session ID and base URL. |
| `idmc_logout` | Log out and invalidate the current session. |
| `idmc_logout_all_sessions` | Log out and end ALL active REST API sessions for the organisation. |
| `idmc_validate_session` | Check whether the current session ID is still valid and how many minutes remain. |
| `idmc_change_password` | Change a user's password. |
| `idmc_reset_password` | Reset a user's password using their security answer. |

### Connections

| Tool | Description |
|---|---|
| `idmc_list_connections` | List all available source connections in the organisation. |
| `idmc_create_connection` | Create a new connection (Salesforce, Oracle, MySQL, S3, etc.). |
| `idmc_update_connection` | Update an existing connection by connection ID. |
| `idmc_delete_connection` | Delete a connection by ID. |
| `idmc_test_connection` | Test whether a connection is working. |
| `idmc_migrate_connection` | Migrate assets from an old connector version to the latest. |
| `idmc_get_connection_objects` | List all tables / files available in a connection. |
| `idmc_get_object_fields` | List all columns / fields in a source table or file. |
| `idmc_list_connectors` | List all connectors available to the organisation. |
| `idmc_get_connector_metadata` | Get attribute metadata for a specific connector type. |

### Projects & Folders

| Tool | Description |
|---|---|
| `idmc_list_projects` | List all projects. Optionally filter by name. Supports pagination. |
| `idmc_create_project` | Create a new project to organise profiling tasks. |
| `idmc_update_project` | Update a project's name or description. |
| `idmc_delete_project` | Delete an empty project. |
| `idmc_list_folders` | List all folders inside a project by project ID. |
| `idmc_create_folder` | Create a folder inside an existing project. |
| `idmc_update_folder` | Update a folder's name or description. |
| `idmc_delete_folder` | Delete an empty folder from a project. |

### Data Profiles

| Tool | Description |
|---|---|
| `idmc_list_profiles` | List all profiles. Filter by name, project, or folder. Supports pagination. |
| `idmc_get_profile` | Get full definition of a profile by its ID. |
| `idmc_create_profile` | Create a new data profiling task. |
| `idmc_run_profile` | Execute / run a data profiling task by its ID. |
| `idmc_update_profile` | Update an existing profile definition. |
| `idmc_delete_profile` | Permanently delete a profile and all its run history. |
| `idmc_suggest_profile_name` | Get an auto-suggested name for a new profile. |
| `idmc_get_last_successful_run_key` | Return the run key of the most recent successful profile run. |
| `idmc_get_rule_ids` | Return the unique frsRuleId and ruleId for a rule associated with a profile. |

### Profile Jobs

| Tool | Description |
|---|---|
| `idmc_get_job` | Get status and step details of a profiling job by job ID. |
| `idmc_get_running_jobs` | Get all currently running jobs for a profile. |
| `idmc_stop_job` | Stop a running profiling job. |
| `idmc_resume_job` | Resume a stopped profiling job. |
| `idmc_get_session_logs` | Download session logs for a specific job step. |
| `idmc_get_session_log` | Download the session log for a completed activity log entry (base64 ZIP). |

### Profile Results

| Tool | Description |
|---|---|
| `idmc_list_columns` | List all profiled columns with statistics (null%, distinct%, patterns, etc.). |
| `idmc_get_column` | Get detailed statistics for one specific column by column ID. |
| `idmc_get_column_patterns` | Get inferred data patterns and their frequencies for a column. |
| `idmc_get_column_datatypes` | Get inferred data types for a column. |
| `idmc_get_value_frequencies` | Get top-N value frequencies (value counts) for a column. |
| `idmc_export_profile_results` | Export profile results to Excel (base64-encoded). |

### Run History

| Tool | Description |
|---|---|
| `idmc_list_run_details` | List all historical runs for a profile. |
| `idmc_get_run_detail` | Get detailed info about a specific profile run. |
| `idmc_delete_run_details` | Delete one or more historical profile runs to free storage. |
| `idmc_get_top_n_runs` | Identify the profile runs that consume the most storage space. |
| `idmc_get_top_n_profile_tasks` | Identify the profile tasks that consume the most storage space. |

### Queries

| Tool | Description |
|---|---|
| `idmc_list_queries` | List all queries associated with a profile. |
| `idmc_get_query` | Get full details of a specific query by its ID. |
| `idmc_create_query` | Create a query to filter or drill-down into profile results. |
| `idmc_update_query` | Update an existing query. |
| `idmc_execute_query` | Run an existing query by its ID. |
| `idmc_get_query_results` | Retrieve results from an executed query. |
| `idmc_delete_query` | Delete a query by its ID. |

### CLAIRE Insights

| Tool | Description |
|---|---|
| `idmc_get_insights` | Retrieve CLAIRE AI-generated data quality insights for a profile. |
| `idmc_update_insights` | Approve or reject CLAIRE insights recommendations. |

### Activity & Audit Logs

| Tool | Description |
|---|---|
| `idmc_get_activity_log` | Get completed job activity logs. Filter by task ID, run ID, or paginate. |
| `idmc_get_activity_monitor` | Get currently running jobs from the activity monitor. |
| `idmc_get_error_log` | Download the error log for a specific activity log entry. |
| `idmc_get_audit_log` | Get organisation audit log entries (user actions, config changes, etc.). |
| `idmc_get_security_logs` | Get security log entries (login/logout, user/group/role changes). Requires Admin role. |
| `idmc_get_di_job_log_entries` | Get completed DI job log entries from Operational Insights. |

### Users

| Tool | Description |
|---|---|
| `idmc_get_users` | List all users in the organisation. Supports filter and pagination. |
| `idmc_get_user` | Get details for a specific user by user ID. |
| `idmc_create_user` | Create a new user in the organisation. |
| `idmc_delete_user` | Permanently delete a user from the organisation. |
| `idmc_add_user_roles` | Add roles to a user. |
| `idmc_remove_user_roles` | Remove roles from a user. |
| `idmc_add_user_groups` | Add a user to one or more user groups. |
| `idmc_remove_user_groups` | Remove a user from one or more user groups. |

### Roles

| Tool | Description |
|---|---|
| `idmc_get_roles` | List all roles in the organisation. Supports filter and expansion. |
| `idmc_get_privileges` | List all available privileges in the organisation. |
| `idmc_create_role` | Create a new custom role with specified privileges. |
| `idmc_add_role_privileges` | Add privileges to an existing custom role. |
| `idmc_remove_role_privileges` | Remove privileges from a custom role. |
| `idmc_delete_role` | Delete a custom role from the organisation. |

### User Groups

| Tool | Description |
|---|---|
| `idmc_get_user_groups` | List all user groups. Supports filter and pagination. |
| `idmc_get_user_group` | Get details for a specific user group by ID. |
| `idmc_create_user_group` | Create a new user group. |
| `idmc_delete_user_group` | Delete a user group from the organisation. |
| `idmc_add_users_to_group` | Add users to a user group. |
| `idmc_remove_users_from_group` | Remove users from a user group. |
| `idmc_add_roles_to_group` | Add roles to a user group. |
| `idmc_remove_roles_from_group` | Remove roles from a user group. |

### Schedules

| Tool | Description |
|---|---|
| `idmc_get_schedules` | List schedules. Filter by status or get by schedule_id. |
| `idmc_create_schedule` | Create a schedule (minutely, hourly, daily, weekly, biweekly, monthly). |
| `idmc_update_schedule` | Update an existing schedule (name, status, interval, times). |
| `idmc_delete_schedule` | Delete a schedule from the organisation. |

### Runtime Environments & Secure Agents

| Tool | Description |
|---|---|
| `idmc_get_runtime_environments` | List all Secure Agent runtime environments. |
| `idmc_create_runtime_environment` | Create a new Secure Agent group (runtime environment). |
| `idmc_update_runtime_environment` | Rename a runtime environment or add/remove agents. |
| `idmc_delete_runtime_environment` | Delete a Secure Agent group by ID. |
| `idmc_get_runtime_environment_selections` | Get enabled/disabled services and connectors for a Secure Agent group. |
| `idmc_update_runtime_environment_selections` | Enable or disable services and connectors for a Secure Agent group. |
| `idmc_get_secure_agents` | List all Secure Agents in the organisation. |
| `idmc_delete_secure_agent` | Delete a Secure Agent by ID. |
| `idmc_get_agent_installer_info` | Get the install token and download URL for a Secure Agent installer. |
| `idmc_manage_secure_agent_service` | Start or stop a specific Secure Agent service. |

### Organisation & License

| Tool | Description |
|---|---|
| `idmc_get_organization` | Get details for the current organisation. |
| `idmc_get_organization_details` | Get details for the current org or a sub-organisation. |
| `idmc_update_organization` | Update organisation details (name, address, password policy). |
| `idmc_create_sub_organization` | Create a new sub-organisation (IDMC partner feature). |
| `idmc_delete_sub_organization` | Permanently delete a sub-organisation. |
| `idmc_get_license` | Get licence details for the current organisation. |
| `idmc_update_sub_org_license` | Update a sub-organisation's license (editions, limits). |

### Object Permissions

| Tool | Description |
|---|---|
| `idmc_get_object_permissions` | Get permissions on a specific IICS object (project, folder, asset). |
| `idmc_create_object_permission` | Set permissions on an IICS object for a user or group. |
| `idmc_update_object_permission` | Update an existing permission entry on an IDMC object. |
| `idmc_delete_object_permission` | Remove permissions from an IICS object. |
| `idmc_check_object_access` | Check the current user's access rights on a specific object. |

### Assets & Object Lookup

| Tool | Description |
|---|---|
| `idmc_lookup_object` | Look up IDMC objects by path+type or by ID. Returns federated IDs. |
| `idmc_list_assets` | Find and list assets using filters (type, location, tag, time, user). |
| `idmc_get_asset_dependencies` | Get objects an asset uses, or objects that use the asset. |
| `idmc_assign_tags` | Assign one or more tags to assets (up to 100 per call). |
| `idmc_remove_asset_tags` | Remove one or more tags from assets (up to 100 per call). |

### Data Integration (DI) Jobs

| Tool | Description |
|---|---|
| `idmc_get_di_tasks` | List Data Integration tasks by type (MTT, DSS, DRS, DMASK, PCS). |
| `idmc_start_di_job` | Start a Data Integration task (mapping task, replication, taskflow, etc.). |
| `idmc_stop_di_job` | Stop a running Data Integration task. |

### Mappings

| Tool | Description |
|---|---|
| `idmc_list_mappings` | List all mappings in the organisation. |
| `idmc_get_mapping` | Get details of a mapping by ID or name. |
| `idmc_get_mapping_transformations` | Get advanced transformation properties for a mapping. |

### Mapping Tasks

| Tool | Description |
|---|---|
| `idmc_list_mapping_tasks` | List all mapping tasks in the organisation. |
| `idmc_get_mapping_task` | Get details of a mapping task by ID, federated ID, or name. |
| `idmc_create_mapping_task` | Create a new mapping task based on an existing mapping. |
| `idmc_update_mapping_task` | Update an existing mapping task. |
| `idmc_delete_mapping_task` | Delete a mapping task by task ID. |

### Linear Taskflows

| Tool | Description |
|---|---|
| `idmc_list_linear_taskflows` | List all linear taskflows in the organisation. |
| `idmc_get_linear_taskflow` | Get details of a linear taskflow by ID or name. |
| `idmc_create_linear_taskflow` | Create a new linear taskflow containing a sequence of DI tasks. |
| `idmc_update_linear_taskflow` | Update an existing linear taskflow. |
| `idmc_delete_linear_taskflow` | Delete a linear taskflow by ID. |
| `idmc_get_taskflow_status` | Get the execution status of a published taskflow run. |
| `idmc_publish_taskflows` | Publish one or more advanced taskflows in bulk. |
| `idmc_unpublish_taskflows` | Unpublish one or more advanced taskflows in bulk. |

### Expression Validation & Data Preview

| Tool | Description |
|---|---|
| `idmc_validate_expression` | Validate a Data Integration expression against a source object. |
| `idmc_get_data_preview` | Preview sample rows from a source or target object via a DI connection. |

### Data Ingestion & Replication (DBMI / APPMI)

| Tool | Description |
|---|---|
| `idmc_create_ingestion_task` | Create a database (DBMI) or application (APPMI) ingestion and replication task. |
| `idmc_get_ingestion_task_id` | Look up an ingestion task's numeric ID by task name, project, or folder. |
| `idmc_deploy_ingestion_task` | Deploy an ingestion task by numeric task ID. |
| `idmc_get_ingestion_task_details` | Get full task definition details for ingestion tasks. |
| `idmc_start_ingestion_job` | Start an ingestion job by job ID. |
| `idmc_stop_ingestion_job` | Stop a running ingestion job. |
| `idmc_resume_ingestion_job` | Resume a stopped/failed ingestion job. |
| `idmc_undeploy_ingestion_job` | Undeploy an ingestion job. |
| `idmc_get_ingestion_job_status` | Get the current status of an ingestion job. |
| `idmc_get_ingestion_job_metrics` | Get detailed statistics and per-table metrics for an ingestion job. |

### File Ingestion (MI Tasks)

| Tool | Description |
|---|---|
| `idmc_list_mi_tasks` | List all file ingestion and replication (MI) tasks. |
| `idmc_create_mi_task` | Create a file ingestion and replication (MI) task. |
| `idmc_update_mi_task` | Update an existing file ingestion and replication (MI) task. |
| `idmc_delete_mi_task` | Delete a file ingestion and replication (MI) task. |
| `idmc_run_mi_task_job` | Run a file ingestion and replication task job by task ID. |
| `idmc_get_mi_task_job_status` | Get the status of a running or completed file ingestion job. |
| `idmc_get_mi_activity_log` | Get the activity log for file ingestion and replication jobs. |

### Export / Import

| Tool | Description |
|---|---|
| `idmc_start_export_job` | Start an export job to package IDMC assets into a ZIP file. |
| `idmc_get_export_job_status` | Get the status of an export job. |
| `idmc_download_export_package` | Download the export ZIP package (base64-encoded). |
| `idmc_upload_import_package` | Upload an export ZIP to prepare it for import. Returns import job ID. |
| `idmc_start_import_job` | Start an import job. Specify conflict resolution. |
| `idmc_get_import_job_status` | Get the status of an import job. |

### Source Control

| Tool | Description |
|---|---|
| `idmc_pull_objects` | Pull objects from the source control repository into the IDMC org. |
| `idmc_checkout_objects` | Check out source-controlled objects for editing (locks them). |
| `idmc_checkin_objects` | Check updated objects in to the source control repository. |
| `idmc_undo_checkout` | Undo a checkout, reverting the object to its last pulled version. |
| `idmc_compare_object_versions` | Compare two versions of a source-controlled asset. |
| `idmc_get_commit_details` | Get details about a specific source control commit. |
| `idmc_get_commit_history` | Get source control commit history for all objects or a specific asset. |
| `idmc_get_source_control_action_status` | Get the status of a source control operation. |

### Bundles

| Tool | Description |
|---|---|
| `idmc_get_bundle` | Get bundle details by bundle ID or name (omit both to list all). |
| `idmc_install_bundle` | Install a bundle on the organisation by bundle object ID. |
| `idmc_uninstall_bundle` | Uninstall a bundle from the organisation. |

### PowerCenter Mapplets

| Tool | Description |
|---|---|
| `idmc_list_pc_mapplets` | List all PowerCenter mapplets in the organisation. |
| `idmc_get_pc_mapplet` | Get details of a PowerCenter mapplet by ID or name. |
| `idmc_delete_pc_mapplet` | Delete a PowerCenter mapplet by ID. |

### Fixed-Width Configurations

| Tool | Description |
|---|---|
| `idmc_list_fwconfigs` | List all fixed-width format configurations. |
| `idmc_get_fwconfig` | Get a fixed-width format configuration by ID or name. |
| `idmc_create_fwconfig` | Create a fixed-width format configuration for flat file sources/targets. |
| `idmc_delete_fwconfig` | Delete a fixed-width format configuration by ID. |

### Metering Data

| Tool | Description |
|---|---|
| `idmc_start_metering_export` | Start a metering data export job (SUMMARY, PROJECT_FOLDER, or ASSET). |
| `idmc_get_metering_export_status` | Get the status of a metering data export job. |
| `idmc_download_metering_data` | Download the metering data ZIP file (base64-encoded). |

### Object State Synchronisation

| Tool | Description |
|---|---|
| `idmc_start_fetch_state` | Start a fetchState job to capture object states for migration. |
| `idmc_get_fetch_state_status` | Get the status of a fetchState job. |
| `idmc_download_object_states` | Download the object states ZIP package (base64-encoded). |
| `idmc_upload_load_state_package` | Upload an object states ZIP to the target org. |
| `idmc_start_load_state` | Start a loadState job to synchronise object states. |
| `idmc_get_load_state_status` | Get the status of a loadState job. |

### SAML / SSO

| Tool | Description |
|---|---|
| `idmc_get_saml_group_mappings` | Get SAML group-to-IDMC-role mappings for the organisation. |
| `idmc_get_saml_role_mappings` | Get SAML role-to-IDMC-role mappings for the organisation. |
| `idmc_add_saml_group_mappings` | Map SAML groups to IDMC roles for SSO group-based access control. |
| `idmc_add_saml_role_mappings` | Map SAML roles to IDMC roles for SSO role-based access control. |
| `idmc_remove_saml_group_mappings` | Remove SAML group-to-IDMC-role mappings. |
| `idmc_remove_saml_role_mappings` | Remove SAML role-to-IDMC-role mappings. |
| `idmc_register_identity_provider` | Register an OIDC identity provider for JWT/OAuth login. |
| `idmc_get_identity_providers` | Get the registered identity provider(s) for an organisation. |
| `idmc_update_identity_provider` | Update an existing identity provider configuration. |
| `idmc_delete_identity_provider` | Delete the registered identity provider for an organisation. |

### SCIM Tokens

| Tool | Description |
|---|---|
| `idmc_list_scim_tokens` | List SCIM tokens created for the organisation. |
| `idmc_create_scim_token` | Create a new SCIM 2.0 token for pushing users/groups from an IdP. |
| `idmc_delete_scim_token` | Delete a SCIM token by token ID. |

### IP Address Management & Key Rotation

| Tool | Description |
|---|---|
| `idmc_get_trusted_ips` | Get trusted IP address ranges configured for the organisation. |
| `idmc_update_trusted_ips` | Set trusted IP address ranges and enable/disable IP filtering. |
| `idmc_get_key_rotation_settings` | Get the current encryption key rotation interval. Requires Key Admin role. |
| `idmc_update_key_rotation_settings` | Change the encryption key rotation interval. |

### Server

| Tool | Description |
|---|---|
| `idmc_get_server_time` | Get the current IICS server time. |

---

## Architecture Reference

### File Structure

```
idmc-rest-api_endusers/
├── option2_mcp/
│   └── server.py              # MCP server entry point
├── shared/
│   ├── tools.py               # JSON schema for all 151 tools (source of truth)
│   ├── tool_executor.py       # Maps tool names → api_client methods
│   ├── api_client.py          # REST client, session state, payload builders
│   └── credential_prompt.py  # Native OS login dialog (Tkinter)
├── setup_credentials.py       # Credential setup utility
├── requirements.txt
├── .mcp.json                  # MCP server config (contains credentials)
└── .claude/
    └── settings.local.json    # Claude Code MCP enablement config
```

### Adding a New Tool

1. Add the JSON schema definition to `shared/tools.py` in the `TOOLS` list
2. Add the executor mapping in `shared/tool_executor.py` inside `execute_tool()`
3. Add the corresponding API method in `shared/api_client.py`

The tool name in `tools.py` must exactly match the key used in `tool_executor.py`.

### API Versioning

| Version | Used for |
|---|---|
| v1 | Data profiling service (`profiling-service/api/v1/`) |
| v2 | DI platform, connections, jobs, agents (`api/v2/`, `saas/api/v2/`) |
| v3 | Licenses, object permissions (`public/core/v3/`) |
| FRS | File Repository Service (`frs/v1/`, `frs-dqprofile`) |

### Session State

`idmc_login` must always be called first. It populates `session_id` and `base_url` on the `InformaticaAPIClient` instance. All subsequent tool calls use these values. Sessions expire; call `idmc_validate_session` to check remaining time.

---

## Security Notes

- Credentials are stored in `.mcp.json` — keep this file out of version control (it is listed in `.gitignore`)
- Passwords are never echoed in terminal output or logged to stderr
- `idmc_change_password` and `idmc_reset_password` support passing passwords via environment variables (`IDMC_OLD_PASSWORD`, `IDMC_NEW_PASSWORD`) instead of plaintext arguments

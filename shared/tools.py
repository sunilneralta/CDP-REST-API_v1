"""
Informatica Cloud Data Profiling - Tool Definitions
Shared tool schemas used by both Option 1 (Claude Agent) and Option 2 (MCP Server).
"""

TOOLS = [
    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    {
        "name": "idmc_login",
        "description": (
            "Login to Informatica Intelligent Cloud Services. "
            "Must be called first before any other tool. Returns session ID and base URL. "
            "Credentials are collected via a native GUI dialog. "
            "On headless systems set IDMC_USERNAME and IDMC_PASSWORD environment variables instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pod_region": {
                    "type": "string",
                    "enum": ["us", "eu", "ap", "em"],
                    "description": "us=North America, eu=Europe, ap=Asia, em=EMEA (dm-em). Default: us.",
                    "default": "us",
                },
            },
            "required": [],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_connections",
        "description": "List all available source connections in the organisation.",
            "input_schema": {
            "type": "object",
            "properties": {
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip for pagination", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_connection_objects",
        "description": "List all tables / files available in a connection.",
        "input_schema": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "Connection ID"},
                "search_pattern": {"type": "string", "description": "Optional filter pattern"},
            },
            "required": ["connection_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_object_fields",
        "description": "List all columns / fields in a source table or file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string"},
                "object_name": {"type": "string", "description": "Table or file name"},
                "source_type": {
                    "type": "string",
                    "description": "oracle, flatfile, etc.",
                    "default": "oracle",
                },
            },
            "required": ["connection_id", "object_name"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Projects / Folders
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_projects",
        "description": "List all projects. Optionally filter by name. Supports pagination via limit/offset.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":   {"type": "string", "description": "Project name to filter by"},
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip for pagination", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_project",
        "description": "Create a new project to organise profiling tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["name"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_list_folders",
        "description": "List all folders inside a project by project ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID to list folders from"},
            },
            "required": ["project_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_folder",
        "description": "Create a folder inside an existing project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["project_id", "name"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Profiles – CRUD + Run
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_profiles",
        "description": (
            "List all profiles. Can filter by name, project, folder. "
            "Use exact_match=true to find an exact profile name. Supports pagination via limit/offset."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name":             {"type": "string"},
                "exact_match":      {"type": "boolean"},
                "frs_project_name": {"type": "string"},
                "frs_folder_name":  {"type": "string"},
                "limit":            {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset":           {"type": "integer", "description": "Number of results to skip", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_profile",
        "description": "Get full definition of a profile by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
            },
            "required": ["profile_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_profile",
        "description": (
            "Create a new data profiling task. "
            "Requires a connection_id, source object name, and list of fields to profile."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Profile name"},
                "description": {"type": "string"},
                "connection_id": {"type": "string", "description": "Source connection ID"},
                "frs_project_id": {"type": "string", "description": "Project ID to store profile in"},
                "frs_folder_id": {"type": "string", "description": "Optional folder ID"},
                "source_name": {"type": "string", "description": "Table or file to profile"},
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "dataType": {"type": "string"},
                            "precision": {"type": "integer"},
                            "scale": {"type": "integer"},
                            "pcType": {"type": "string"},
                            "order": {"type": "integer"},
                        },
                        "required": ["name", "dataType"],
                    },
                    "description": "List of fields to include in the profile",
                },
                "data_source_type": {
                    "type": "string",
                    "description": "e.g. ORACLE, FLATFILE, UNSET",
                    "default": "UNSET",
                },
                "sampling_type": {
                    "type": "string",
                    "enum": ["ALL_ROWS", "RANDOM"],
                    "default": "ALL_ROWS",
                },
                "sampling_rows": {
                    "type": "integer",
                    "description": "-1 means all rows",
                    "default": -1,
                },
                "drill_down": {
                    "type": "boolean",
                    "description": "Enable drill-down on results",
                    "default": True,
                },
                "enable_claire": {
                    "type": "boolean",
                    "description": "Enable CLAIRE AI anomaly detection",
                    "default": False,
                },
                "filter_enabled": {"type": "boolean", "default": False},
                "filters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "columnName": {"type": "string"},
                            "operator": {"type": "string"},
                            "value": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["name", "connection_id", "source_name", "fields"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_run_profile",
        "description": "Execute / run a data profiling task by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
            },
            "required": ["profile_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_delete_profile",
        "description": "Permanently delete a profile and all its run history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
            },
            "required": ["profile_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_update_profile",
        "description": (
            "Update an existing profile definition. Specify only the fields you want to change; "
            "all fields are optional except profile_id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id":       {"type": "string", "description": "Profile UUID to update"},
                "name":             {"type": "string", "description": "New profile name"},
                "description":      {"type": "string"},
                "sampling_type":    {"type": "string", "enum": ["ALL_ROWS", "RANDOM"]},
                "sampling_rows":    {"type": "integer", "description": "-1 means all rows"},
                "drill_down":       {"type": "boolean", "description": "Enable drill-down"},
                "enable_claire":    {"type": "boolean", "description": "Enable CLAIRE anomaly detection"},
                "filter_enabled":   {"type": "boolean"},
                "filters": {
                    "type": "array",
                    "description": "Row filters to apply",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name":        {"type": "string"},
                            "columnName":  {"type": "string"},
                            "operator":    {"type": "string"},
                            "value":       {"type": "string"},
                        },
                    },
                },
                "fields": {
                    "type": "array",
                    "description": "Updated list of fields to profile",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name":      {"type": "string"},
                            "dataType":  {"type": "string"},
                            "precision": {"type": "integer"},
                            "scale":     {"type": "integer"},
                            "pcType":    {"type": "string"},
                        },
                        "required": ["name", "dataType"],
                    },
                },
            },
            "required": ["profile_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_suggest_profile_name",
        "description": "Get an auto-suggested name for a new profile (e.g. Profile32).",
        "input_schema": {
            "type": "object",
            "properties": {
                "frs_project_name": {"type": "string"},
                "frs_folder_name": {"type": "string"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_last_successful_run_key",
        "description": (
            "Return the run key of the most recent successful profile run. "
            "Identify by profile ID, name, project, or folder."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id":       {"type": "string", "description": "Profile UUID"},
                "profile_name":     {"type": "string", "description": "Profile name"},
                "frs_project_name": {"type": "string"},
                "frs_folder_name":  {"type": "string"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_rule_ids",
        "description": (
            "Return the unique frsRuleId and ruleId for a rule associated with a profile. "
            "Used when adding rules to profiles or looking up rule column IDs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id":       {"type": "string", "description": "Profile UUID"},
                "profile_name":     {"type": "string"},
                "frs_project_name": {"type": "string"},
                "frs_folder_name":  {"type": "string"},
                "rule_name":        {"type": "string"},
                "column_id":        {"type": "string"},
                "column_name":      {"type": "string"},
                "rule_project":     {"type": "string"},
                "rule_folder":      {"type": "string"},
                "frs_rule_id":      {"type": "string"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_job",
        "description": "Get status and step details of a profiling job by job ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_running_jobs",
        "description": "Get all currently running jobs for a profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
            },
            "required": ["profile_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_stop_job",
        "description": "Stop a running profiling job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "job_step_id": {"type": "string"},
                "job_type": {"type": "string"},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_resume_job",
        "description": "Resume a stopped profiling job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "job_step_id": {"type": "string"},
                "job_type": {"type": "string"},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_session_logs",
        "description": "Download session logs for a specific job step.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_step_id": {"type": "string"},
            },
            "required": ["job_step_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Profile Results
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_columns",
        "description": "List all profiled columns with statistics (null%, distinct%, patterns, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
            },
            "required": ["profile_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_column",
        "description": "Get detailed statistics for one specific column by column ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
                "column_id": {"type": "string"},
            },
            "required": ["profile_id", "column_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_column_patterns",
        "description": "Get inferred data patterns and their frequencies for a column.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
                "column_id": {"type": "string"},
            },
            "required": ["profile_id", "column_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_column_datatypes",
        "description": "Get inferred data types for a column.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
                "column_id": {"type": "string"},
            },
            "required": ["profile_id", "column_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_value_frequencies",
        "description": "Get top-N value frequencies (value counts) for a column.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
                "column_id": {"type": "string"},
            },
            "required": ["profile_id", "column_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_export_profile_results",
        "description": "Export profile results to Excel. Returns base64-encoded file content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
                "run_key": {"type": "integer", "default": 1},
            },
            "required": ["profile_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Run Details
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_run_details",
        "description": "List all historical runs for a profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
            },
            "required": ["profile_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_run_detail",
        "description": "Get detailed info about a specific profile run.",
        "input_schema": {
            "type": "object",
            "properties": {
                "run_detail_id": {"type": "string"},
            },
            "required": ["run_detail_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_delete_run_details",
        "description": "Delete one or more historical profile runs to free storage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
                "run_detail_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of run detail IDs to delete",
                },
            },
            "required": ["profile_id", "run_detail_ids"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_get_top_n_runs",
        "description": "Identify the profile runs that consume the most storage space.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_top_n_profile_tasks",
        "description": "Identify the profile tasks that consume the most storage space.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    {
        "name": "idmc_create_query",
        "description": (
            "Create a query to filter or drill-down into profile results. "
            "queryType: PERSISTENT (queries source) or DRILLDOWN (filters results)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "profile_id": {"type": "string"},
                "connection_id": {"type": "string"},
                "operator": {"type": "string", "enum": ["AND", "OR"], "default": "AND"},
                "query_type": {"type": "string", "enum": ["PERSISTENT", "DRILLDOWN"]},
                "conditions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "column_id": {"type": "string"},
                            "column_name": {"type": "string"},
                            "column_type": {
                                "type": "string",
                                "enum": ["DATASOURCEFIELD", "MAPPLETFIELD", "PROFILEABLECOLUMN"],
                            },
                            "operation_type": {
                                "type": "string",
                                "enum": ["VALUE", "PATTERN", "DATATYPE"],
                            },
                            "value_function": {
                                "type": "string",
                                "description": "EQUAL, NOT_EQUAL, GREATER_THAN, LESS_THAN, IS_NULL, IS_NOT_NULL, CONTAINS, STARTS_WITH, ENDS_WITH, BETWEEN, IN, NOT_IN",
                            },
                            "values": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["column_id", "column_name", "column_type", "operation_type", "value_function"],
                    },
                },
            },
            "required": ["name", "profile_id", "conditions", "query_type"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_execute_query",
        "description": "Run an existing query by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_id": {"type": "string"},
            },
            "required": ["query_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_query_results",
        "description": "Retrieve results from an executed query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_id": {"type": "string"},
            },
            "required": ["query_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_list_queries",
        "description": "List all queries associated with a profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
            },
            "required": ["profile_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_delete_query",
        "description": "Delete a query by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_id": {"type": "string"},
            },
            "required": ["query_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_get_query",
        "description": "Get full details of a specific query by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_id": {"type": "string"},
            },
            "required": ["query_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_query",
        "description": (
            "Update an existing query. Specify only the fields you want to change."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query_id":    {"type": "string", "description": "Query UUID to update"},
                "name":        {"type": "string", "description": "New query name"},
                "description": {"type": "string"},
                "operator":    {"type": "string", "enum": ["AND", "OR"]},
                "query_type":  {"type": "string", "enum": ["PERSISTENT", "DRILLDOWN"]},
                "conditions": {
                    "type": "array",
                    "description": "Updated filter conditions",
                    "items": {
                        "type": "object",
                        "properties": {
                            "column_id":       {"type": "string"},
                            "column_name":     {"type": "string"},
                            "column_type":     {"type": "string", "enum": ["DATASOURCEFIELD", "MAPPLETFIELD", "PROFILEABLECOLUMN"]},
                            "operation_type":  {"type": "string", "enum": ["VALUE", "PATTERN", "DATATYPE"]},
                            "value_function":  {"type": "string"},
                            "values":          {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["column_id", "column_name", "column_type", "operation_type", "value_function"],
                    },
                },
            },
            "required": ["query_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Admin – Activity Logs
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_activity_log",
        "description": "Get completed job activity logs. Filter by task ID, run ID, or paginate with offset/row_limit.",
        "input_schema": {
            "type": "object",
            "properties": {
                "log_id":    {"type": "string", "description": "Specific log entry ID"},
                "task_id":   {"type": "string", "description": "Filter by task ID"},
                "run_id":    {"type": "string", "description": "Filter by run ID (requires task_id)"},
                "offset":    {"type": "integer", "description": "Number of rows to skip"},
                "row_limit": {"type": "integer", "description": "Max rows to return (max 1000)"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_activity_monitor",
        "description": "Get currently running jobs from the activity monitor.",
        "input_schema": {"type": "object", "properties": {}},
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_error_log",
        "description": "Download the error log for a specific activity log entry.",
        "input_schema": {
            "type": "object",
            "properties": {
                "log_id": {"type": "string"},
            },
            "required": ["log_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Admin – Audit Logs
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_audit_log",
        "description": "Get organisation audit log entries (user actions, config changes, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "batch_id":   {"type": "integer", "description": "Batch number (0 = most recent)", "default": 0},
                "batch_size": {"type": "integer", "description": "Number of entries per batch", "default": 200},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Admin – Users
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_users",
        "description": "List all users in the organisation. Optionally filter with a query string (e.g. username==\"john@example.com\"). Supports pagination.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":  {"type": "string", "description": "Filter query, e.g. 'name==\"john@acme.com\"'"},
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_user",
        "description": "Get details for a specific user by user ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
            },
            "required": ["user_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_user",
        "description": "Create a new user in the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":      {"type": "string", "description": "Username / email"},
                "first_name": {"type": "string"},
                "last_name":  {"type": "string"},
                "title":      {"type": "string"},
                "phone":      {"type": "string"},
                "emails":     {"type": "string", "description": "Notification email address"},
                "timezone":   {"type": "string"},
                "roles":      {"type": "array", "items": {"type": "string"}, "description": "List of role names"},
            },
            "required": ["name"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_add_user_roles",
        "description": "Add roles to a user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "roles":   {"type": "array", "items": {"type": "string"}, "description": "Role names to add"},
            },
            "required": ["user_id", "roles"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_remove_user_roles",
        "description": "Remove roles from a user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "roles":   {"type": "array", "items": {"type": "string"}, "description": "Role names to remove"},
            },
            "required": ["user_id", "roles"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_add_user_groups",
        "description": "Add a user to one or more user groups.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "groups":  {"type": "array", "items": {"type": "string"}, "description": "Group IDs to add"},
            },
            "required": ["user_id", "groups"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_remove_user_groups",
        "description": "Remove a user from one or more user groups.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "groups":  {"type": "array", "items": {"type": "string"}, "description": "Group IDs to remove"},
            },
            "required": ["user_id", "groups"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_delete_user",
        "description": "Permanently delete a user from the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
            },
            "required": ["user_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_change_password",
        "description": (
            "Change a user's password. "
            "Prefer passing passwords via IDMC_OLD_PASSWORD / IDMC_NEW_PASSWORD env vars "
            "rather than as plaintext arguments."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "username":     {"type": "string"},
                "old_password": {"type": "string", "description": "Current password. Omit to use IDMC_OLD_PASSWORD env var."},
                "new_password": {"type": "string", "description": "New password. Omit to use IDMC_NEW_PASSWORD env var."},
            },
            "required": ["username"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Admin – Roles
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_roles",
        "description": "List all roles in the organisation. Use query to filter (e.g. roleName==\"Admin\") and expand=privileges to include privileges. Supports pagination.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":  {"type": "string", "description": "Filter, e.g. 'roleName==\"Designer\"'"},
                "expand": {"type": "string", "description": "Use 'privileges' to include privilege details"},
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_privileges",
        "description": "List all available privileges in the organisation.",
        "input_schema": {"type": "object", "properties": {}},
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_role",
        "description": "Create a new custom role with specified privileges.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":        {"type": "string"},
                "description": {"type": "string"},
                "privileges":  {"type": "array", "items": {"type": "string"}, "description": "Privilege IDs to assign"},
            },
            "required": ["name", "privileges"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_add_role_privileges",
        "description": "Add privileges to an existing custom role.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role_id":    {"type": "string"},
                "privileges": {"type": "array", "items": {"type": "string"}, "description": "Privilege names to add"},
            },
            "required": ["role_id", "privileges"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_remove_role_privileges",
        "description": "Remove privileges from a custom role.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role_id":    {"type": "string"},
                "privileges": {"type": "array", "items": {"type": "string"}, "description": "Privilege names to remove"},
            },
            "required": ["role_id", "privileges"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_delete_role",
        "description": "Delete a custom role from the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role_id": {"type": "string"},
            },
            "required": ["role_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Admin – User Groups
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_user_groups",
        "description": "List all user groups in the organisation. Optionally filter with a query string. Supports pagination.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":  {"type": "string", "description": "Filter query"},
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_user_group",
        "description": "Get details for a specific user group by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {"type": "string"},
            },
            "required": ["group_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_user_group",
        "description": "Create a new user group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":        {"type": "string"},
                "description": {"type": "string"},
                "roles":       {"type": "array", "items": {"type": "string"}, "description": "Role names to assign"},
                "users":       {"type": "array", "items": {"type": "string"}, "description": "User IDs to add"},
            },
            "required": ["name"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_add_users_to_group",
        "description": "Add users to a user group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {"type": "string"},
                "users":    {"type": "array", "items": {"type": "string"}, "description": "User IDs to add"},
            },
            "required": ["group_id", "users"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_remove_users_from_group",
        "description": "Remove users from a user group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {"type": "string"},
                "users":    {"type": "array", "items": {"type": "string"}, "description": "User IDs to remove"},
            },
            "required": ["group_id", "users"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_add_roles_to_group",
        "description": "Add roles to a user group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {"type": "string"},
                "roles":    {"type": "array", "items": {"type": "string"}, "description": "Role names to add"},
            },
            "required": ["group_id", "roles"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_remove_roles_from_group",
        "description": "Remove roles from a user group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {"type": "string"},
                "roles":    {"type": "array", "items": {"type": "string"}, "description": "Role names to remove"},
            },
            "required": ["group_id", "roles"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_delete_user_group",
        "description": "Delete a user group from the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {"type": "string"},
            },
            "required": ["group_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Admin – Schedules
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_schedules",
        "description": "List schedules in the organisation. Filter with query (e.g. status=='Enabled') or get by schedule_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "schedule_id": {"type": "string", "description": "Specific schedule ID"},
                "query":       {"type": "string", "description": "Filter, e.g. \"status=='Enabled'\""},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_schedule",
        "description": "Create a new schedule. Supports minutely, hourly, daily, weekly, biweekly, or monthly intervals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":         {"type": "string"},
                "description":  {"type": "string"},
                "status":       {"type": "string", "enum": ["Enabled", "Disabled"], "default": "Enabled"},
                "start_time":   {"type": "string", "description": "Start time in UTC, e.g. 2025-01-01T08:00:00.000Z"},
                "end_time":     {"type": "string", "description": "End time in UTC (optional)"},
                "interval":     {"type": "string", "enum": ["None", "Minutely", "Hourly", "Daily", "Weekly", "Biweekly", "Monthly"], "default": "Daily"},
                "frequency":    {"type": "integer", "description": "Repeat frequency, e.g. every 2 hours", "default": 1},
                "timezone":     {"type": "string", "description": "Timezone, e.g. America/New_York"},
            },
            "required": ["name", "start_time"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_schedule",
        "description": "Update an existing schedule (name, status, interval, times).",
        "input_schema": {
            "type": "object",
            "properties": {
                "schedule_id": {"type": "string"},
                "payload":     {"type": "object", "description": "Fields to update"},
            },
            "required": ["schedule_id", "payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_delete_schedule",
        "description": "Delete a schedule from the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "schedule_id": {"type": "string"},
            },
            "required": ["schedule_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Admin – Runtime Environments & Secure Agents
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_runtime_environments",
        "description": "List all Secure Agent runtime environments. Optionally get a specific one by env_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "env_id": {"type": "string", "description": "Specific runtime environment ID"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_secure_agents",
        "description": "List all Secure Agents in the organisation. Optionally get a specific agent by agent_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Specific Secure Agent ID"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Admin – Organisation
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_organization",
        "description": "Get details for the current organisation (org ID, name, edition, etc.).",
        "input_schema": {"type": "object", "properties": {}},
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Admin – Licenses
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_license",
        "description": "Get licence details for the current organisation.",
        "input_schema": {"type": "object", "properties": {}},
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Admin – Object Permissions
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_object_permissions",
        "description": "Get permissions set on a specific IICS object (project, folder, asset).",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_id": {"type": "string", "description": "FRS object ID"},
            },
            "required": ["object_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_object_permission",
        "description": "Set permissions on an IICS object for a user or group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_id": {"type": "string"},
                "payload":   {"type": "object", "description": "Permission payload with subject and permissions"},
            },
            "required": ["object_id", "payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_delete_object_permission",
        "description": "Remove permissions from an IICS object.",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_id": {"type": "string"},
                "payload":   {"type": "object", "description": "Permission payload identifying what to remove"},
            },
            "required": ["object_id", "payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Admin – DI Jobs (start/stop Data Integration tasks)
    # ------------------------------------------------------------------
    {
        "name": "idmc_start_di_job",
        "description": "Start a Data Integration task (mapping task, replication, synchronisation, linear taskflow, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id":           {"type": "string", "description": "Task ID (for tasks in Default folder)"},
                "task_federated_id": {"type": "string", "description": "Federated task ID (for tasks in projects/folders)"},
                "task_name":         {"type": "string", "description": "Task name"},
                "task_type":         {
                    "type": "string",
                    "enum": ["DMASK", "DRS", "DSS", "MTT", "PCS", "WORKFLOW"],
                    "description": "DMASK=masking, DRS=replication, DSS=sync, MTT=mapping task, PCS=PowerCenter, WORKFLOW=linear taskflow",
                },
                "callback_url":         {"type": "string", "description": "URL to POST job status when complete"},
                "parameter_file_name":  {"type": "string"},
                "parameter_file_dir":   {"type": "string"},
            },
            "required": ["task_type"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_stop_di_job",
        "description": "Stop a running Data Integration task. Use clean_stop=true for a graceful stop.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id":           {"type": "string"},
                "task_federated_id": {"type": "string"},
                "task_name":         {"type": "string"},
                "task_type":         {"type": "string", "enum": ["DMASK", "DRS", "DSS", "MTT", "PCS", "WORKFLOW"]},
                "clean_stop":        {"type": "boolean", "default": False, "description": "Gracefully stop the job"},
            },
            "required": ["task_type"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Admin – Server Time & Logout
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_server_time",
        "description": "Get the current IICS server time.",
        "input_schema": {"type": "object", "properties": {}},
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_logout",
        "description": "Log out and invalidate the current session.",
        "input_schema": {"type": "object", "properties": {}},
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # CLAIRE Insights
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_insights",
        "description": "Retrieve CLAIRE AI-generated data quality insights for a profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
            },
            "required": ["profile_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_insights",
        "description": "Approve or reject CLAIRE insights recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile_id": {"type": "string"},
                "curated_insights": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "insight_id": {"type": "integer"},
                            "column_key": {"type": "integer"},
                            "confirmation_status": {
                                "type": "string",
                                "enum": ["Approved", "Rejected"],
                            },
                        },
                        "required": ["insight_id", "column_key", "confirmation_status"],
                    },
                },
            },
            "required": ["profile_id", "curated_insights"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Platform v2 – Tasks
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_di_tasks",
        "description": "List Data Integration tasks by type (MTT, DSS, DRS, DMASK, PCS). Returns task IDs and names.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_type": {
                    "type": "string",
                    "enum": ["MTT", "DSS", "DRS", "DMASK", "PCS"],
                    "description": "MTT=mapping task, DSS=synchronization, DRS=replication, DMASK=masking, PCS=PowerCenter",
                },
            },
            "required": ["task_type"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v2 – Bundles
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_bundle",
        "description": "Get bundle details by bundle ID or name. Omit both to list all bundles.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bundle_id":   {"type": "string", "description": "Bundle ID"},
                "bundle_name": {"type": "string", "description": "Bundle name"},
                "installed":   {"type": "boolean", "description": "Filter installed bundles only"},
                "published":   {"type": "boolean", "description": "Filter published bundles only"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_install_bundle",
        "description": "Install a bundle on the organisation by bundle object ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bundle_object_id": {"type": "string", "description": "Bundle object ID to install"},
            },
            "required": ["bundle_object_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_uninstall_bundle",
        "description": "Uninstall a bundle from the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bundle_object_id": {"type": "string"},
                "update_option": {
                    "type": "string",
                    "enum": ["DELETE_EXISTING_OBJECTS", "UPDATE_EXISTING_OBJECTS", "EXCEPTION_IF_IS_USED"],
                    "default": "EXCEPTION_IF_IS_USED",
                },
            },
            "required": ["bundle_object_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v2 – Organisation management
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_organization_details",
        "description": "Get details for the current org or a sub-organisation by ID or name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id":   {"type": "string", "description": "Sub-organisation ID"},
                "org_name": {"type": "string", "description": "Sub-organisation name"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_organization",
        "description": "Update organisation or sub-organisation details (name, address, emails, password policy).",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id":  {"type": "string", "description": "Org ID to update; omit to update current org"},
                "payload": {"type": "object", "description": "Fields to update (name, city, country, employees, etc.)"},
            },
            "required": ["payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_delete_sub_organization",
        "description": "Permanently delete a sub-organisation by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
            },
            "required": ["org_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_create_sub_organization",
        "description": "Create a new sub-organisation (IDMC partner feature). Requires admin role in parent org.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_name":        {"type": "string"},
                "org_address":     {"type": "string"},
                "org_city":        {"type": "string"},
                "org_country":     {"type": "string"},
                "org_employees":   {"type": "string", "description": "e.g. 11_25, 26_50, 51_100"},
                "admin_username":  {"type": "string", "description": "Email for the new org admin"},
                "admin_password":  {"type": "string"},
                "admin_first_name": {"type": "string"},
                "admin_last_name":  {"type": "string"},
                "admin_title":     {"type": "string"},
                "admin_phone":     {"type": "string"},
                "admin_email":     {"type": "string"},
            },
            "required": ["org_name", "org_address", "org_city", "org_country", "org_employees",
                         "admin_username", "admin_password", "admin_first_name", "admin_last_name",
                         "admin_title", "admin_phone", "admin_email"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v2 – Secure Agent management
    # ------------------------------------------------------------------
    {
        "name": "idmc_delete_secure_agent",
        "description": "Delete a Secure Agent by ID. Ensure no connections use the agent before deleting.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
            },
            "required": ["agent_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_get_agent_installer_info",
        "description": "Get the install token and download URL for a Secure Agent installer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "enum": ["win64", "linux64"], "default": "linux64"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v2 – Runtime Environment (Secure Agent Group) management
    # ------------------------------------------------------------------
    {
        "name": "idmc_create_runtime_environment",
        "description": "Create a new Secure Agent group (runtime environment).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":      {"type": "string"},
                "is_shared": {"type": "boolean", "default": False},
            },
            "required": ["name"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_runtime_environment",
        "description": "Update a Secure Agent group — rename it or add/remove agents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "env_id":    {"type": "string"},
                "name":      {"type": "string"},
                "is_shared": {"type": "boolean"},
                "agents":    {
                    "type": "array",
                    "items": {"type": "object", "properties": {"id": {"type": "string"}, "orgId": {"type": "string"}}},
                    "description": "Agents to assign to the group",
                },
            },
            "required": ["env_id", "name"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_delete_runtime_environment",
        "description": "Delete a Secure Agent group by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "env_id": {"type": "string"},
            },
            "required": ["env_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_get_runtime_environment_selections",
        "description": "Get enabled/disabled services and connectors for a Secure Agent group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "env_id":  {"type": "string"},
                "details": {"type": "boolean", "description": "Include disabled selections too", "default": False},
            },
            "required": ["env_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_runtime_environment_selections",
        "description": "Enable or disable services and connectors for a Secure Agent group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "env_id":  {"type": "string"},
                "payload": {"type": "object", "description": "Selections payload with services and connectors arrays"},
            },
            "required": ["env_id", "payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Platform v2 – Session logs & session validation
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_session_log",
        "description": "Download the session log for a completed activity log entry. Returns base64-encoded ZIP content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "log_id":        {"type": "string", "description": "Top-level activity log entry ID"},
                "item_id":       {"type": "string", "description": "Child item ID for replication/taskflow subtask"},
                "child_item_id": {"type": "string", "description": "Sub-subtask ID for 3-level taskflows"},
            },
            "required": ["log_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_validate_session",
        "description": "Check whether the current session ID is still valid and how many minutes remain.",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
            },
            "required": ["username"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_logout_all_sessions",
        "description": "Log out and end ALL active REST API sessions for the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password": {"type": "string"},
            },
            "required": ["username", "password"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Lookup & Objects
    # ------------------------------------------------------------------
    {
        "name": "idmc_lookup_object",
        "description": "Look up one or more IDMC objects by path+type or by ID. Returns federated IDs needed for jobs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "objects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":   {"type": "string", "description": "Object ID"},
                            "path": {"type": "string", "description": "Full path, e.g. Default/MyTask"},
                            "type": {"type": "string", "description": "Object type, e.g. MTT, DSS, WORKFLOW, PROJECT, FOLDER, CONNECTION"},
                        },
                    },
                    "description": "List of objects to look up. Provide id OR path+type per object.",
                },
            },
            "required": ["objects"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_list_project_assets",
        "description": (
            "Recursively list ALL assets inside a project, including assets nested in subfolders. "
            "Performs a two-phase fetch: phase 1 discovers top-level folders, phase 2 fans out "
            "to every subfolder in parallel. Returns a flat table with columns: project, folder, "
            "path, asset_name, type, updated_on, updated_by, description, tags. "
            "Use this instead of idmc_list_assets when you need a complete project inventory."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Exact project name as it appears in IDMC (case-sensitive), e.g. 'SUCHERUKURI'",
                },
            },
            "required": ["project_name"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_list_assets",
        "description": "Find and list assets in the organisation using filters (type, location, tag, updateTime, updatedBy).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":  {"type": "string", "description": "Filter, e.g. \"type=='MTT' and location=='Default'\""},
                "limit":  {"type": "integer", "description": "Max assets to return (up to 200)", "default": 200},
                "skip":   {"type": "integer", "description": "Number of assets to skip for pagination", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_asset_dependencies",
        "description": "Get objects that an asset uses ('uses') or objects that use the asset ('usedBy').",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_id": {"type": "string"},
                "ref_type":  {"type": "string", "enum": ["uses", "usedBy"], "default": "uses"},
                "limit":     {"type": "integer", "default": 25},
                "skip":      {"type": "integer", "default": 0},
            },
            "required": ["object_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Passwords
    # ------------------------------------------------------------------
    {
        "name": "idmc_reset_password",
        "description": "Reset a user's password using their security answer (for expired/forgotten passwords).",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id":         {"type": "string"},
                "security_answer": {"type": "string"},
                "new_password":    {"type": "string"},
            },
            "required": ["user_id", "security_answer", "new_password"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Object Permissions (update + check access)
    # ------------------------------------------------------------------
    {
        "name": "idmc_update_object_permission",
        "description": "Update an existing ACL (permission entry) on an IDMC object.",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_id":     {"type": "string"},
                "permission_id": {"type": "string", "description": "ACL ID to update"},
                "payload":       {"type": "object", "description": "Updated principal and permissions"},
            },
            "required": ["object_id", "permission_id", "payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_check_object_access",
        "description": "Check the current user's access rights on a specific object or asset type within a container.",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_id":   {"type": "string"},
                "asset_type":  {"type": "string", "description": "Optional asset type to check create permission, e.g. MTT, DTEMPLATE"},
            },
            "required": ["object_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Projects & Folders (update/delete)
    # ------------------------------------------------------------------
    {
        "name": "idmc_update_project",
        "description": "Update a project's name or description.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id":   {"type": "string", "description": "Project ID"},
                "project_name": {"type": "string", "description": "Project name (use instead of project_id)"},
                "name":         {"type": "string", "description": "New name"},
                "description":  {"type": "string"},
            },
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_delete_project",
        "description": "Delete an empty project (must contain no assets or folders).",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id":   {"type": "string"},
                "project_name": {"type": "string"},
            },
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_update_folder",
        "description": "Update a folder's name or description inside a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id":   {"type": "string"},
                "folder_id":    {"type": "string"},
                "name":         {"type": "string"},
                "description":  {"type": "string"},
            },
            "required": ["folder_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_delete_folder",
        "description": "Delete an empty folder from a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id":   {"type": "string"},
                "folder_id":    {"type": "string"},
            },
            "required": ["folder_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Export / Import
    # ------------------------------------------------------------------
    {
        "name": "idmc_start_export_job",
        "description": "Start an export job to package IDMC assets (mappings, tasks, connections, schedules, etc.) into a ZIP file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Job name"},
                "objects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":                   {"type": "string"},
                            "include_dependencies": {"type": "boolean", "default": True},
                        },
                        "required": ["id"],
                    },
                    "description": "List of object IDs to export",
                },
            },
            "required": ["objects"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_export_job_status",
        "description": "Get the status of an export job. Use expand_objects=true to see per-object status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "export_id":      {"type": "string"},
                "expand_objects": {"type": "boolean", "default": False},
            },
            "required": ["export_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_download_export_package",
        "description": "Download the export ZIP package once the export job is SUCCESSFUL. Returns base64-encoded content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "export_id": {"type": "string"},
            },
            "required": ["export_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_upload_import_package",
        "description": "Upload an export ZIP file to prepare it for import. Returns the import job ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Local path to the ZIP file to upload"},
            },
            "required": ["file_path"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_start_import_job",
        "description": "Start an import job using the job ID from upload_import_package. Specify conflict resolution.",
        "input_schema": {
            "type": "object",
            "properties": {
                "import_job_id":              {"type": "string"},
                "name":                       {"type": "string"},
                "default_conflict_resolution": {"type": "string", "enum": ["OVERWRITE", "REUSE"], "default": "REUSE"},
                "include_objects":             {"type": "array", "items": {"type": "string"}, "description": "Object IDs to include"},
            },
            "required": ["import_job_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_import_job_status",
        "description": "Get the status of an import job. Use expand_objects=true for per-object status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "import_id":      {"type": "string"},
                "expand_objects": {"type": "boolean", "default": False},
            },
            "required": ["import_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Security Logs
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_security_logs",
        "description": "Get security log entries (login/logout, user/group/role changes). Requires Admin role.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":  {"type": "string", "description": "Filter, e.g. \"actor=='admin'\""},
                "limit":  {"type": "integer", "default": 200},
                "skip":   {"type": "integer", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – IP Address Management
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_trusted_ips",
        "description": "Get trusted IP address ranges configured for the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "string", "description": "Organisation ID"},
            },
            "required": ["org_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_trusted_ips",
        "description": "Set trusted IP address ranges and enable/disable IP filtering for the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id":    {"type": "string"},
                "enable_ip": {"type": "boolean"},
                "ip_ranges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start_ip": {"type": "string"},
                            "end_ip":   {"type": "string"},
                        },
                    },
                },
            },
            "required": ["org_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Key Rotation
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_key_rotation_settings",
        "description": "Get the current encryption key rotation interval and valid options. Requires Key Admin role.",
        "input_schema": {"type": "object", "properties": {}},
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_key_rotation_settings",
        "description": "Change the encryption key rotation interval (90_DAYS, 120_DAYS, 180_DAYS, 365_DAYS).",
        "input_schema": {
            "type": "object",
            "properties": {
                "rotation_interval": {
                    "type": "string",
                    "enum": ["90_DAYS", "120_DAYS", "180_DAYS", "365_DAYS"],
                },
            },
            "required": ["rotation_interval"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Sub-org License Management
    # ------------------------------------------------------------------
    {
        "name": "idmc_update_sub_org_license",
        "description": "Update a sub-organisation's license (editions, custom licenses, limits). Requires parent org Admin.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id":  {"type": "string"},
                "payload": {"type": "object", "description": "License payload with customLicenses, assignedEditions, customLimits"},
            },
            "required": ["org_id", "payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Metering Data
    # ------------------------------------------------------------------
    {
        "name": "idmc_start_metering_export",
        "description": "Start a metering data export job. job_type: SUMMARY, PROJECT_FOLDER, or ASSET.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date":     {"type": "string", "description": "ISO 8601 start date, e.g. 2024-01-01T00:00:00Z"},
                "end_date":       {"type": "string"},
                "job_type":       {"type": "string", "enum": ["SUMMARY", "PROJECT_FOLDER", "ASSET"], "default": "SUMMARY"},
                "all_linked_orgs": {"type": "boolean", "default": False},
                "callback_url":   {"type": "string"},
            },
            "required": ["start_date", "end_date", "job_type"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_metering_export_status",
        "description": "Get the status of a metering data export job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_download_metering_data",
        "description": "Download the metering data ZIP file once the export job status is SUCCESS. Returns base64-encoded content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Object State Synchronisation (fetchState / loadState)
    # ------------------------------------------------------------------
    {
        "name": "idmc_start_fetch_state",
        "description": "Start a fetchState job to capture object states (sequence values, in-out params) for migration.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "objects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":                   {"type": "string"},
                            "include_dependencies": {"type": "boolean", "default": True},
                        },
                        "required": ["id"],
                    },
                },
            },
            "required": ["objects"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_fetch_state_status",
        "description": "Get the status of a fetchState job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id":         {"type": "string"},
                "expand_objects": {"type": "boolean", "default": False},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_download_object_states",
        "description": "Download the object states ZIP package from a completed fetchState job. Returns base64-encoded content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_upload_load_state_package",
        "description": "Upload an object states ZIP to the target org to prepare for loadState.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Local path to the object states ZIP"},
            },
            "required": ["file_path"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_start_load_state",
        "description": "Start a loadState job to synchronise object states into the target org.",
        "input_schema": {
            "type": "object",
            "properties": {
                "load_job_id":     {"type": "string", "description": "Job ID from upload_load_state_package"},
                "name":            {"type": "string"},
                "include_objects": {"type": "array", "items": {"type": "string"}, "description": "Object IDs to include"},
            },
            "required": ["load_job_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_load_state_status",
        "description": "Get the status of a loadState job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id":         {"type": "string"},
                "expand_objects": {"type": "boolean", "default": False},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – SAML Group & Role Mappings
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_saml_group_mappings",
        "description": "Get SAML group-to-IDMC-role mappings for the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "query":  {"type": "string", "description": "Filter, e.g. roleName==\"Admin\""},
            },
            "required": ["org_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_saml_role_mappings",
        "description": "Get SAML role-to-IDMC-role mappings for the organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "query":  {"type": "string"},
            },
            "required": ["org_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_add_saml_group_mappings",
        "description": "Map SAML groups to IDMC roles for SSO group-based access control.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "group_mappings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role_name":        {"type": "string"},
                            "saml_group_names": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["role_name", "saml_group_names"],
                    },
                },
                "reuse_group": {"type": "boolean", "default": False},
            },
            "required": ["org_id", "group_mappings"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_add_saml_role_mappings",
        "description": "Map SAML roles to IDMC roles for SSO role-based access control.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "role_mappings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role_name":       {"type": "string"},
                            "saml_role_names": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["role_name", "saml_role_names"],
                    },
                },
            },
            "required": ["org_id", "role_mappings"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_remove_saml_group_mappings",
        "description": "Remove SAML group-to-IDMC-role mappings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "group_mappings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role_name":        {"type": "string"},
                            "saml_group_names": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
            "required": ["org_id", "group_mappings"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_remove_saml_role_mappings",
        "description": "Remove SAML role-to-IDMC-role mappings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "role_mappings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role_name":       {"type": "string"},
                            "saml_role_names": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
            "required": ["org_id", "role_mappings"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Identity Providers
    # ------------------------------------------------------------------
    {
        "name": "idmc_register_identity_provider",
        "description": "Register an OIDC identity provider for JWT/OAuth login. Only one IDP per org.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id":             {"type": "string"},
                "issuer_url":         {"type": "string", "description": "Absolute URL of the identity provider issuer"},
                "keys_url":           {"type": "string", "description": "Absolute URL of the JWT token keys"},
                "token_claim":        {"type": "string", "default": "sub"},
                "match_type":         {"type": "string", "enum": ["uid", "aliasName"], "default": "uid"},
                "signing_algorithm":  {"type": "string", "default": "RS256"},
            },
            "required": ["org_id", "issuer_url", "keys_url"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_identity_providers",
        "description": "Get the registered identity provider(s) for an organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
            },
            "required": ["org_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_identity_provider",
        "description": "Update an existing identity provider configuration.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id":            {"type": "string"},
                "idp_id":            {"type": "string"},
                "issuer_url":        {"type": "string"},
                "keys_url":          {"type": "string"},
                "token_claim":       {"type": "string"},
                "match_type":        {"type": "string", "enum": ["uid", "aliasName"]},
                "signing_algorithm": {"type": "string"},
            },
            "required": ["org_id", "idp_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_delete_identity_provider",
        "description": "Delete the registered identity provider for an organisation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id": {"type": "string"},
                "idp_id": {"type": "string"},
            },
            "required": ["org_id", "idp_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – SCIM Tokens
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_scim_tokens",
        "description": "List SCIM tokens created for the organisation.",
        "input_schema": {"type": "object", "properties": {}},
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_scim_token",
        "description": "Create a new SCIM 2.0 token for pushing users/groups from an IdP.",
        "input_schema": {"type": "object", "properties": {}},
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_delete_scim_token",
        "description": "Delete a SCIM token by token ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "token_id": {"type": "string"},
            },
            "required": ["token_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Secure Agent Service (start/stop)
    # ------------------------------------------------------------------
    {
        "name": "idmc_manage_secure_agent_service",
        "description": "Start or stop a specific Secure Agent service (e.g. Data Integration Server).",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_id":       {"type": "string", "description": "Secure Agent ID"},
                "service_name":   {"type": "string", "description": "Display name of the service, e.g. 'Data Integration Server'"},
                "service_action": {"type": "string", "enum": ["start", "stop"]},
            },
            "required": ["agent_id", "service_name", "service_action"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Tags
    # ------------------------------------------------------------------
    {
        "name": "idmc_assign_tags",
        "description": "Assign one or more tags to assets (up to 100 assets per call).",
        "input_schema": {
            "type": "object",
            "properties": {
                "tag_assignments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":   {"type": "string", "description": "Asset ID"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["id", "tags"],
                    },
                },
            },
            "required": ["tag_assignments"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_remove_asset_tags",
        "description": "Remove one or more tags from assets (up to 100 assets per call).",
        "input_schema": {
            "type": "object",
            "properties": {
                "tag_removals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":   {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["id", "tags"],
                    },
                },
            },
            "required": ["tag_removals"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Platform v3 – Source Control
    # ------------------------------------------------------------------
    {
        "name": "idmc_pull_objects",
        "description": "Pull (load) objects from the source control repository into the IDMC org.",
        "input_schema": {
            "type": "object",
            "properties": {
                "commit_hash": {"type": "string"},
                "objects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":   {"type": "string"},
                            "path": {"type": "array", "items": {"type": "string"}},
                            "type": {"type": "string"},
                        },
                    },
                    "description": "Objects to pull. Provide id or path+type per object.",
                },
            },
            "required": ["commit_hash", "objects"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_checkout_objects",
        "description": "Check out source-controlled objects so they can be edited (locks them).",
        "input_schema": {
            "type": "object",
            "properties": {
                "objects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":                     {"type": "string"},
                            "path":                   {"type": "array", "items": {"type": "string"}},
                            "type":                   {"type": "string"},
                            "include_container_assets": {"type": "boolean", "default": False},
                        },
                    },
                },
            },
            "required": ["objects"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_checkin_objects",
        "description": "Check updated objects in to the source control repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "objects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":                     {"type": "string"},
                            "path":                   {"type": "array", "items": {"type": "string"}},
                            "type":                   {"type": "string"},
                            "include_container_assets": {"type": "boolean", "default": False},
                        },
                    },
                },
                "summary":     {"type": "string", "description": "Check-in summary message"},
                "description": {"type": "string"},
            },
            "required": ["objects", "summary"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_undo_checkout",
        "description": "Undo a source control checkout, reverting the object to its last pulled version.",
        "input_schema": {
            "type": "object",
            "properties": {
                "objects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id":   {"type": "string"},
                            "path": {"type": "array", "items": {"type": "string"}},
                            "type": {"type": "string"},
                        },
                    },
                },
                "checkout_operation_id": {"type": "string", "description": "Undo all objects from a specific checkout operation"},
            },
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_compare_object_versions",
        "description": "Compare two versions of a source-controlled asset to see differences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id":     {"type": "string"},
                "source":       {"type": "string", "description": "Commit hash or CURRENT-VERSION"},
                "destination":  {"type": "string", "description": "Commit hash or CURRENT-VERSION"},
                "output_format": {"type": "string", "enum": ["JSON", "TEXT"], "default": "JSON"},
            },
            "required": ["asset_id", "source", "destination"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_commit_details",
        "description": "Get details about a specific source control commit (changed objects, author, message).",
        "input_schema": {
            "type": "object",
            "properties": {
                "commit_hash": {"type": "string"},
            },
            "required": ["commit_hash"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_commit_history",
        "description": "Get source control commit history for all objects or a specific asset/project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":    {"type": "string", "description": "Filter, e.g. \"id=='abc123'\" or \"path=='Default/MyMapping'\""},
                "per_page": {"type": "integer", "default": 100},
                "page":     {"type": "integer", "default": 1},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_source_control_action_status",
        "description": "Get the status of a source control operation (pull, push, checkout, checkin).",
        "input_schema": {
            "type": "object",
            "properties": {
                "action_id":      {"type": "string"},
                "expand_objects": {"type": "boolean", "default": False},
            },
            "required": ["action_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – Connections CRUD
    # ------------------------------------------------------------------
    {
        "name": "idmc_create_connection",
        "description": "Create a new connection in the organisation (Salesforce, Oracle, MySQL, S3, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":                  {"type": "string"},
                "type":                  {"type": "string", "description": "Connection type, e.g. Salesforce, Oracle, MySQL, CSVFile, TOOLKIT"},
                "description":           {"type": "string"},
                "runtime_environment_id": {"type": "string"},
                "username":              {"type": "string"},
                "password":              {"type": "string"},
                "host":                  {"type": "string"},
                "port":                  {"type": "integer"},
                "database":              {"type": "string"},
                "schema":                {"type": "string"},
                "service_url":           {"type": "string"},
                "extra_properties":      {"type": "object", "description": "Additional connector-specific properties"},
            },
            "required": ["name", "type"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_connection",
        "description": "Update an existing connection by connection ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string"},
                "payload":       {"type": "object", "description": "Fields to update"},
            },
            "required": ["connection_id", "payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_delete_connection",
        "description": "Delete a connection by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string"},
            },
            "required": ["connection_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_test_connection",
        "description": "Test whether a connection is working.",
        "input_schema": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string"},
            },
            "required": ["connection_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_migrate_connection",
        "description": "Migrate assets from an old connector version to the latest version within a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_conn":   {"type": "string", "description": "Old connection name"},
                "target_conn":   {"type": "string", "description": "New connection name"},
                "project_name":  {"type": "string", "description": "Project to migrate (optional — all if omitted)"},
            },
            "required": ["source_conn", "target_conn"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – Connectors metadata
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_connectors",
        "description": "List all connectors available to the organisation.",
            "input_schema": {
            "type": "object",
            "properties": {
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip for pagination", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_connector_metadata",
        "description": "Get attribute metadata for a specific connector type (useful before creating a connection).",
        "input_schema": {
            "type": "object",
            "properties": {
                "connector_name": {"type": "string", "description": "Connector name, e.g. Salesforce, Oracle, SQLServer"},
            },
            "required": ["connector_name"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – Data Preview
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_data_preview",
        "description": "Preview sample rows from a source or target object via a DI connection.",
        "input_schema": {
            "type": "object",
            "properties": {
                "connection_id":  {"type": "string"},
                "object_name":    {"type": "string"},
                "direction":      {"type": "string", "enum": ["source", "target"], "default": "source"},
                "num_rows":       {"type": "integer", "default": 10},
            },
            "required": ["connection_id", "object_name"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – Mappings
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_mappings",
        "description": "List all mappings in the organisation.",
            "input_schema": {
            "type": "object",
            "properties": {
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip for pagination", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_mapping",
        "description": "Get details of a mapping by ID or name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mapping_id":   {"type": "string"},
                "mapping_name": {"type": "string"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_mapping_transformations",
        "description": "Get advanced transformation properties and sequence details for a mapping.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mapping_id":         {"type": "string"},
                "mapping_name":       {"type": "string"},
                "transformation_type": {"type": "string", "description": "Filter by transformation type, e.g. Sequence"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – Mapping Tasks
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_mapping_tasks",
        "description": "List all mapping tasks in the organisation.",
            "input_schema": {
            "type": "object",
            "properties": {
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip for pagination", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_mapping_task",
        "description": "Get details of a mapping task by ID, federated ID, or name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id":         {"type": "string"},
                "federated_id":    {"type": "string"},
                "task_name":       {"type": "string"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_mapping_task",
        "description": "Create a new mapping task based on an existing mapping.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":                  {"type": "string"},
                "description":           {"type": "string"},
                "mapping_id":            {"type": "string", "description": "ID of the mapping to base the task on"},
                "runtime_environment_id": {"type": "string"},
                "schedule_id":           {"type": "string"},
                "payload":               {"type": "object", "description": "Full mtTask payload for advanced options"},
            },
            "required": ["name", "mapping_id", "runtime_environment_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_mapping_task",
        "description": "Update an existing mapping task by task ID or federated ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id":      {"type": "string"},
                "federated_id": {"type": "string"},
                "payload":      {"type": "object", "description": "Fields to update"},
                "partial":      {"type": "boolean", "default": False, "description": "Use partial update mode"},
            },
            "required": ["payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_delete_mapping_task",
        "description": "Delete a mapping task by task ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
            },
            "required": ["task_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – Linear Taskflows
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_linear_taskflows",
        "description": "List all linear taskflows in the organisation.",
            "input_schema": {
            "type": "object",
            "properties": {
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip for pagination", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_linear_taskflow",
        "description": "Get details of a linear taskflow by ID or name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_id":   {"type": "string"},
                "workflow_name": {"type": "string"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_linear_taskflow",
        "description": "Create a new linear taskflow containing a sequence of DI tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":        {"type": "string"},
                "description": {"type": "string"},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task_id":      {"type": "string"},
                            "type":         {"type": "string", "enum": ["MTT", "DSS", "DRS", "DMASK", "PCS"]},
                            "name":         {"type": "string"},
                            "stop_on_error": {"type": "boolean", "default": False},
                        },
                        "required": ["task_id", "type", "name"],
                    },
                },
                "schedule_id":            {"type": "string"},
                "runtime_environment_id": {"type": "string"},
            },
            "required": ["name", "tasks"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_linear_taskflow",
        "description": "Update an existing linear taskflow.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string"},
                "payload":     {"type": "object", "description": "Updated workflow payload"},
            },
            "required": ["workflow_id", "payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_delete_linear_taskflow",
        "description": "Delete a linear taskflow by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string"},
            },
            "required": ["workflow_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – Published Taskflows (active-bpel)
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_taskflow_status",
        "description": "Get the execution status of a published (advanced) taskflow run.",
        "input_schema": {
            "type": "object",
            "properties": {
                "run_id":          {"type": "string"},
                "subtask_details": {"type": "boolean", "default": False},
            },
            "required": ["run_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_publish_taskflows",
        "description": "Publish one or more advanced taskflows in bulk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Paths like 'Explore/Project/Taskflow.TASKFLOW.xml'",
                },
            },
            "required": ["asset_paths"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_unpublish_taskflows",
        "description": "Unpublish one or more advanced taskflows in bulk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["asset_paths"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – Expression Validation
    # ------------------------------------------------------------------
    {
        "name": "idmc_validate_expression",
        "description": "Validate a Data Integration expression against a source object.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression":     {"type": "string"},
                "connection_id":  {"type": "string"},
                "object_name":    {"type": "string"},
                "is_source_type": {"type": "boolean", "default": True},
            },
            "required": ["expression", "connection_id", "object_name"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – Operational Insights Job Log Entries
    # ------------------------------------------------------------------
    {
        "name": "idmc_get_di_job_log_entries",
        "description": "Get completed DI job log entries from Operational Insights. Filter by status, asset type, time range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "org_id":    {"type": "string", "description": "Organisation ID"},
                "filter":    {"type": "string", "description": "OData filter, e.g. \"(endTime ge 2024-01-01T00:00:00Z)\""},
                "list_filter": {"type": "string", "description": "Status/type filter, e.g. \"status in (SUCCESS) and assetType in (MTT)\""},
                "top":       {"type": "integer", "default": 500, "description": "Max records (up to 500)"},
                "skip":      {"type": "integer", "default": 0},
            },
            "required": ["org_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – Fixed-Width Configuration
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_fwconfigs",
        "description": "List all fixed-width format configurations in the organisation.",
            "input_schema": {
            "type": "object",
            "properties": {
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip for pagination", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_fwconfig",
        "description": "Get a fixed-width format configuration by ID or name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fwconfig_id":   {"type": "string"},
                "fwconfig_name": {"type": "string"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_fwconfig",
        "description": "Create a fixed-width format configuration for flat file sources/targets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":               {"type": "string"},
                "description":        {"type": "string"},
                "line_sequential":    {"type": "boolean", "default": True},
                "pad_bytes":          {"type": "integer", "default": 0},
                "skip_rows":          {"type": "integer", "default": 0},
                "null_char":          {"type": "string", "default": ""},
                "date_format":        {"type": "string", "default": ""},
                "null_char_type":     {"type": "string", "default": "ASCII"},
                "repeat_null_char":   {"type": "boolean", "default": False},
                "strip_trailing_blank": {"type": "boolean", "default": False},
                "columns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name":       {"type": "string"},
                            "nativeType": {"type": "string", "default": "string"},
                            "precision":  {"type": "integer"},
                            "scale":      {"type": "integer", "default": 0},
                        },
                        "required": ["name", "precision"],
                    },
                },
            },
            "required": ["name", "columns"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_delete_fwconfig",
        "description": "Delete a fixed-width format configuration by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fwconfig_id": {"type": "string"},
            },
            "required": ["fwconfig_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Data Integration – PowerCenter Mapplets
    # ------------------------------------------------------------------
    {
        "name": "idmc_list_pc_mapplets",
        "description": "List all PowerCenter mapplets in the organisation.",
            "input_schema": {
            "type": "object",
            "properties": {
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip for pagination", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_pc_mapplet",
        "description": "Get details of a PowerCenter mapplet by ID or name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mapplet_id":   {"type": "string"},
                "mapplet_name": {"type": "string"},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_delete_pc_mapplet",
        "description": "Delete a PowerCenter mapplet by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mapplet_id": {"type": "string"},
            },
            "required": ["mapplet_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },

    # ------------------------------------------------------------------
    # Data Ingestion & Replication – DBMI / APPMI Tasks
    # ------------------------------------------------------------------
    {
        "name": "idmc_create_ingestion_task",
        "description": "Create a database (DBMI) or application (APPMI) ingestion and replication task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_type":              {"type": "string", "enum": ["dbmi", "appmi"], "default": "dbmi"},
                "name":                   {"type": "string"},
                "description":            {"type": "string"},
                "location":               {"type": "string", "description": "Project or project/folder path"},
                "runtime_environment":    {"type": "string"},
                "load_type":              {"type": "string", "enum": ["initial", "cdc", "combined"]},
                "source_connection":      {"type": "string"},
                "source_schema":          {"type": "string"},
                "target_connection":      {"type": "string"},
                "target_schema":          {"type": "string"},
                "selection_rules":        {"type": "array", "items": {"type": "object"}, "description": "Include/exclude table rules"},
                "advanced_options":       {"type": "object", "description": "Additional source/target/runtime options"},
            },
            "required": ["name", "load_type", "source_connection", "target_connection", "runtime_environment"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_ingestion_task_id",
        "description": "Look up an ingestion task's numeric ID by task name, project ID, or folder ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_name":   {"type": "string"},
                "project_id":  {"type": "string"},
                "folder_id":   {"type": "string"},
                "page_no":     {"type": "integer", "default": 0},
                "page_size":   {"type": "integer", "default": 25},
            },
            "required": ["task_name"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_deploy_ingestion_task",
        "description": "Deploy an ingestion task by numeric task ID. Deployment runs asynchronously.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "Numeric task ID from get_ingestion_task_id"},
            },
            "required": ["task_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_ingestion_task_details",
        "description": "Get full task definition details for ingestion tasks. Filter by taskId, projectId, or folderId.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id":    {"type": "integer"},
                "project_id": {"type": "string"},
                "folder_id":  {"type": "string"},
                "page_no":    {"type": "integer", "default": 0},
                "page_size":  {"type": "integer", "default": 25},
                "order_by":   {"type": "string", "enum": ["name", "createdTime", "lastUpdatedTime"]},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_start_ingestion_job",
        "description": "Start an ingestion job by job ID. Get the job ID first using get_ingestion_task_id + fetch job ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer"},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_stop_ingestion_job",
        "description": "Stop a running ingestion job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer"},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_resume_ingestion_job",
        "description": "Resume a stopped/failed ingestion job, optionally with schema drift resolution options.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id":         {"type": "integer"},
                "resume_options": {
                    "type": "object",
                    "description": "Schema change options, e.g. {\"schemaChangeOptions\":[{\"pattern\":\"*.*\",\"action\":\"REPLICATE\"}]}",
                },
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_undeploy_ingestion_job",
        "description": "Undeploy an ingestion job (must be in Stopped, Failed, Aborted, or Completed state).",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer"},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_ingestion_job_status",
        "description": "Get the current status of an ingestion job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer"},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_ingestion_job_metrics",
        "description": "Get detailed statistics and per-table metrics for an ingestion job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id":      {"type": "integer"},
                "state_filter": {"type": "string", "description": "Filter by table state, e.g. RUNNING, COMPLETED"},
                "sort":        {"type": "array", "items": {"type": "string"}, "default": ["srcTable", "asc"]},
                "search":      {"type": "string", "default": ""},
                "limit":       {"type": "integer", "default": 25},
                "offset":      {"type": "integer", "default": 0},
            },
            "required": ["job_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },

    # ------------------------------------------------------------------
    # Data Ingestion & Replication – File Ingestion (MI Tasks)
    # ------------------------------------------------------------------
    {
        "name": "idmc_run_mi_task_job",
        "description": "Run a file ingestion and replication (MI) task job by task ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id":    {"type": "string"},
                "task_name":  {"type": "string"},
                "parameters": {"type": "object", "description": "Optional overrides for source/target parameters"},
            },
            "required": ["task_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_mi_task_job_status",
        "description": "Get the status of a running or completed file ingestion job by run ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string"},
            },
            "required": ["run_id"],
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_get_mi_activity_log",
        "description": "Get the activity log for file ingestion and replication jobs. Filter by task ID or run ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id":           {"type": "string"},
                "run_id":            {"type": "string"},
                "offset":            {"type": "integer", "default": 0},
                "row_limit":         {"type": "integer", "default": 25},
                "job_type":          {"type": "string", "enum": ["all", "completed", "active"], "default": "all"},
                "fetch_file_events": {"type": "boolean", "default": False},
                "file_events_limit": {"type": "integer", "default": 100},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_list_mi_tasks",
        "description": "List all file ingestion and replication (MI) tasks in the organisation.",
            "input_schema": {
            "type": "object",
            "properties": {
                "limit":  {"type": "integer", "description": "Max results to return (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Number of results to skip for pagination", "default": 0},
            },
        },
        "annotations": {
            "read_only": True,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_create_mi_task",
        "description": "Create a file ingestion and replication (MI) task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":              {"type": "string"},
                "description":       {"type": "string"},
                "source_type":       {"type": "string", "enum": ["CONNECTION", "FILELISTENER"], "default": "CONNECTION"},
                "agent_group_id":    {"type": "string"},
                "source_connection": {"type": "object", "description": "Source connection {id, name, type}"},
                "target_connection": {"type": "object", "description": "Target connection {id, name, type}"},
                "source_parameters": {"type": "object", "description": "Source params (filePattern, sourceDirectory, etc.)"},
                "target_parameters": {"type": "object", "description": "Target params (targetDirectory, etc.)"},
                "file_pickup_option": {"type": "string", "enum": ["PATTERN", "FILELIST"], "default": "PATTERN"},
                "log_level":         {"type": "string", "enum": ["NORMAL", "DEBUG"], "default": "NORMAL"},
                "allow_concurrency": {"type": "boolean", "default": False},
                "location":          {"type": "object", "description": "Project/folder location {projectId, projectName}"},
            },
            "required": ["name", "agent_group_id", "source_connection", "target_connection", "source_parameters", "target_parameters"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": False,
        },
    },
    {
        "name": "idmc_update_mi_task",
        "description": "Update an existing file ingestion and replication (MI) task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "payload": {"type": "object", "description": "Fields to update"},
            },
            "required": ["task_id", "payload"],
        },
        "annotations": {
            "read_only": False,
            "destructive": False,
            "idempotent": True,
        },
    },
    {
        "name": "idmc_delete_mi_task",
        "description": "Delete a file ingestion and replication (MI) task by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
            },
            "required": ["task_id"],
        },
        "annotations": {
            "read_only": False,
            "destructive": True,
            "idempotent": True,
        },
    },
]

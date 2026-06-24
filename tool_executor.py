"""
IDMC MCP Server - Tool Executor
Maps tool names + inputs to API client calls.
"""

import base64
import hashlib
import json
import os
from typing import Any
from api_client import InformaticaAPIClient, Session, InformaticaAPIError
from credential_prompt import collect_credentials_via_dialog


def _to_base64(content: bytes, filename: str) -> dict:
    """Return binary content as base64 string with metadata."""
    return {
        "filename": filename,
        "encoding": "base64",
        "content": base64.b64encode(content).decode("ascii"),
        "size_bytes": len(content),
    }


def _build_create_profile_payload(inputs: dict) -> dict:
    """Translate flat tool inputs into the nested API payload for create_profile."""
    fields = inputs.get("fields", [])
    profileable_fields = []
    source_fields = []

    for i, f in enumerate(fields):
        source_fields.append({
            "name": f["name"],
            "dataType": f.get("dataType", "varchar"),
            "precision": f.get("precision", 255),
            "scale": f.get("scale", 0),
            "pcType": f.get("pcType", "STRING"),
            "order": f.get("order", i),
            "isDeleted": False,
            "isMetadataUpdated": False,
            "xpath": "/",
            "columnGroup": 0,
            "isLeafNode": True,
        })
        profileable_fields.append({
            "sourceName": inputs["source_name"],
            "fieldName": f["name"],
            "fieldType": "DATASOURCEFIELD",
            "isDeleted": False,
            "xpath": "/",
        })

    filters_raw = inputs.get("filters", [])
    filters = []
    for flt in filters_raw:
        filters.append({
            "isEnabled": True,
            "name": flt.get("name", "filter"),
            "description": flt.get("description", ""),
            "fieldFilters": [{
                "columnName": flt["columnName"],
                "operator": flt["operator"],
                "value": flt["value"],
            }],
            "filterType": "SIMPLE",
        })

    enable_claire = inputs.get("enable_claire", False)
    data_source_type = inputs.get("data_source_type", "UNSET")
    is_flatfile = data_source_type.upper() in ("FLATFILE", "FLAT_FILE", "DELIMITED")

    user_adv_props = inputs.get("profile_adv_props") or {}
    if user_adv_props or enable_claire:
        adv_props = dict(user_adv_props)
        adv_props["enableClaireAnomalyDetection"] = enable_claire
    else:
        adv_props = None

    schema = inputs.get("schema", "")

    if is_flatfile:
        source_properties = {
            "dataSourceType": data_source_type,
            "delimiter": ",",
            "textQualifier": "\"",
            "escapeCharacter": "",
            "sourceFileName": inputs["source_name"],
            "firstDataRow": 2,
            "headerLineNo": 1,
        }
    else:
        source_properties = {"dataSourceType": data_source_type}
        if schema:
            source_properties["sourcePath"] = schema

    source_obj: dict = {
        "name": inputs["source_name"],
        "fields": source_fields,
        "dataSourceType": data_source_type,
        "sourceType": "DATASOURCE",
        "properties": source_properties,
    }
    if not is_flatfile:
        source_obj["advancedOptions"] = {
            "Apply Custom Schema": "true" if schema else "false",
            "Schema Name": schema if schema else "",
            "Pre SQL": "",
            "Post SQL": "",
            "Sql Override": "",
            "Table Name": "",
            "Source Type": "Table",
            "Tracing Level": "Normal",
            "Output is Deterministic": "false",
            "Output is Repeatable": "",
        }

    payload: dict = {
        "name": inputs["name"],
        "description": inputs.get("description", ""),
        "connectionId": inputs["connection_id"],
        "isFilterEnabled": inputs.get("filter_enabled", False),
        "source": source_obj,
        "profileableFields": profileable_fields,
        "samplingOptions": {
            "samplingType": inputs.get("sampling_type", "ALL_ROWS"),
            "rows": inputs.get("sampling_rows", -1),
        },
        "drillDownType": "ON" if inputs.get("drill_down", True) else "OFF",
        "profileType": inputs.get("profile_type", "COLUMN_PROFILE"),
        "runtimeOptions": {
            "scheduleId": inputs.get("schedule_id"),
            "runtimeEnvironmentId": inputs.get("runtime_environment_id"),
            "defaultEmailNotification": inputs.get("default_email_notification", True),
            **({"profileAdvProps": adv_props} if adv_props is not None else {}),
        },
    }

    if inputs.get("org_id"):
        payload["orgId"] = inputs["org_id"]

    if inputs.get("frs_project_id"):
        payload["frsProjectId"] = inputs["frs_project_id"]
    if inputs.get("frs_folder_id"):
        payload["frsFolderId"] = inputs["frs_folder_id"]
    if filters:
        payload["filters"] = filters

    # Attach rules to the source object if provided
    rules_raw = inputs.get("rules", [])
    if rules_raw:
        rules = []
        for r in rules_raw:
            rule_entry = {
                "name":        r["name"],
                "description": r.get("description"),
                "frsId":       r["frsId"],
                "ruleType":    r.get("ruleType", "RULE_SPECIFICATION"),
            }
            if r.get("inFields"):
                rule_entry["inFields"] = r["inFields"]
            if r.get("outFields"):
                rule_entry["outFields"] = r["outFields"]
            rules.append(rule_entry)
        payload["source"]["rules"] = rules

    return payload


def _build_create_query_payload(inputs: dict) -> dict:
    """Translate flat tool inputs into the nested API payload for create_query."""
    queries = []
    for cond in inputs.get("conditions", []):
        queries.append({
            "columnId": cond["column_id"],
            "columnName": cond["column_name"],
            "columnType": cond["column_type"],
            "operationType": cond["operation_type"],
            "valueFunctiontype": cond["value_function"],
            "values": cond.get("values", []),
        })

    payload: dict = {
        "name": inputs["name"],
        "description": inputs.get("description", ""),
        "operator": inputs.get("operator", "AND"),
        "profileId": inputs["profile_id"],
        "queries": queries,
        "queryType": inputs["query_type"],
    }
    if inputs.get("connection_id"):
        payload["connectionId"] = inputs["connection_id"]
    return payload


def _paginate(items: list, inp: dict) -> dict:
    """Apply limit/offset pagination to a list result and return envelope."""
    if not isinstance(items, list):
        return items
    limit = inp.get("limit", 50)
    offset = inp.get("offset", 0)
    total = len(items)
    page = items[offset: offset + limit]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + limit) < total,
        "items": page,
    }


class ToolExecutor:
    """Executes tool calls by delegating to the API client."""

    def __init__(self):
        self.client = InformaticaAPIClient()
        self._lock = __import__("threading").Lock()

    def execute(self, tool_name: str, tool_input: dict) -> Any:
        """Dispatch a tool call. Returns a JSON-serialisable result."""
        try:
            return self._dispatch(tool_name, tool_input)
        except InformaticaAPIError as e:
            return {"error": str(e), "status_code": e.status_code}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def _dispatch(self, tool_name: str, inp: dict) -> Any:
        c = self.client

        # ---- Auth ----
        if tool_name == "idmc_login":
            username = os.environ.get("IDMC_USERNAME", "")
            password = os.environ.get("IDMC_PASSWORD", "")
            if not (username and password):
                try:
                    username, password = collect_credentials_via_dialog()
                except RuntimeError:
                    return {"error": "Login cancelled by user."}
                except Exception as e:
                    return {
                        "error": (
                            f"Failed to open credential dialog: {e}. "
                            "On headless systems set IDMC_USERNAME and IDMC_PASSWORD env vars."
                        )
                    }
            pod_region = inp.get("pod_region", "us")
            return c.login(username, password, pod_region)

        # ---- Connections ----
        if tool_name == "idmc_list_connections":
            return c.list_connections(
                inp.get("connection_id"),
                inp.get("connection_name"),
            )

        if tool_name == "idmc_search_connections":
            return c.search_connections(
                inp["ui_type"],
                inp.get("agent_id"),
                inp.get("runtime_environment_id"),
            )

        if tool_name == "idmc_get_connection_objects":
            return c.get_connection_objects(
                inp["connection_id"],
                inp.get("object_type", "source"),
                inp.get("search_pattern", ""),
                inp.get("max_records_count", 200),
                inp.get("metadata_only", False),
            )

        if tool_name == "idmc_get_object_fields":
            return c.get_object_fields(
                inp["connection_id"],
                inp["object_name"],
                inp.get("source_type", "oracle"),
            )

        # ---- Projects / Folders ----
        if tool_name == "idmc_list_projects":
            return _paginate(c.list_projects(inp.get("name")), inp)

        if tool_name == "idmc_create_project":
            return c.create_project(inp["name"], inp.get("description", ""))

        if tool_name == "idmc_list_folders":
            return c.list_folders(
                project_id=inp.get("project_id"),
                project_name=inp.get("project_name"),
            )

        if tool_name == "idmc_create_folder":
            return c.create_folder(
                name=inp["name"],
                description=inp.get("description", ""),
                project_id=inp.get("project_id"),
                project_name=inp.get("project_name"),
            )

        # ---- Profiles ----
        if tool_name == "idmc_list_profiles":
            return _paginate(c.list_profiles(
                name=inp.get("name"),
                exact_match=inp.get("exact_match"),
                frs_project_name=inp.get("frs_project_name"),
                frs_folder_name=inp.get("frs_folder_name"),
            ), inp)

        if tool_name == "idmc_get_profile":
            return c.get_profile(inp["profile_id"])

        if tool_name == "idmc_create_profile":
            inp = dict(inp)
            # Auto-inject orgId from session if not explicitly provided
            if not inp.get("org_id") and c.session.org_uuid:
                inp["org_id"] = c.session.org_uuid
            # Try to resolve federatedId and auto-detect data_source_type from connection metadata
            # The input connection_id may already be a federatedId — handle both cases
            try:
                conn = c.list_connections(connection_id=inp["connection_id"])
                if isinstance(conn, dict) and "federatedId" in conn:
                    inp["connection_id"] = conn["federatedId"]
                    if not inp.get("data_source_type") or inp.get("data_source_type") == "UNSET":
                        _type_map = {
                            "CSVFile": "DELIMITED",
                            "Oracle": "ORACLE",
                            "SqlServer": "SQLSERVER",
                            "PostgreSQL": "POSTGRESQL",
                            "Snowflake Data Cloud": "SNOWFLAKE",
                            "Amazon S3 v2": "S3",
                        }
                        inp["data_source_type"] = _type_map.get(conn.get("instanceDisplayName", ""), "UNSET")
            except Exception:
                pass  # connection_id is already a federatedId — use as-is
            payload = _build_create_profile_payload(inp)
            return c.create_profile(payload)

        if tool_name == "idmc_run_profile":
            return c.run_profile(inp["profile_id"])

        if tool_name == "idmc_delete_profile":
            return c.delete_profile(inp["profile_id"])

        if tool_name == "idmc_update_profile":
            # Full PUT — fetch existing profile and merge changes
            existing = c.get_profile(inp["profile_id"])
            payload: dict = {k: existing[k] for k in existing if k != "profileType"}
            payload["profileType"] = existing.get("profileType", "COLUMN_PROFILE")

            for field, api_key in [
                ("name", "name"), ("description", "description"),
                ("filter_enabled", "isFilterEnabled"), ("drill_down", "drillDownType"),
            ]:
                if inp.get(field) is not None:
                    if field == "drill_down":
                        payload["drillDownType"] = "ON" if inp[field] else "OFF"
                    else:
                        payload[api_key] = inp[field]
            if inp.get("sampling_type") or inp.get("sampling_rows") is not None:
                payload["samplingOptions"] = {
                    "samplingType": inp.get("sampling_type", "ALL_ROWS"),
                    "rows": inp.get("sampling_rows", -1),
                }
            if inp.get("enable_claire") is not None:
                payload.setdefault("runtimeOptions", {}).setdefault(
                    "profileAdvProps", {})["enableClaireAnomalyDetection"] = inp["enable_claire"]
            if inp.get("filters"):
                payload["filters"] = [
                    {"isEnabled": True, "name": f.get("name", "filter"),
                     "description": f.get("description", ""),
                     "fieldFilters": [{"columnName": f["columnName"],
                                       "operator": f["operator"], "value": f["value"]}],
                     "filterType": "SIMPLE"}
                    for f in inp["filters"]
                ]
            if inp.get("fields"):
                payload["source"]["fields"] = [
                    {"name": fld["name"], "dataType": fld.get("dataType", "varchar"),
                     "precision": fld.get("precision", 255), "scale": fld.get("scale", 0),
                     "pcType": fld.get("pcType", "STRING")}
                    for fld in inp["fields"]
                ]
            # Remove rule specs by frsId (from both source.rules and profileableFields)
            if inp.get("remove_rule_spec_frs_ids"):
                remove_set = set(inp["remove_rule_spec_frs_ids"])
                payload["source"]["rules"] = [
                    r for r in payload["source"].get("rules", [])
                    if r.get("frsId") not in remove_set
                ]
                payload["profileableFields"] = [
                    f for f in payload["profileableFields"]
                    if f.get("frsId") not in remove_set
                ]
            # Remove plain datasource columns
            if inp.get("remove_columns"):
                remove_cols = set(inp["remove_columns"])
                payload["profileableFields"] = [
                    f for f in payload["profileableFields"]
                    if not (f.get("fieldType") == "DATASOURCEFIELD" and f.get("fieldName") in remove_cols)
                ]
            # Add plain datasource columns
            if inp.get("add_columns"):
                existing_col_names = {f.get("fieldName") for f in payload["profileableFields"]}
                source_fields = {sf["name"]: sf for sf in payload["source"].get("fields", [])}
                for col_name in inp["add_columns"]:
                    if col_name not in existing_col_names:
                        sf = source_fields.get(col_name, {})
                        payload["profileableFields"].append({
                            "fieldName": col_name,
                            "sourceName": payload["source"].get("name", ""),
                            "precision": sf.get("precision", 255),
                            "scale": sf.get("scale", 0),
                            "fieldType": "DATASOURCEFIELD",
                            "isDeleted": False,
                        })
            # Add rule specifications — updates both source.rules and profileableFields (MAPPLETFIELD)
            if inp.get("add_rule_specs"):
                existing_rule_frs_ids = {r.get("frsId") for r in payload["source"].get("rules", [])}
                payload["source"].setdefault("rules", [])
                for rspec in inp["add_rule_specs"]:
                    frs_id = rspec["frsId"]
                    in_fields = rspec.get("inputFields", [])
                    out_fields = rspec.get("outputFields", [])
                    # Add to source.rules if not already present
                    if frs_id not in existing_rule_frs_ids:
                        rule_name = rspec.get("name") or frs_id
                        payload["source"]["rules"].append({
                            "frsId": frs_id,
                            "ruleType": "RULE_SPECIFICATION",
                            "name": rule_name,
                            "description": rspec.get("description", None),
                            "isDeleted": False,
                            "inFields": [{"name": f["inFieldName"], "dataType": "string",
                                          "precision": 50, "scale": 0, "isDeleted": False}
                                         for f in in_fields],
                            "outFields": [{"name": f["outFieldName"], "dataType": "string",
                                           "precision": 100, "scale": 0, "isDeleted": False}
                                          for f in out_fields],
                        })
                    # Add MAPPLETFIELD to profileableFields
                    import hashlib as _hl
                    _id_src = frs_id + "".join(f["inFieldName"] for f in in_fields)
                    assignment_id = _hl.md5(_id_src.encode()).hexdigest()
                    payload["profileableFields"].append({
                        "frsId": frs_id,
                        "assignmentIdentifier": assignment_id,
                        "fieldType": "MAPPLETFIELD",
                        "ruleType": "RULE_SPECIFICATION",
                        "isDeleted": False,
                        "appliedBy": "USER",
                        "inputFieldMappings": [{"inFieldName": f["inFieldName"],
                                                "dataSourceFieldName": f["dataSourceFieldName"],
                                                "isDeleted": False}
                                               for f in in_fields],
                        "outputFieldMappings": [{"outFieldName": f["outFieldName"],
                                                 "isDeleted": False}
                                                for f in out_fields],
                    })
            return c.update_profile(inp["profile_id"], payload)

        if tool_name == "idmc_suggest_profile_name":
            name = c.suggest_profile_name(
                inp.get("frs_project_name"), inp.get("frs_folder_name")
            )
            return {"suggested_name": name}

        if tool_name == "idmc_get_last_successful_run_key":
            payload = {}
            for key, api_key in [
                ("profile_id", "profileId"), ("profile_name", "profileName"),
                ("frs_project_name", "frsProjectName"), ("frs_folder_name", "frsFolderName"),
            ]:
                if inp.get(key):
                    payload[api_key] = inp[key]
            return c.get_last_successful_run_key(payload)

        if tool_name == "idmc_get_rule_spec_ports":
            return c.get_rule_spec_ports(inp["frs_id"])

        if tool_name == "idmc_get_rule_ids":
            payload = {}
            for key, api_key in [
                ("profile_id", "profileId"), ("profile_name", "profileName"),
                ("frs_project_name", "frsProjectName"), ("frs_folder_name", "frsFolderName"),
                ("rule_name", "ruleName"), ("column_id", "columnId"),
                ("column_name", "columnName"), ("rule_project", "ruleProject"),
                ("rule_folder", "ruleFolder"), ("frs_rule_id", "frsRuleId"),
            ]:
                if inp.get(key):
                    payload[api_key] = inp[key]
            return c.get_rule_ids(payload)

        # ---- Jobs ----
        if tool_name == "idmc_get_job":
            return c.get_job(inp["job_id"])

        if tool_name == "idmc_get_running_jobs":
            return c.get_running_jobs(inp["profile_id"])

        if tool_name == "idmc_stop_job":
            return c.stop_job(
                inp["job_id"], inp.get("job_step_id"), inp.get("job_type")
            )

        if tool_name == "idmc_resume_job":
            return c.resume_job(
                inp["job_id"], inp.get("job_step_id"), inp.get("job_type")
            )

        if tool_name == "idmc_get_session_logs":
            return {"logs": c.get_session_logs(inp["job_step_id"])}

        # ---- Results ----
        if tool_name == "idmc_list_columns":
            return c.list_columns(inp["profile_id"])

        if tool_name == "idmc_get_column":
            return c.get_column(inp["profile_id"], inp["column_id"], inp.get("run_key"))

        if tool_name == "idmc_get_column_patterns":
            return c.get_column_patterns(inp["profile_id"], inp["column_id"])

        if tool_name == "idmc_get_column_datatypes":
            return c.get_column_datatypes(inp["profile_id"], inp["column_id"])

        if tool_name == "idmc_get_value_frequencies":
            return c.get_value_frequencies(inp["profile_id"], inp["column_id"])

        if tool_name == "idmc_export_profile_results":
            content = c.export_profile_results(
                inp["profile_id"],
                profile_name=inp.get("profile_name", "profile_results"),
                run_key=inp.get("run_key", 1),
                range_type=inp.get("range_type", "ALL_COLUMNS"),
                column_ids=inp.get("column_ids"),
                file_format=inp.get("file_format", "EXCEL"),
                scopes=inp.get("scopes"),
                code_page=inp.get("code_page", "ASCII"),
            )
            return _to_base64(content, "profile_results.xlsx")

        # ---- Run Details ----
        if tool_name == "idmc_list_run_details":
            return c.list_run_details(inp["profile_id"])

        if tool_name == "idmc_get_run_detail":
            return c.get_run_detail(inp["run_detail_id"])

        if tool_name == "idmc_delete_run_details":
            return c.delete_run_details(inp["profile_id"], inp["run_detail_ids"])

        if tool_name == "idmc_get_top_n_runs":
            return c.get_top_n_runs(inp.get("limit", 10))

        if tool_name == "idmc_get_top_n_profile_tasks":
            return c.get_top_n_profile_tasks(inp.get("limit", 10))

        # ---- Queries ----
        if tool_name == "idmc_create_query":
            payload = _build_create_query_payload(inp)
            return c.create_query(payload)

        if tool_name == "idmc_execute_query":
            return c.execute_query(inp["query_id"])

        if tool_name == "idmc_get_query_results":
            return c.get_query_results(inp["query_id"])

        if tool_name == "idmc_list_queries":
            return c.list_queries(inp["profile_id"])

        if tool_name == "idmc_delete_query":
            return c.delete_query(inp["query_id"])

        if tool_name == "idmc_get_query":
            return c.get_query(inp["query_id"])

        if tool_name == "idmc_update_query":
            payload: dict = {}
            for field in ("name", "description", "operator", "query_type"):
                if inp.get(field) is not None:
                    key = "queryType" if field == "query_type" else field
                    payload[key] = inp[field]
            if inp.get("conditions"):
                payload["queries"] = [
                    {"columnId": cond["column_id"], "columnName": cond["column_name"],
                     "columnType": cond["column_type"], "operationType": cond["operation_type"],
                     "valueFunctiontype": cond["value_function"],
                     "values": cond.get("values", [])}
                    for cond in inp["conditions"]
                ]
            return c.update_query(inp["query_id"], payload)

        # ---- CLAIRE Insights ----
        if tool_name == "idmc_get_insights":
            return c.get_insights(inp["profile_id"])

        if tool_name == "idmc_update_insights":
            curated = [
                {
                    "insightId": item["insight_id"],
                    "columnKey": item["column_key"],
                    "confirmationStatus": item["confirmation_status"],
                }
                for item in inp["curated_insights"]
            ]
            return c.update_insights(inp["profile_id"], curated)

        # ---- Admin – Activity Logs ----
        if tool_name == "idmc_get_activity_log":
            return c.get_activity_log(
                log_id=inp.get("log_id"),
                task_id=inp.get("task_id"),
                run_id=inp.get("run_id"),
                offset=inp.get("offset"),
                row_limit=inp.get("row_limit"),
            )

        if tool_name == "idmc_get_activity_monitor":
            return c.get_activity_monitor()

        if tool_name == "idmc_get_error_log":
            return {"log": c.get_error_log(inp["log_id"])}

        # ---- Admin – Audit Logs ----
        if tool_name == "idmc_get_audit_log":
            return c.get_audit_log(
                batch_id=inp.get("batch_id", 0),
                batch_size=inp.get("batch_size", 200),
            )

        # ---- Admin – Users ----
        if tool_name == "idmc_get_users":
            return c.get_users(
                query=inp.get("query"),
                limit=inp.get("limit", 100),
                skip=inp.get("offset", 0),
            )

        if tool_name == "idmc_get_user":
            return c.get_user(inp["user_id"])

        if tool_name == "idmc_create_user":
            payload: dict = {
                "name":      inp["name"],
                "firstName": inp["first_name"],
                "lastName":  inp["last_name"],
                "email":     inp["email"],
            }
            for src, dst in (
                ("password",             "password"),
                ("title",                "title"),
                ("phone",                "phone"),
                ("timezone",             "timezone"),
                ("description",          "description"),
                ("authentication",       "authentication"),
                ("force_password_change","forcePasswordChange"),
                ("max_login_attempts",   "maxLoginAttempts"),
            ):
                if inp.get(src) is not None:
                    payload[dst] = inp[src]
            # v3 expects arrays of ID strings, not name-objects
            if inp.get("roles"):
                payload["roles"] = inp["roles"]
            if inp.get("groups"):
                payload["groups"] = inp["groups"]
            return c.create_user(payload)

        if tool_name == "idmc_add_user_roles":
            return c.update_user_roles(inp["user_id"], inp["roles"], "addRoles")

        if tool_name == "idmc_remove_user_roles":
            return c.update_user_roles(inp["user_id"], inp["roles"], "removeRoles")

        if tool_name == "idmc_add_user_groups":
            return c.update_user_groups(inp["user_id"], inp["groups"], "addGroups")

        if tool_name == "idmc_remove_user_groups":
            return c.update_user_groups(inp["user_id"], inp["groups"], "removeGroups")

        if tool_name == "idmc_delete_user":
            return c.delete_user(inp["user_id"])

        if tool_name == "idmc_change_password":
            old_pw = inp.get("old_password") or os.environ.get("IDMC_OLD_PASSWORD", "")
            new_pw = inp.get("new_password") or os.environ.get("IDMC_NEW_PASSWORD", "")
            if not old_pw or not new_pw:
                return {"error": "Passwords required. Pass old_password/new_password or set IDMC_OLD_PASSWORD/IDMC_NEW_PASSWORD env vars."}
            return c.change_password(old_pw, new_pw)

        # ---- Admin – Roles ----
        if tool_name == "idmc_get_roles":
            return c.get_roles(
                query=inp.get("query"),
                expand=inp.get("expand"),
                limit=inp.get("limit"),
                skip=inp.get("offset"),
            )

        if tool_name == "idmc_get_privileges":
            return c.get_privileges(query=inp.get("query"))

        if tool_name == "idmc_create_role":
            return c.create_role(inp["name"], inp.get("description", ""), inp["privileges"])

        if tool_name == "idmc_add_role_privileges":
            return c.update_role_privileges(
                inp["privileges"], "addPrivileges",
                role_id=inp.get("role_id"),
                role_name=inp.get("role_name"),
            )

        if tool_name == "idmc_remove_role_privileges":
            return c.update_role_privileges(
                inp["privileges"], "removePrivileges",
                role_id=inp.get("role_id"),
                role_name=inp.get("role_name"),
            )

        if tool_name == "idmc_delete_role":
            return c.delete_role(
                role_id=inp.get("role_id"),
                role_name=inp.get("role_name"),
            )

        # ---- Admin – User Groups ----
        if tool_name == "idmc_get_user_groups":
            return c.get_user_groups(
                query=inp.get("query"),
                limit=inp.get("limit"),
                skip=inp.get("offset"),
            )

        if tool_name == "idmc_get_user_group":
            return c.get_user_group(
                group_id=inp.get("group_id"),
                group_name=inp.get("group_name"),
            )

        if tool_name == "idmc_create_user_group":
            return c.create_user_group(
                inp["name"],
                inp.get("description", ""),
                inp.get("roles"),
                inp.get("users"),
            )

        if tool_name == "idmc_add_users_to_group":
            return c.update_user_group(
                inp["users"], "addUsers",
                group_id=inp.get("group_id"),
                group_name=inp.get("group_name"),
            )

        if tool_name == "idmc_remove_users_from_group":
            return c.update_user_group(
                inp["users"], "removeUsers",
                group_id=inp.get("group_id"),
                group_name=inp.get("group_name"),
            )

        if tool_name == "idmc_add_roles_to_group":
            return c.update_user_group_roles(
                inp["roles"], "addRoles",
                group_id=inp.get("group_id"),
                group_name=inp.get("group_name"),
            )

        if tool_name == "idmc_remove_roles_from_group":
            return c.update_user_group_roles(
                inp["roles"], "removeRoles",
                group_id=inp.get("group_id"),
                group_name=inp.get("group_name"),
            )

        if tool_name == "idmc_delete_user_group":
            return c.delete_user_group(
                group_id=inp.get("group_id"),
                group_name=inp.get("group_name"),
            )

        # ---- Admin – Schedules ----
        if tool_name == "idmc_get_schedules":
            return c.get_schedules(inp.get("query"), inp.get("schedule_id"))

        if tool_name == "idmc_create_schedule":
            payload = {
                "name": inp["name"],
                "description": inp.get("description", ""),
                "status": inp.get("status", "Enabled"),
                "startTime": inp["start_time"],
                "interval": inp.get("interval", "Daily"),
                "frequency": inp.get("frequency", 1),
            }
            if inp.get("end_time"):
                payload["endTime"] = inp["end_time"]
            if inp.get("timezone"):
                payload["timezone"] = inp["timezone"]
            return c.create_schedule(payload)

        if tool_name == "idmc_update_schedule":
            return c.update_schedule(inp["schedule_id"], inp["payload"])

        if tool_name == "idmc_delete_schedule":
            return c.delete_schedule(inp["schedule_id"])

        # ---- Admin – Runtime Environments & Secure Agents ----
        if tool_name == "idmc_get_runtime_environments":
            return c.get_runtime_environments(inp.get("env_id"), inp.get("env_name"))

        if tool_name == "idmc_get_secure_agents":
            return c.get_secure_agents(
                agent_id=inp.get("agent_id"),
                agent_name=inp.get("agent_name"),
                include_unassigned_only=inp.get("include_unassigned_only", False),
                basic_info=inp.get("basic_info", False),
                include_service_details=inp.get("include_service_details", False),
                only_status=inp.get("only_status", True),
            )

        # ---- Admin – Organisation ----
        if tool_name == "idmc_get_organization":
            return c.get_organization()

        # ---- Admin – Licenses ----
        if tool_name == "idmc_get_license":
            return c.get_license()

        # ---- Admin – Object Permissions ----
        if tool_name == "idmc_get_object_permissions":
            return c.get_object_permissions(inp["object_id"], inp.get("acl_id"))

        if tool_name == "idmc_create_object_permission":
            return c.create_object_permission(
                object_id=inp["object_id"],
                principal_type=inp["principal_type"],
                principal_name=inp["principal_name"],
                read=inp["read"],
                update=inp["update"],
                delete=inp["delete"],
                execute=inp["execute"],
                change_permission=inp["change_permission"],
            )

        if tool_name == "idmc_delete_object_permission":
            return c.delete_object_permission(inp["object_id"], inp.get("acl_id"))

        # ---- Admin – DI Jobs ----
        if tool_name == "idmc_start_di_job":
            payload = {"taskType": inp["task_type"]}
            if inp.get("task_id"):
                payload["taskId"] = inp["task_id"]
            if inp.get("task_federated_id"):
                payload["taskFederatedId"] = inp["task_federated_id"]
            if inp.get("task_name"):
                payload["taskName"] = inp["task_name"]
            if inp.get("callback_url"):
                payload["callbackURL"] = inp["callback_url"]
            if inp.get("parameter_file_name") or inp.get("parameter_file_dir"):
                payload["runtime"] = {
                    "@type": "mtTaskRuntime",
                    "parameterFileName": inp.get("parameter_file_name", ""),
                    "parameterFileDir": inp.get("parameter_file_dir", ""),
                }
            return c.start_di_job(payload)

        if tool_name == "idmc_stop_di_job":
            payload = {"taskType": inp["task_type"]}
            if inp.get("task_id"):
                payload["taskId"] = inp["task_id"]
            if inp.get("task_federated_id"):
                payload["taskFederatedId"] = inp["task_federated_id"]
            if inp.get("task_name"):
                payload["taskName"] = inp["task_name"]
            return c.stop_di_job(payload, inp.get("clean_stop", False))

        # ---- Admin – Server Time & Logout ----
        if tool_name == "idmc_get_server_time":
            return c.get_server_time()

        if tool_name == "idmc_logout":
            return c.logout()

        # ---- Platform v2 – Tasks ----
        if tool_name == "idmc_get_di_tasks":
            return c.get_di_tasks(inp["task_type"])

        # ---- Platform v2 – Bundles ----
        if tool_name == "idmc_get_bundle":
            return c.get_bundle(
                bundle_id=inp.get("bundle_id"),
                bundle_name=inp.get("bundle_name"),
                installed=inp.get("installed"),
                published=inp.get("published"),
            )

        if tool_name == "idmc_install_bundle":
            return c.install_bundle(inp["bundle_object_id"])

        if tool_name == "idmc_uninstall_bundle":
            return c.uninstall_bundle(
                inp["bundle_object_id"],
                inp.get("update_option", "EXCEPTION_IF_IS_USED"),
            )

        # ---- Platform v2 – Organisation management ----
        if tool_name == "idmc_get_organization_details":
            return c.get_organization_details(
                org_id=inp.get("org_id"), org_name=inp.get("org_name")
            )

        if tool_name == "idmc_update_organization":
            return c.update_organization(inp["payload"], org_id=inp.get("org_id"))

        if tool_name == "idmc_delete_sub_organization":
            return c.delete_sub_organization(inp["org_id"])

        if tool_name == "idmc_create_sub_organization":
            org_obj: dict = {
                "@type":     "org",
                "name":      inp["org_name"],
                "address1":  inp["org_address"],
                "city":      inp["org_city"],
                "country":   inp["org_country"],
                "employees": inp["org_employees"],
            }
            if inp.get("org_address2"):    org_obj["address2"]  = inp["org_address2"]
            if inp.get("org_address3"):    org_obj["address3"]  = inp["org_address3"]
            if inp.get("org_state"):       org_obj["state"]     = inp["org_state"]
            if inp.get("org_zipcode"):     org_obj["zipcode"]   = inp["org_zipcode"]
            if inp.get("org_timezone"):    org_obj["timezone"]  = inp["org_timezone"]
            if inp.get("org_offer_code"):  org_obj["offerCode"] = inp["org_offer_code"]

            user_obj: dict = {
                "@type":     "user",
                "name":      inp["admin_username"],
                "password":  inp["admin_password"],
                "firstName": inp["admin_first_name"],
                "lastName":  inp["admin_last_name"],
                "title":     inp["admin_title"],
                "phone":     inp["admin_phone"],
                "emails":    inp["admin_email"],
            }
            if inp.get("admin_timezone"):          user_obj["timezone"]            = inp["admin_timezone"]
            if inp.get("admin_security_question"): user_obj["securityQuestion"]    = inp["admin_security_question"]
            if inp.get("admin_security_answer"):   user_obj["securityAnswer"]      = inp["admin_security_answer"]
            if inp.get("admin_force_change_password") is not None:
                user_obj["forceChangePassword"] = inp["admin_force_change_password"]
            if inp.get("admin_opt_out_of_emails") is not None:
                user_obj["optOutOfEmails"] = inp["admin_opt_out_of_emails"]

            payload = {
                "@type":    "registration",
                "org":      org_obj,
                "user":     user_obj,
                "sendEmail": inp.get("send_email", True),
            }
            if inp.get("registration_code"):
                payload["registrationCode"] = inp["registration_code"]
            return c.create_sub_organization(payload)

        # ---- Platform v2 – Secure Agent management ----
        if tool_name == "idmc_delete_secure_agent":
            return c.delete_secure_agent(inp["agent_id"])

        if tool_name == "idmc_get_agent_installer_info":
            return c.get_agent_installer_info(inp.get("platform", "linux64"))

        # ---- Platform v2 – Runtime Environment management ----
        if tool_name == "idmc_create_runtime_environment":
            return c.create_runtime_environment(inp["name"], inp.get("is_shared", False))

        if tool_name == "idmc_update_runtime_environment":
            payload = {"@type": "runtimeEnvironment", "name": inp["name"]}
            if inp.get("is_shared") is not None:
                payload["isShared"] = inp["is_shared"]
            if inp.get("agents"):
                payload["agents"] = [
                    {"@type": "agent", "id": a["id"], "orgId": a.get("orgId", "")}
                    for a in inp["agents"]
                ]
            return c.update_runtime_environment(inp["env_id"], payload)

        if tool_name == "idmc_delete_runtime_environment":
            return c.delete_runtime_environment(inp["env_id"])

        if tool_name == "idmc_get_runtime_environment_selections":
            return c.get_runtime_environment_selections(
                inp["env_id"], inp.get("details", False)
            )

        if tool_name == "idmc_update_runtime_environment_selections":
            return c.update_runtime_environment_selections(inp["env_id"], inp["payload"])

        if tool_name == "idmc_get_runtime_environment_configs":
            return c.get_runtime_environment_configs(
                inp["env_id"],
                inp.get("platform", "linux64"),
                inp.get("details", False),
            )

        if tool_name == "idmc_update_runtime_environment_configs":
            return c.update_runtime_environment_configs(
                inp["env_id"],
                inp.get("platform", "linux64"),
                inp["payload"],
            )

        if tool_name == "idmc_delete_runtime_environment_configs":
            return c.delete_runtime_environment_configs(inp["env_id"])

        # ---- Platform v2 – Session logs & validation ----
        if tool_name == "idmc_get_session_log":
            content = c.get_session_log(
                inp["log_id"],
                item_id=inp.get("item_id"),
                child_item_id=inp.get("child_item_id"),
            )
            return _to_base64(content, "session_log.zip")

        if tool_name == "idmc_validate_session":
            return c.validate_session(inp["username"])

        if tool_name == "idmc_logout_all_sessions":
            return c.logout_all_sessions(inp["username"], inp["password"])

        # ---- Platform v3 – Lookup & Objects ----
        if tool_name == "idmc_lookup_object":
            raw = inp["objects"]
            objects = []
            for o in raw:
                obj: dict = {}
                if o.get("id"):
                    obj["id"] = o["id"]
                else:
                    obj["path"] = o["path"]
                    obj["type"] = o["type"]
                objects.append(obj)
            return c.lookup_object(objects)

        if tool_name == "idmc_list_project_assets":
            return c.list_project_assets_recursive(inp["project_name"])

        if tool_name == "idmc_list_assets":
            return c.list_assets(
                query=inp.get("query"),
                limit=inp.get("limit", 200),
                skip=inp.get("skip", 0),
            )

        if tool_name == "idmc_get_asset_dependencies":
            return c.get_asset_dependencies(
                inp["object_id"],
                ref_type=inp.get("ref_type", "uses"),
                limit=inp.get("limit", 25),
                skip=inp.get("skip", 0),
            )

        # ---- Platform v3 – Passwords ----
        if tool_name == "idmc_reset_password":
            return c.reset_password(
                inp["user_id"], inp["security_answer"], inp["new_password"]
            )

        # ---- Platform v3 – Object Permissions (update + check) ----
        if tool_name == "idmc_update_object_permission":
            return c.update_object_permission(
                object_id=inp["object_id"],
                acl_id=inp["acl_id"],
                principal_type=inp["principal_type"],
                principal_name=inp["principal_name"],
                read=inp["read"],
                update=inp["update"],
                delete=inp["delete"],
                execute=inp["execute"],
                change_permission=inp["change_permission"],
            )

        if tool_name == "idmc_check_object_access":
            return c.check_object_access(inp["object_id"], inp.get("asset_type"))

        # ---- Platform v3 – Projects & Folders (update/delete) ----
        if tool_name == "idmc_update_project":
            return c.update_project(
                name=inp.get("name"),
                description=inp.get("description"),
                project_id=inp.get("project_id"),
                project_name=inp.get("project_name"),
            )

        if tool_name == "idmc_delete_project":
            return c.delete_project(
                project_id=inp.get("project_id"), project_name=inp.get("project_name")
            )

        if tool_name == "idmc_update_folder":
            return c.update_folder(
                folder_id=inp.get("folder_id"),
                folder_name=inp.get("folder_name"),
                name=inp.get("name"),
                description=inp.get("description"),
                project_id=inp.get("project_id"),
                project_name=inp.get("project_name"),
            )

        if tool_name == "idmc_delete_folder":
            return c.delete_folder(
                folder_id=inp.get("folder_id"),
                folder_name=inp.get("folder_name"),
                project_id=inp.get("project_id"),
                project_name=inp.get("project_name"),
            )

        # ---- Platform v3 – Export / Import ----
        if tool_name == "idmc_start_export_job":
            objects = [
                {"id": o["id"], "includeDependencies": o.get("include_dependencies", True)}
                for o in inp["objects"]
            ]
            return c.start_export_job(inp.get("name"), objects)

        if tool_name == "idmc_get_export_job_status":
            return c.get_export_job_status(
                inp["export_id"], inp.get("expand_objects", False)
            )

        if tool_name == "idmc_download_export_package":
            content = c.download_export_package(inp["export_id"])
            return _to_base64(content, "export_package.zip")

        if tool_name == "idmc_upload_import_package":
            return c.upload_import_package(inp["file_path"])

        if tool_name == "idmc_start_import_job":
            return c.start_import_job(
                import_job_id=inp["import_job_id"],
                name=inp.get("name"),
                default_conflict_resolution=inp.get("default_conflict_resolution", "REUSE"),
                include_objects=inp.get("include_objects"),
            )

        if tool_name == "idmc_get_import_job_status":
            return c.get_import_job_status(
                inp["import_id"], inp.get("expand_objects", False)
            )

        # ---- Platform v3 – Security Logs ----
        if tool_name == "idmc_get_security_logs":
            return c.get_security_logs(
                query=inp.get("query"),
                limit=inp.get("limit", 200),
                skip=inp.get("skip", 0),
            )

        # ---- Platform v3 – IP Addresses ----
        if tool_name == "idmc_get_trusted_ips":
            return c.get_trusted_ips(inp["org_id"])

        if tool_name == "idmc_update_trusted_ips":
            return c.update_trusted_ips(
                org_id=inp["org_id"],
                enable_ip=inp.get("enable_ip"),
                ip_ranges=inp.get("ip_ranges"),
            )

        # ---- Platform v3 – Key Rotation ----
        if tool_name == "idmc_get_key_rotation_settings":
            return c.get_key_rotation_settings()

        if tool_name == "idmc_update_key_rotation_settings":
            return c.update_key_rotation_settings(inp["rotation_interval"])

        # ---- Platform v3 – Sub-org License ----
        if tool_name == "idmc_update_sub_org_license":
            return c.update_sub_org_license(inp["org_id"], inp["payload"])

        # ---- Platform v3 – Metering Data ----
        if tool_name == "idmc_start_metering_export":
            return c.start_metering_export(
                start_date=inp["start_date"],
                end_date=inp["end_date"],
                job_type=inp.get("job_type", "SUMMARY"),
                all_linked_orgs=inp.get("all_linked_orgs", False),
                callback_url=inp.get("callback_url"),
            )

        if tool_name == "idmc_get_metering_export_status":
            return c.get_metering_export_status(inp["job_id"])

        if tool_name == "idmc_download_metering_data":
            content = c.download_metering_data(inp["job_id"])
            return _to_base64(content, "metering_data.zip")

        # ---- Platform v3 – fetchState / loadState ----
        if tool_name == "idmc_start_fetch_state":
            objects = [
                {"id": o["id"], "includeDependencies": o.get("include_dependencies", True)}
                for o in inp["objects"]
            ]
            return c.start_fetch_state(inp.get("name"), objects)

        if tool_name == "idmc_get_fetch_state_status":
            return c.get_fetch_state_status(inp["job_id"], inp.get("expand_objects", False))

        if tool_name == "idmc_download_object_states":
            content = c.download_object_states(inp["job_id"])
            return _to_base64(content, "object_states.zip")

        if tool_name == "idmc_upload_load_state_package":
            return c.upload_load_state_package(inp["file_path"])

        if tool_name == "idmc_start_load_state":
            return c.start_load_state(
                load_job_id=inp["load_job_id"],
                name=inp.get("name"),
                include_objects=inp.get("include_objects"),
            )

        if tool_name == "idmc_get_load_state_status":
            return c.get_load_state_status(inp["job_id"], inp.get("expand_objects", False))

        # ---- Platform v3 – SAML Mappings ----
        if tool_name == "idmc_get_saml_group_mappings":
            return c.get_saml_group_mappings(inp["org_id"], inp.get("query"))

        if tool_name == "idmc_get_saml_role_mappings":
            return c.get_saml_role_mappings(inp["org_id"], inp.get("query"))

        if tool_name == "idmc_add_saml_group_mappings":
            return c.add_saml_group_mappings(
                inp["org_id"], inp["group_mappings"], inp.get("reuse_group", False)
            )

        if tool_name == "idmc_add_saml_role_mappings":
            return c.add_saml_role_mappings(inp["org_id"], inp["role_mappings"])

        if tool_name == "idmc_remove_saml_group_mappings":
            return c.remove_saml_group_mappings(inp["org_id"], inp["group_mappings"])

        if tool_name == "idmc_remove_saml_role_mappings":
            return c.remove_saml_role_mappings(inp["org_id"], inp["role_mappings"])

        # ---- Platform v3 – Identity Providers ----
        if tool_name == "idmc_register_identity_provider":
            return c.register_identity_provider(
                org_id=inp["org_id"],
                issuer_url=inp["issuer_url"],
                keys_url=inp["keys_url"],
                token_claim=inp.get("token_claim", "sub"),
                match_type=inp.get("match_type", "uid"),
                signing_algorithm=inp.get("signing_algorithm", "RS256"),
            )

        if tool_name == "idmc_get_identity_providers":
            return c.get_identity_providers(inp["org_id"])

        if tool_name == "idmc_update_identity_provider":
            payload: dict = {}
            for field in ("issuer_url", "keys_url", "token_claim", "match_type", "signing_algorithm"):
                if inp.get(field):
                    key_map = {
                        "issuer_url": "endPoints.issuer",
                        "keys_url": "endPoints.keys",
                        "token_claim": "tokenClaim",
                        "match_type": "matchType",
                        "signing_algorithm": "signingAlgorithm",
                    }
                    payload[key_map[field]] = inp[field]
            api_payload: dict = {}
            if "endPoints.issuer" in payload or "endPoints.keys" in payload:
                api_payload["endPoints"] = {
                    "issuer": payload.get("endPoints.issuer", ""),
                    "keys": payload.get("endPoints.keys", ""),
                }
            if "tokenClaim" in payload or "matchType" in payload:
                api_payload["accountPolicy"] = {
                    "link": {
                        "tokenClaim": payload.get("tokenClaim", "sub"),
                        "matchType": payload.get("matchType", "uid"),
                    }
                }
            if "signingAlgorithm" in payload:
                api_payload["signingAlgorithm"] = payload["signingAlgorithm"]
            return c.update_identity_provider(inp["org_id"], inp["idp_id"], api_payload)

        if tool_name == "idmc_delete_identity_provider":
            return c.delete_identity_provider(inp["org_id"], inp["idp_id"])

        # ---- Platform v3 – SCIM Tokens ----
        if tool_name == "idmc_list_scim_tokens":
            return c.list_scim_tokens()

        if tool_name == "idmc_create_scim_token":
            return c.create_scim_token()

        if tool_name == "idmc_delete_scim_token":
            return c.delete_scim_token(inp["token_id"])

        # ---- Platform v3 – Secure Agent Service ----
        if tool_name == "idmc_manage_secure_agent_service":
            return c.manage_secure_agent_service(
                inp["agent_id"], inp["service_name"], inp["service_action"]
            )

        # ---- Platform v3 – Tags ----
        if tool_name == "idmc_assign_tags":
            return c.assign_tags(inp["tag_assignments"])

        if tool_name == "idmc_remove_asset_tags":
            return c.remove_asset_tags(inp["tag_removals"])

        # ---- Platform v3 – Source Control ----
        if tool_name == "idmc_pull_objects":
            objects = []
            for o in inp["objects"]:
                obj: dict = {}
                if o.get("id"):
                    obj["id"] = o["id"]
                else:
                    obj["path"] = o["path"]
                    if o.get("type"):
                        obj["type"] = o["type"]
                objects.append(obj)
            return c.pull_objects(inp["commit_hash"], objects)

        if tool_name == "idmc_checkout_objects":
            objects = []
            for o in inp["objects"]:
                obj: dict = {}
                if o.get("id"):
                    obj["id"] = o["id"]
                else:
                    obj["path"] = o["path"]
                    obj["type"] = o["type"]
                if o.get("include_container_assets") is not None:
                    obj["includeContainerAssets"] = o["include_container_assets"]
                objects.append(obj)
            return c.checkout_objects(objects)

        if tool_name == "idmc_checkin_objects":
            objects = []
            for o in inp["objects"]:
                obj: dict = {}
                if o.get("id"):
                    obj["id"] = o["id"]
                else:
                    obj["path"] = o["path"]
                    obj["type"] = o["type"]
                if o.get("include_container_assets") is not None:
                    obj["includeContainerAssets"] = o["include_container_assets"]
                objects.append(obj)
            return c.checkin_objects(objects, inp["summary"], inp.get("description", ""))

        if tool_name == "idmc_undo_checkout":
            objects = []
            for o in inp.get("objects", []):
                obj: dict = {}
                if o.get("id"):
                    obj["id"] = o["id"]
                else:
                    obj["path"] = o["path"]
                    obj["type"] = o["type"]
                objects.append(obj)
            return c.undo_checkout(
                objects=objects or None,
                checkout_operation_id=inp.get("checkout_operation_id"),
            )

        if tool_name == "idmc_compare_object_versions":
            return c.compare_object_versions(
                asset_id=inp["asset_id"],
                source=inp["source"],
                destination=inp["destination"],
                output_format=inp.get("output_format", "JSON"),
            )

        if tool_name == "idmc_get_commit_details":
            return c.get_commit_details(inp["commit_hash"])

        if tool_name == "idmc_get_commit_history":
            return c.get_commit_history(
                query=inp.get("query"),
                per_page=inp.get("per_page", 100),
                page=inp.get("page", 1),
            )

        if tool_name == "idmc_get_source_control_action_status":
            return c.get_source_control_action_status(
                inp["action_id"], inp.get("expand_objects", False)
            )

        # ---- DI – Connections CRUD ----
        if tool_name == "idmc_create_connection":
            payload = {
                "@type": "connection",
                "name": inp["name"],
                "type": inp["type"],
                "description": inp.get("description", ""),
            }
            if inp.get("agent_id"):
                payload["agentId"] = inp["agent_id"]
            if inp.get("runtime_environment_id"):
                payload["runtimeEnvironmentId"] = inp["runtime_environment_id"]
            field_map = {
                "username": "username", "password": "password", "host": "host",
                "port": "port", "database": "database", "schema": "schema",
                "service_url": "serviceUrl", "security_token": "securityToken",
                "authentication_type": "authenticationType", "codepage": "codepage",
            }
            for py_key, api_key in field_map.items():
                if inp.get(py_key) is not None:
                    payload[api_key] = inp[py_key]
            if inp.get("conn_params"):
                payload["connParams"] = inp["conn_params"]
            return c.create_connection(payload)

        if tool_name == "idmc_update_connection":
            return c.update_connection(
                inp["connection_id"], inp["payload"], inp.get("partial", False)
            )

        if tool_name == "idmc_delete_connection":
            return c.delete_connection(inp["connection_id"])

        if tool_name == "idmc_test_connection":
            return c.test_connection(inp["connection_id"])

        if tool_name == "idmc_migrate_connection":
            return c.migrate_connection(
                inp["source_conn"], inp["target_conn"], inp.get("project_name")
            )

        # ---- DI – Connectors metadata ----
        if tool_name == "idmc_list_connectors":
            return _paginate(c.list_connectors(), inp)

        if tool_name == "idmc_get_connector_metadata":
            return c.get_connector_metadata(inp["connector_name"])

        # ---- DI – Data Preview ----
        if tool_name == "idmc_get_data_preview":
            return c.get_data_preview(
                connection_id=inp["connection_id"],
                object_name=inp["object_name"],
                direction=inp.get("direction", "source"),
                num_rows=inp.get("num_rows", 10),
            )

        # ---- DI – Mappings ----
        if tool_name == "idmc_list_mappings":
            return _paginate(c.list_mappings(), inp)

        if tool_name == "idmc_get_mapping":
            return c.get_mapping(
                mapping_id=inp.get("mapping_id"), mapping_name=inp.get("mapping_name")
            )

        if tool_name == "idmc_get_mapping_transformations":
            return c.get_mapping_transformations(
                mapping_id=inp.get("mapping_id"),
                mapping_name=inp.get("mapping_name"),
                transformation_type=inp.get("transformation_type"),
            )

        # ---- DI – Mapping Tasks ----
        if tool_name == "idmc_list_mapping_tasks":
            return _paginate(c.list_mapping_tasks(), inp)

        if tool_name == "idmc_get_mapping_task":
            return c.get_mapping_task(
                task_id=inp.get("task_id"),
                federated_id=inp.get("federated_id"),
                task_name=inp.get("task_name"),
            )

        if tool_name == "idmc_create_mapping_task":
            payload = {
                "@type": "mtTask",
                "name": inp["name"],
                "description": inp.get("description", ""),
                "mappingId": inp["mapping_id"],
                "runtimeEnvironmentId": inp["runtime_environment_id"],
            }
            if inp.get("schedule_id"):
                payload["scheduleId"] = inp["schedule_id"]
            if inp.get("payload"):
                payload.update(inp["payload"])
            return c.create_mapping_task(payload)

        if tool_name == "idmc_update_mapping_task":
            return c.update_mapping_task(
                payload=inp["payload"],
                task_id=inp.get("task_id"),
                federated_id=inp.get("federated_id"),
                partial=inp.get("partial", False),
            )

        if tool_name == "idmc_delete_mapping_task":
            return c.delete_mapping_task(inp["task_id"])

        # ---- DI – Linear Taskflows ----
        if tool_name == "idmc_list_linear_taskflows":
            return _paginate(c.list_linear_taskflows(), inp)

        if tool_name == "idmc_get_linear_taskflow":
            return c.get_linear_taskflow(
                workflow_id=inp.get("workflow_id"), workflow_name=inp.get("workflow_name")
            )

        if tool_name == "idmc_create_linear_taskflow":
            tasks_payload = [
                {
                    "@type": "workflowTask",
                    "taskId": t["task_id"],
                    "type": t["type"],
                    "name": t["name"],
                    "stopOnError": t.get("stop_on_error", False),
                }
                for t in inp["tasks"]
            ]
            payload = {"@type": "workflow", "name": inp["name"], "tasks": tasks_payload}
            if inp.get("description"):
                payload["description"] = inp["description"]
            if inp.get("schedule_id"):
                payload["scheduleId"] = inp["schedule_id"]
            if inp.get("runtime_environment_id"):
                payload["runtimeEnvironmentId"] = inp["runtime_environment_id"]
            return c.create_linear_taskflow(payload)

        if tool_name == "idmc_update_linear_taskflow":
            return c.update_linear_taskflow(inp["workflow_id"], inp["payload"])

        if tool_name == "idmc_delete_linear_taskflow":
            return c.delete_linear_taskflow(inp["workflow_id"])

        # ---- DI – Published Taskflows ----
        if tool_name == "idmc_get_taskflow_status":
            return c.get_taskflow_status(
                inp["run_id"], subtask_details=inp.get("subtask_details", False)
            )

        if tool_name == "idmc_publish_taskflows":
            return c.publish_taskflows(inp["asset_paths"])

        if tool_name == "idmc_unpublish_taskflows":
            return c.unpublish_taskflows(inp["asset_paths"])

        # ---- DI – Expression Validation ----
        if tool_name == "idmc_validate_expression":
            return c.validate_expression(
                expression=inp["expression"],
                connection_id=inp["connection_id"],
                object_name=inp["object_name"],
                is_source_type=inp.get("is_source_type", True),
            )

        # ---- DI – Operational Insights Job Logs ----
        if tool_name == "idmc_get_di_job_log_entries":
            return c.get_di_job_log_entries(
                org_id=inp["org_id"],
                filter_str=inp.get("filter"),
                list_filter=inp.get("list_filter"),
                top=inp.get("top", 500),
                skip=inp.get("skip", 0),
            )

        # ---- DI – Fixed-Width Configuration ----
        if tool_name == "idmc_list_fwconfigs":
            return _paginate(c.list_fwconfigs(), inp)

        if tool_name == "idmc_get_fwconfig":
            return c.get_fwconfig(
                fwconfig_id=inp.get("fwconfig_id"), fwconfig_name=inp.get("fwconfig_name")
            )

        if tool_name == "idmc_create_fwconfig":
            payload = {
                "@type": "fwConfig",
                "name": inp["name"],
                "description": inp.get("description", ""),
                "lineSequential": inp.get("line_sequential", True),
                "padBytes": inp.get("pad_bytes", 0),
                "skipRows": inp.get("skip_rows", 0),
                "nullChar": inp.get("null_char", ""),
                "dateFormat": inp.get("date_format", ""),
                "nullCharType": inp.get("null_char_type", "ASCII"),
                "repeatNullChar": inp.get("repeat_null_char", False),
                "stripTrailingBlank": inp.get("strip_trailing_blank", False),
                "columns": [
                    {
                        "@type": "fwColumn",
                        "name": col["name"],
                        "nativeType": col.get("nativeType", "string"),
                        "precision": col["precision"],
                        "scale": col.get("scale", 0),
                    }
                    for col in inp["columns"]
                ],
            }
            return c.create_fwconfig(payload)

        if tool_name == "idmc_delete_fwconfig":
            return c.delete_fwconfig(inp["fwconfig_id"])

        # ---- DI – PowerCenter Mapplets ----
        if tool_name == "idmc_list_pc_mapplets":
            return _paginate(c.list_pc_mapplets(), inp)

        if tool_name == "idmc_get_pc_mapplet":
            return c.get_pc_mapplet(
                mapplet_id=inp.get("mapplet_id"), mapplet_name=inp.get("mapplet_name")
            )

        if tool_name == "idmc_delete_pc_mapplet":
            return c.delete_pc_mapplet(inp["mapplet_id"])

        # ---- Ingestion – DBMI / APPMI ----
        if tool_name == "idmc_create_ingestion_task":
            payload = {
                "taskType": inp.get("task_type", "dbmi"),
                "general": {
                    "name": inp["name"],
                    "description": inp.get("description", ""),
                    "location": inp.get("location", "Default"),
                    "runtimeEnvironment": inp["runtime_environment"],
                    "type": inp["load_type"],
                },
                "source": {"connection": inp["source_connection"]},
                "target": {"connection": inp["target_connection"]},
            }
            if inp.get("source_schema"):
                payload["source"]["schema"] = inp["source_schema"]
            if inp.get("target_schema"):
                payload["target"]["schema"] = inp["target_schema"]
            if inp.get("selection_rules"):
                payload["source"]["selectionRules"] = inp["selection_rules"]
            if inp.get("advanced_options"):
                payload.update(inp["advanced_options"])
            return c.create_ingestion_task(payload)

        if tool_name == "idmc_get_ingestion_task_id":
            return c.get_ingestion_task_id(
                task_name=inp["task_name"],
                project_id=inp.get("project_id"),
                folder_id=inp.get("folder_id"),
                page_no=inp.get("page_no", 0),
                page_size=inp.get("page_size", 25),
            )

        if tool_name == "idmc_deploy_ingestion_task":
            return c.deploy_ingestion_task(inp["task_id"])

        if tool_name == "idmc_get_ingestion_task_details":
            return c.get_ingestion_task_details(
                task_id=inp.get("task_id"),
                project_id=inp.get("project_id"),
                folder_id=inp.get("folder_id"),
                page_no=inp.get("page_no", 0),
                page_size=inp.get("page_size", 25),
                order_by=inp.get("order_by"),
            )

        if tool_name == "idmc_start_ingestion_job":
            return c.start_ingestion_job(inp["job_id"])

        if tool_name == "idmc_stop_ingestion_job":
            return c.stop_ingestion_job(inp["job_id"])

        if tool_name == "idmc_resume_ingestion_job":
            return c.resume_ingestion_job(inp["job_id"], inp.get("resume_options"))

        if tool_name == "idmc_undeploy_ingestion_job":
            return c.undeploy_ingestion_job(inp["job_id"])

        if tool_name == "idmc_get_ingestion_job_status":
            return c.get_ingestion_job_status(inp["job_id"])

        if tool_name == "idmc_get_ingestion_job_metrics":
            return c.get_ingestion_job_metrics(
                job_id=inp["job_id"],
                state_filter=inp.get("state_filter"),
                sort=inp.get("sort"),
                search=inp.get("search", ""),
                limit=inp.get("limit", 25),
                offset=inp.get("offset", 0),
            )

        # ---- Ingestion – File Ingestion (MI Tasks) ----
        if tool_name == "idmc_run_mi_task_job":
            return c.run_mi_task_job(
                task_id=inp["task_id"],
                task_name=inp.get("task_name"),
                parameters=inp.get("parameters"),
            )

        if tool_name == "idmc_get_mi_task_job_status":
            return c.get_mi_task_job_status(inp["run_id"])

        if tool_name == "idmc_get_mi_activity_log":
            return c.get_mi_activity_log(
                task_id=inp.get("task_id"),
                run_id=inp.get("run_id"),
                offset=inp.get("offset", 0),
                row_limit=inp.get("row_limit", 25),
                job_type=inp.get("job_type", "all"),
                fetch_file_events=inp.get("fetch_file_events", False),
                file_events_limit=inp.get("file_events_limit", 100),
            )

        if tool_name == "idmc_list_mi_tasks":
            return _paginate(c.list_mi_tasks(), inp)

        if tool_name == "idmc_create_mi_task":
            payload = {
                "name": inp["name"],
                "description": inp.get("description", ""),
                "sourceType": inp.get("source_type", "CONNECTION"),
                "agentGroup": inp["agent_group_id"],
                "sourceConnection": inp["source_connection"],
                "targetConnection": inp["target_connection"],
                "sourceParameters": inp["source_parameters"],
                "targetParameters": inp["target_parameters"],
                "filePickupOption": inp.get("file_pickup_option", "PATTERN"),
                "logLevel": inp.get("log_level", "NORMAL"),
                "allowConcurrency": str(inp.get("allow_concurrency", False)).lower(),
            }
            if inp.get("location"):
                payload["location"] = inp["location"]
            return c.create_mi_task(payload)

        if tool_name == "idmc_update_mi_task":
            return c.update_mi_task(inp["task_id"], inp["payload"])

        if tool_name == "idmc_delete_mi_task":
            return c.delete_mi_task(inp["task_id"])

        return {"error": f"Unknown tool: {tool_name}"}

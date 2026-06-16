"""
Informatica Cloud Data Profiling - API Client
Handles all REST API calls to the profiling service.
"""

import requests
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Session:
    session_id: str = ""        # v2 icSessionId
    v3_session_id: str = ""     # v3 INFA-SESSION-ID
    base_url: str = ""          # e.g. usw3-dqprofile.dm-us.informaticacloud.com
    frs_base_url: str = ""      # e.g. usw3.dm-us.informaticacloud.com  (no -dqprofile)
    pod_region: str = "us"

    @property
    def authenticated(self) -> bool:
        return bool(self.session_id and self.base_url)


class InformaticaAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"API Error {status_code}: {message}")


class InformaticaAPIClient:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or Session()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "IDS-SESSION-ID": self.session.session_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _di_headers(self) -> dict:
        """Header for DI/platform APIs that use icSessionId instead of IDS-SESSION-ID."""
        return {
            "icSessionId": self.session.session_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _v3_headers(self) -> dict:
        """Header for public/core/v3 admin APIs that require INFA-SESSION-ID."""
        return {
            "INFA-SESSION-ID": self.session.v3_session_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # Admin v3 URL patterns that commonly 404 on restricted accounts
    _ADMIN_V3_PATTERNS = (
        "/public/core/v3/users",
        "/public/core/v3/userGroups",
        "/public/core/v3/roles",
        "/public/core/v3/license",
        "/public/core/v3/objects/",
    )

    def _check(self, resp: requests.Response) -> dict:
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            msg = str(detail)
            # Annotate empty 404s on known admin endpoints with a helpful hint
            if resp.status_code == 404 and not msg.strip("{}\" "):
                url = resp.url if hasattr(resp, "url") else ""
                if any(p in url for p in self._ADMIN_V3_PATTERNS):
                    msg = (
                        "Admin API returned 404 — the account may lack admin privileges, "
                        "or this endpoint is unavailable on this pod/region. "
                        "Verify the account has 'Admin' role in the IDMC console."
                    )
            raise InformaticaAPIError(resp.status_code, msg)
        if resp.status_code == 204:
            return {"status": "success", "code": 204}
        if not resp.content:
            return {}
        return resp.json()

    def _profiling_url(self, path: str) -> str:
        return f"https://{self.session.base_url}/{path.lstrip('/')}"

    def _frs_url(self, path: str) -> str:
        return f"https://{self.session.frs_base_url}/{path.lstrip('/')}"

    def _v3_url(self, path: str) -> str:
        """Build URL for public/core/v3 admin APIs — always rooted under /saas/."""
        return f"https://{self.session.frs_base_url}/saas/{path.lstrip('/')}"

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self, username: str, password: str, pod_region: str = "us") -> dict:
        """Login to both v2 and v3, capturing icSessionId and INFA-SESSION-ID."""
        # --- v2 login ---
        v2_url = f"https://dm-{pod_region}.informaticacloud.com/ma/api/v2/user/login"
        resp = requests.post(
            v2_url,
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
        )
        data = self._check(resp)

        self.session.session_id = data["icSessionId"]
        self.session.pod_region = pod_region

        # serverUrl example: https://usw3.dm-us.informaticacloud.com/saas
        server_url: str = data["serverUrl"]
        # Strip scheme and /saas to get the raw hostname
        hostname = server_url.replace("https://", "").replace("/saas", "").rstrip("/")
        self.session.frs_base_url = hostname

        # Insert -dqprofile into the first label for profiling APIs
        # usw3.dm-us.informaticacloud.com → usw3-dqprofile.dm-us.informaticacloud.com
        parts = hostname.split(".")
        parts[0] = parts[0] + "-dqprofile"
        self.session.base_url = ".".join(parts)

        # --- v3 login ---
        v3_url = f"https://dm-{pod_region}.informaticacloud.com/saas/public/core/v3/login"
        v3_resp = requests.post(
            v3_url,
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
        )
        v3_session_id = ""
        try:
            v3_data = self._check(v3_resp)
            # Response: {"products": [{"baseApiUrl": "https://emw1.dm-em.../saas"}], "userInfo": {"sessionId": "..."}}
            v3_session_id = (
                v3_data.get("userInfo", {}).get("sessionId", "")
                or v3_data.get("sessionId", "")
            )
            self.session.v3_session_id = v3_session_id

            # Capture baseApiUrl from the first product — this is the authoritative base for all API calls
            products = v3_data.get("products", [])
            if products:
                base_api_url = products[0].get("baseApiUrl", "")
                if base_api_url:
                    # Strip scheme and trailing /saas to get the raw hostname
                    hostname = base_api_url.replace("https://", "").replace("/saas", "").rstrip("/")
                    self.session.frs_base_url = hostname
                    parts = hostname.split(".")
                    parts[0] = parts[0] + "-dqprofile"
                    self.session.base_url = ".".join(parts)
        except Exception:
            # v3 login failure is non-fatal; v3 tools will return auth errors if needed
            self.session.v3_session_id = ""

        return {
            "status": "logged_in",
            "user": data.get("name"),
            "org": data.get("orgId"),
            "base_url": self.session.base_url,
            "session_id": self.session.session_id,
            "v3_session_id": v3_session_id if v3_session_id else "not_available",
        }

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    def list_connections(
        self,
        connection_id: Optional[str] = None,
        connection_name: Optional[str] = None,
    ) -> list:
        if connection_id:
            path = f"saas/api/v2/connection/{connection_id}"
        elif connection_name:
            encoded = connection_name.replace(" ", "%20")
            path = f"saas/api/v2/connection/name/{encoded}"
        else:
            path = "saas/api/v2/connection"
        url = self._frs_url(path)
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def search_connections(
        self,
        ui_type: str,
        agent_id: Optional[str] = None,
        runtime_environment_id: Optional[str] = None,
    ) -> list:
        params: dict = {"uiType": ui_type}
        if runtime_environment_id:
            params["runtimeEnvironmentId"] = runtime_environment_id
        elif agent_id:
            params["agentId"] = agent_id
        url = self._frs_url("saas/api/v2/connection/search")
        resp = requests.get(url, headers=self._di_headers(), params=params)
        return self._check(resp)

    def get_connection_objects(
        self,
        connection_id: str,
        object_type: str = "source",
        search_pattern: str = "",
        max_records_count: int = 200,
        metadata_only: bool = False,
    ) -> list:
        base = f"saas/api/v2/connection/{object_type}/{connection_id}"
        if metadata_only:
            base += "/metadata"
        url = self._frs_url(base)
        params = {}
        if search_pattern:
            params["searchPattern"] = search_pattern
        if not metadata_only:
            params["maxRecordsCount"] = max_records_count
        resp = requests.get(url, headers=self._di_headers(), params=params)
        return self._check(resp)

    def get_object_fields(
        self,
        connection_id: str,
        object_name: str,
        source_type: str = "oracle",
        flat_file_attrs: Optional[dict] = None,
    ) -> list:
        di_id = self._resolve_di_connection_id(connection_id)
        url = self._frs_url(
            f"saas/api/v2/connection/source/{di_id}/field/{object_name}"
        )
        if source_type.lower() in ("flatfile", "flat_file", "csvfile"):
            body = flat_file_attrs or {
                "@type": "flatFileAttrs",
                "delimiter": ",",
                "textQualifier": "\"",
                "escapeChar": "",
                "firstDataRow": 2,
                "headerLineNo": 1,
            }
            params = {}
        else:
            body = flat_file_attrs or {}
            params = {"validateFields": "false"}
        resp = requests.post(url, headers=self._di_headers(), json=body, params=params)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Projects / Folders
    # ------------------------------------------------------------------

    def list_projects(self, name: Optional[str] = None) -> list:
        if name:
            url = self._v3_url(f"public/core/v3/projects/name/{name}")
        else:
            url = self._v3_url("public/core/v3/projects")
        resp = requests.get(url, headers=self._v3_headers())
        data = self._check(resp)
        if isinstance(data, list):
            return data
        return data.get("projects", data.get("value", [data] if data else []))

    def create_project(self, name: str, description: str = "") -> dict:
        url = self._v3_url("public/core/v3/projects")
        resp = requests.post(
            url, headers=self._v3_headers(), json={"name": name, "description": description}
        )
        return self._check(resp)

    def list_folders(
        self,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> list:
        if project_id:
            url = self._v3_url(f"public/core/v3/projects/{project_id}/folders")
        elif project_name:
            url = self._v3_url(f"public/core/v3/projects/name/{project_name}/folders")
        else:
            raise ValueError("project_id or project_name required")
        resp = requests.get(url, headers=self._v3_headers())
        data = self._check(resp)
        if isinstance(data, list):
            return data
        return data.get("folders", data.get("value", []))

    def create_folder(
        self,
        name: str,
        description: str = "",
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> dict:
        if project_id:
            url = self._v3_url(f"public/core/v3/projects/{project_id}/folders")
        elif project_name:
            url = self._v3_url(f"public/core/v3/projects/name/{project_name}/folders")
        else:
            url = self._v3_url("public/core/v3/folders")
        resp = requests.post(
            url, headers=self._v3_headers(), json={"name": name, "description": description}
        )
        return self._check(resp)

    # ------------------------------------------------------------------
    # Profiles
    # ------------------------------------------------------------------

    def list_profiles(
        self,
        name: Optional[str] = None,
        exact_match: Optional[bool] = None,
        frs_project_name: Optional[str] = None,
        frs_folder_name: Optional[str] = None,
    ) -> list:
        params: dict = {}
        if name:
            params["name"] = name
        if exact_match is not None:
            params["exactMatch"] = str(exact_match).lower()
        if frs_project_name:
            params["frsProjectName"] = frs_project_name
        if frs_folder_name:
            params["frsFolderName"] = frs_folder_name

        url = self._profiling_url("profiling-service/api/v1/profile")
        resp = requests.get(url, headers=self._headers(), params=params)
        return self._check(resp)

    def get_profile(self, profile_id: str) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/profile/{profile_id}")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def create_profile(self, payload: dict) -> dict:
        url = self._profiling_url("profiling-service/api/v1/profile")
        resp = requests.post(url, headers=self._headers(), json=payload)
        return self._check(resp)

    def update_profile(self, profile_id: str, payload: dict) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/profile/{profile_id}")
        resp = requests.put(url, headers=self._headers(), json=payload)
        return self._check(resp)

    def delete_profile(self, profile_id: str) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/profile/{profile_id}")
        resp = requests.delete(url, headers=self._headers())
        return self._check(resp)

    def run_profile(self, profile_id: str) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/profile/{profile_id}/execute")
        resp = requests.post(url, headers=self._headers(), json={})
        return self._check(resp)

    def suggest_profile_name(
        self,
        frs_project_name: Optional[str] = None,
        frs_folder_name: Optional[str] = None,
    ) -> str:
        params: dict = {}
        if frs_project_name:
            params["frsProjectName"] = frs_project_name
        if frs_folder_name:
            params["frsFolderName"] = frs_folder_name
        url = self._profiling_url("profiling-service/api/v1/profile/newProfileName")
        resp = requests.get(url, headers=self._headers(), params=params)
        return resp.text.strip()

    def get_last_successful_run_key(self, payload: dict) -> int:
        url = self._profiling_url("profiling-service/api/v1/profile/lastSuccessfulRunKey")
        resp = requests.post(url, headers=self._headers(), json=payload)
        return self._check(resp)

    def get_rule_ids(self, payload: dict) -> dict:
        url = self._profiling_url("profiling-service/api/v1/profile/getRuleIds")
        resp = requests.post(url, headers=self._headers(), json=payload)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------

    def get_job(self, job_id: str) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/job/{job_id}")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def get_running_jobs(self, profile_id: str) -> list:
        url = self._profiling_url(f"profiling-service/api/v1/job/runningJobs/{profile_id}")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def stop_job(self, job_id: str, job_step_id: Optional[str] = None, job_type: Optional[str] = None) -> dict:
        params: dict = {"jobID": job_id}
        if job_step_id:
            params["jobStepID"] = job_step_id
        if job_type:
            params["jobType"] = job_type
        url = self._profiling_url("profiling-service/api/v1/job/stop")
        resp = requests.get(url, headers=self._headers(), params=params)
        return self._check(resp)

    def resume_job(self, job_id: str, job_step_id: Optional[str] = None, job_type: Optional[str] = None) -> dict:
        params: dict = {"jobID": job_id}
        if job_step_id:
            params["jobStepID"] = job_step_id
        if job_type:
            params["jobType"] = job_type
        url = self._profiling_url("profiling-service/api/v1/job/resume")
        resp = requests.get(url, headers=self._headers(), params=params)
        return self._check(resp)

    def get_session_logs(self, job_step_id: str) -> str:
        url = self._profiling_url(f"profiling-service/api/v1/job/getSessionLogs/{job_step_id}")
        resp = requests.get(url, headers=self._headers())
        return resp.text

    # ------------------------------------------------------------------
    # Profile Results (metric-store)
    # ------------------------------------------------------------------

    def list_columns(self, profile_id: str) -> dict:
        url = self._profiling_url(
            f"metric-store/api/v1/odata/Profiles('{profile_id}')/Columns"
        )
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def get_column(self, profile_id: str, column_id: str) -> dict:
        url = self._profiling_url(
            f"metric-store/api/v1/odata/Profiles('{profile_id}')/Columns('{column_id}')"
        )
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def get_column_patterns(self, profile_id: str, column_id: str) -> dict:
        url = self._profiling_url(
            f"metric-store/api/v1/odata/Profiles('{profile_id}')/Columns('{column_id}')/Patterns"
        )
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def get_column_datatypes(self, profile_id: str, column_id: str) -> dict:
        url = self._profiling_url(
            f"metric-store/api/v1/odata/Profiles('{profile_id}')/Columns('{column_id}')/DataTypes"
        )
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def get_value_frequencies(self, profile_id: str, column_id: str) -> dict:
        url = self._profiling_url(
            f"metric-store/api/v1/odata/Profiles('{profile_id}')/Columns('{column_id}')/ValueFrequencies"
        )
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def export_profile_results(
        self,
        profile_id: str,
        run_key: int = 1,
        range_type: str = "All Columns",
        file_format: str = "Excel",
    ) -> bytes:
        url = self._profiling_url(f"metric-store/api/v1/Profiles('{profile_id}')/Export")
        params = {"runKey": run_key, "range": range_type, "fileFormat": file_format}
        resp = requests.get(url, headers=self._headers(), params=params)
        return resp.content

    # ------------------------------------------------------------------
    # Run Details
    # ------------------------------------------------------------------

    def list_run_details(self, profile_id: str) -> list:
        url = self._profiling_url("profiling-service/api/v1/runDetail")
        resp = requests.get(url, headers=self._headers(), params={"profileId": profile_id})
        return self._check(resp)

    def get_run_detail(self, run_detail_id: str) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/runDetail/{run_detail_id}")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def delete_run_details(self, profile_id: str, run_detail_ids: list) -> list:
        url = self._profiling_url("profiling-service/api/v1/runDetail")
        payload = {"profileId": profile_id, "runDetailIds": run_detail_ids}
        resp = requests.delete(url, headers=self._headers(), json=payload)
        return self._check(resp)

    def get_top_n_runs(self, limit: int = 10) -> list:
        url = self._profiling_url(f"profiling-service/api/v1/runDetail/topNrun?limit={limit}")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def get_top_n_profile_tasks(self, limit: int = 10) -> list:
        url = self._profiling_url(f"profiling-service/api/v1/runDetail/topNProfiletask?limit={limit}")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def create_query(self, payload: dict) -> dict:
        url = self._profiling_url("profiling-service/api/v1/query")
        resp = requests.post(url, headers=self._headers(), json=payload)
        return self._check(resp)

    def get_query(self, query_id: str) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/query/{query_id}")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def list_queries(self, profile_id: str) -> list:
        url = self._profiling_url("profiling-service/api/v1/query")
        resp = requests.get(url, headers=self._headers(), params={"profileId": profile_id})
        return self._check(resp)

    def execute_query(self, query_id: str) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/query/{query_id}/execute")
        resp = requests.post(url, headers=self._headers(), json={})
        return self._check(resp)

    def get_query_results(self, query_id: str) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/query/{query_id}/queryResults")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def update_query(self, query_id: str, payload: dict) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/query/{query_id}")
        resp = requests.put(url, headers=self._headers(), json=payload)
        return self._check(resp)

    def delete_query(self, query_id: str) -> dict:
        url = self._profiling_url(f"profiling-service/api/v1/query/{query_id}")
        resp = requests.delete(url, headers=self._headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # CLAIRE Insights
    # ------------------------------------------------------------------

    def get_insights(self, profile_id: str) -> dict:
        url = self._profiling_url(
            f"metric-store/api/v1/odata/Profiles('{profile_id}')/Insights"
        )
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def update_insights(self, profile_id: str, curated_insights: list) -> list:
        url = self._profiling_url(
            f"metric-store/api/v1/Profiles('{profile_id}')/Insights"
        )
        resp = requests.patch(
            url, headers=self._headers(), json={"curatedInsights": curated_insights}
        )
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Activity Logs (v2)
    # ------------------------------------------------------------------

    def get_activity_log(
        self,
        log_id: Optional[str] = None,
        task_id: Optional[str] = None,
        run_id: Optional[str] = None,
        offset: Optional[int] = None,
        row_limit: Optional[int] = None,
    ) -> list:
        params: dict = {}
        if task_id:
            params["taskId"] = task_id
        if run_id:
            params["runId"] = run_id
        if offset is not None:
            params["offset"] = offset
        if row_limit is not None:
            params["rowLimit"] = row_limit
        path = f"saas/api/v2/activity/activityLog/{log_id}" if log_id else "saas/api/v2/activity/activityLog"
        url = self._frs_url(path)
        resp = requests.get(url, headers=self._headers(), params=params)
        return self._check(resp)

    def get_activity_monitor(self) -> list:
        url = self._frs_url("saas/api/v2/activity/activityMonitor")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def get_error_log(self, log_id: str) -> str:
        url = self._frs_url(f"saas/api/v2/activity/errorLog/{log_id}")
        resp = requests.get(url, headers=self._headers())
        return resp.text

    # ------------------------------------------------------------------
    # Admin – Audit Logs (v2)
    # ------------------------------------------------------------------

    def get_audit_log(self, batch_id: int = 0, batch_size: int = 200) -> list:
        url = self._frs_url("saas/api/v2/auditlog")
        params = {"batchId": batch_id, "batchSize": batch_size}
        resp = requests.get(url, headers=self._headers(), params=params)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Users (v3)
    # ------------------------------------------------------------------

    def get_users(self, query: Optional[str] = None, limit: int = 100, skip: int = 0) -> dict:
        url = self._v3_url("public/core/v3/users")
        params: dict = {"limit": limit, "skip": skip}
        if query:
            params["q"] = query
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    def get_user(self, user_id: str) -> dict:
        # IDMC v3 has no GET /users/{id}; use q filter by userId or userName (p.328)
        url = self._v3_url("public/core/v3/users")
        # Heuristic: IDs are alphanumeric 22-char strings; usernames contain @ or .
        field = "userName" if ("@" in user_id or "." in user_id) else "userId"
        params = {"q": f'{field}=="{user_id}"', "limit": 1}
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        result = self._check(resp)
        if isinstance(result, list) and result:
            return result[0]
        raise InformaticaAPIError(f"User not found: {user_id}")

    def create_user(self, payload: dict) -> dict:
        url = self._v3_url("public/core/v3/users")
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def update_user_roles(self, user_id: str, roles: list, action: str = "addRoles") -> dict:
        url = self._v3_url(f"public/core/v3/users/{user_id}/{action}")
        resp = requests.put(url, headers=self._v3_headers(), json={"roles": roles})
        return self._check(resp)

    def update_user_groups(self, user_id: str, groups: list, action: str = "addGroups") -> dict:
        url = self._v3_url(f"public/core/v3/users/{user_id}/{action}")
        resp = requests.put(url, headers=self._v3_headers(), json={"userGroups": groups})
        return self._check(resp)

    def delete_user(self, user_id: str) -> dict:
        url = self._v3_url(f"public/core/v3/users/{user_id}")
        resp = requests.delete(url, headers=self._v3_headers())
        return self._check(resp)

    def change_password(self, old_password: str, new_password: str) -> dict:
        url = self._v3_url("public/core/v3/Users/ChangePassword")
        payload = {"oldPassword": old_password, "newPassword": new_password}
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Roles (v3)
    # ------------------------------------------------------------------

    def get_roles(self, query: Optional[str] = None, expand: Optional[str] = None, limit: Optional[int] = None, skip: Optional[int] = None) -> list:
        url = self._v3_url("public/core/v3/roles")
        params: dict = {}
        if query:
            params["q"] = query
        if expand:
            params["expand"] = expand
        if limit is not None:
            params["limit"] = limit
        if skip is not None:
            params["skip"] = skip
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    def _role_path(self, role_id: Optional[str] = None, role_name: Optional[str] = None) -> str:
        if role_name:
            return f"public/core/v3/roles/name/{role_name}"
        return f"public/core/v3/roles/{role_id}"

    def create_role(self, name: str, description: str, privileges: list) -> dict:
        url = self._v3_url("public/core/v3/roles")
        resp = requests.post(url, headers=self._v3_headers(), json={"name": name, "description": description, "privileges": privileges})
        return self._check(resp)

    def update_role_privileges(self, privileges: list, action: str = "addPrivileges", role_id: Optional[str] = None, role_name: Optional[str] = None) -> dict:
        url = self._v3_url(f"{self._role_path(role_id, role_name)}/{action}")
        resp = requests.put(url, headers=self._v3_headers(), json={"privileges": privileges})
        return self._check(resp)

    def delete_role(self, role_id: Optional[str] = None, role_name: Optional[str] = None) -> dict:
        url = self._v3_url(self._role_path(role_id, role_name))
        resp = requests.delete(url, headers=self._v3_headers())
        return self._check(resp)

    def get_privileges(self, query: Optional[str] = None) -> list:
        url = self._v3_url("public/core/v3/privileges")
        params: dict = {}
        if query:
            params["q"] = query
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – User Groups (v3)
    # ------------------------------------------------------------------

    def _group_path(self, group_id: Optional[str] = None, group_name: Optional[str] = None) -> str:
        if group_name:
            return f"public/core/v3/userGroups/name/{group_name}"
        return f"public/core/v3/userGroups/{group_id}"

    def get_user_groups(self, query: Optional[str] = None, limit: Optional[int] = None, skip: Optional[int] = None) -> list:
        url = self._v3_url("public/core/v3/userGroups")
        params = {}
        if query:
            params["q"] = query
        if limit is not None:
            params["limit"] = limit
        if skip is not None:
            params["skip"] = skip
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    def get_user_group(self, group_id: Optional[str] = None, group_name: Optional[str] = None) -> dict:
        url = self._v3_url(self._group_path(group_id, group_name))
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    def create_user_group(self, name: str, description: str = "", roles: Optional[list] = None, users: Optional[list] = None) -> dict:
        url = self._v3_url("public/core/v3/userGroups")
        payload: dict = {"name": name, "description": description}
        if roles:
            payload["roles"] = roles
        if users:
            payload["users"] = users
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def update_user_group(self, users: list, action: str = "addUsers", group_id: Optional[str] = None, group_name: Optional[str] = None) -> dict:
        url = self._v3_url(f"{self._group_path(group_id, group_name)}/{action}")
        resp = requests.put(url, headers=self._v3_headers(), json={"users": users})
        return self._check(resp)

    def update_user_group_roles(self, roles: list, action: str = "addRoles", group_id: Optional[str] = None, group_name: Optional[str] = None) -> dict:
        url = self._v3_url(f"{self._group_path(group_id, group_name)}/{action}")
        resp = requests.put(url, headers=self._v3_headers(), json={"roles": roles})
        return self._check(resp)

    def delete_user_group(self, group_id: Optional[str] = None, group_name: Optional[str] = None) -> dict:
        url = self._v3_url(self._group_path(group_id, group_name))
        resp = requests.delete(url, headers=self._v3_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Schedules (v3)
    # ------------------------------------------------------------------

    def get_schedules(self, query: Optional[str] = None, schedule_id: Optional[str] = None) -> list:
        if schedule_id:
            url = self._v3_url(f"public/core/v3/schedule/{schedule_id}")
        else:
            url = self._v3_url("public/core/v3/schedule")
        params = {}
        if query:
            params["q"] = query
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    def create_schedule(self, payload: dict) -> dict:
        url = self._v3_url("public/core/v3/schedule")
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def update_schedule(self, schedule_id: str, payload: dict) -> dict:
        url = self._v3_url(f"public/core/v3/schedule/{schedule_id}")
        resp = requests.patch(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def delete_schedule(self, schedule_id: str) -> dict:
        url = self._v3_url(f"public/core/v3/schedule/{schedule_id}")
        resp = requests.delete(url, headers=self._v3_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Runtime Environments / Secure Agents (v2)
    # ------------------------------------------------------------------

    def get_runtime_environments(
        self,
        env_id: Optional[str] = None,
        env_name: Optional[str] = None,
    ) -> list:
        if env_id:
            path = f"saas/api/v2/runtimeEnvironment/{env_id}"
        elif env_name:
            encoded = env_name.replace(" ", "%20")
            path = f"saas/api/v2/runtimeEnvironment/name/{encoded}"
        else:
            path = "saas/api/v2/runtimeEnvironment"
        url = self._frs_url(path)
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def get_secure_agents(
        self,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        include_unassigned_only: bool = False,
        basic_info: bool = False,
        include_service_details: bool = False,
        only_status: bool = True,
    ) -> list:
        if include_service_details:
            # /api/v2/agent/details or /api/v2/agent/details/<id>
            path = f"saas/api/v2/agent/details/{agent_id}" if agent_id else "saas/api/v2/agent/details"
            params = {} if only_status else {"onlyStatus": "false"}
        elif agent_id:
            path = f"saas/api/v2/agent/{agent_id}"
            params = {}
        elif agent_name:
            encoded = agent_name.replace(" ", "%20")
            path = f"saas/api/v2/agent/name/{encoded}"
            params = {}
        else:
            path = "saas/api/v2/agent"
            params = {}
            if include_unassigned_only:
                params["includeUnassignedOnly"] = "true"
            if basic_info:
                params["basicInfo"] = "true"
        url = self._frs_url(path)
        resp = requests.get(url, headers=self._di_headers(), params=params)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Organizations (v2)
    # ------------------------------------------------------------------

    def get_organization(self) -> dict:
        url = self._frs_url("saas/api/v2/org")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Licenses (v3)
    # ------------------------------------------------------------------

    def get_license(self) -> dict:
        url = self._v3_url("public/core/v3/license/org")
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Object Permissions (v3)
    # ------------------------------------------------------------------

    def get_object_permissions(self, object_id: str, acl_id: Optional[str] = None) -> dict:
        if acl_id:
            url = self._v3_url(f"public/core/v3/objects/{object_id}/permissions/{acl_id}")
        else:
            url = self._v3_url(f"public/core/v3/objects/{object_id}/permissions")
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    def create_object_permission(
        self,
        object_id: str,
        principal_type: str,
        principal_name: str,
        read: bool,
        update: bool,
        delete: bool,
        execute: bool,
        change_permission: bool,
    ) -> dict:
        url = self._v3_url(f"public/core/v3/objects/{object_id}/permissions")
        payload = {
            "principal": {"type": principal_type, "name": principal_name},
            "permissions": {
                "read": read,
                "update": update,
                "delete": delete,
                "execute": execute,
                "changePermission": change_permission,
            },
        }
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def update_object_permission(
        self,
        object_id: str,
        acl_id: str,
        principal_type: str,
        principal_name: str,
        read: bool,
        update: bool,
        delete: bool,
        execute: bool,
        change_permission: bool,
    ) -> dict:
        url = self._v3_url(f"public/core/v3/objects/{object_id}/permissions/{acl_id}")
        payload = {
            "principal": {"type": principal_type, "name": principal_name},
            "permissions": {
                "read": read,
                "update": update,
                "delete": delete,
                "execute": execute,
                "changePermission": change_permission,
            },
        }
        resp = requests.put(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def delete_object_permission(self, object_id: str, acl_id: Optional[str] = None) -> dict:
        if acl_id:
            url = self._v3_url(f"public/core/v3/objects/{object_id}/permissions/{acl_id}")
        else:
            url = self._v3_url(f"public/core/v3/objects/{object_id}/permissions")
        resp = requests.delete(url, headers=self._v3_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Jobs (v2 — Data Integration tasks)
    # ------------------------------------------------------------------

    def start_di_job(self, payload: dict) -> dict:
        url = self._frs_url("saas/api/v2/job")
        resp = requests.post(url, headers=self._headers(), json=payload)
        return self._check(resp)

    def stop_di_job(self, payload: dict, clean_stop: bool = False) -> dict:
        path = "api/v2/job/stop"
        if clean_stop:
            path += "?cleanStop=true"
        url = self._frs_url(path)
        resp = requests.post(url, headers=self._headers(), json=payload)
        return self._check(resp)

    def get_di_activity_log(self, log_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/activity/activityLog/{log_id}")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Server Time (v2)
    # ------------------------------------------------------------------

    def get_server_time(self) -> dict:
        url = self._frs_url("saas/api/v2/server/serverTime")
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Admin – Logout (v2)
    # ------------------------------------------------------------------

    def logout(self) -> dict:
        # v2 logout — uses icSessionId header per spec
        v2_url = self._frs_url("saas/api/v2/user/logout")
        requests.post(v2_url, headers=self._di_headers(), json={})

        # v3 logout — uses INFA-SESSION-ID header per spec
        v3_result = {}
        if self.session.v3_session_id:
            v3_url = f"https://dm-{self.session.pod_region}.informaticacloud.com/saas/public/core/v3/logout"
            v3_resp = requests.post(v3_url, headers=self._v3_headers())
            try:
                v3_result = self._check(v3_resp)
            except Exception:
                pass

        self.session.session_id = ""
        self.session.v3_session_id = ""
        self.session.base_url = ""
        self.session.frs_base_url = ""
        return {"status": "logged_out", "v3": v3_result or {"status": "success"}}

    # ------------------------------------------------------------------
    # Platform v2 – Tasks
    # ------------------------------------------------------------------

    def get_di_tasks(self, task_type: str) -> list:
        url = self._frs_url(f"saas/api/v2/task?type={task_type}")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v2 – Bundles
    # ------------------------------------------------------------------

    def get_bundle(
        self,
        bundle_id: Optional[str] = None,
        bundle_name: Optional[str] = None,
        installed: Optional[bool] = None,
        published: Optional[bool] = None,
    ) -> dict:
        if bundle_id:
            url = self._frs_url(f"saas/api/v2/bundleObject/{bundle_id}")
        elif bundle_name:
            url = self._frs_url(f"saas/api/v2/bundleObject/name/{bundle_name}")
        else:
            params: dict = {}
            if installed is not None:
                params["installed"] = str(installed).lower()
            if published is not None:
                params["published"] = str(published).lower()
            url = self._frs_url("saas/api/v2/bundleObject/")
            resp = requests.get(url, headers=self._di_headers(), params=params)
            return self._check(resp)
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def install_bundle(self, bundle_object_id: str) -> dict:
        url = self._frs_url("saas/api/v2/bundleObjectLicense")
        resp = requests.post(url, headers=self._di_headers(), json={"bundleObjectId": bundle_object_id})
        return self._check(resp)

    def uninstall_bundle(self, bundle_object_id: str, update_option: str = "EXCEPTION_IF_IS_USED") -> dict:
        url = self._frs_url(
            f"saas/api/v2/bundleObjectLicense?bundleObjectId={bundle_object_id}&updateOption={update_option}"
        )
        resp = requests.delete(url, headers=self._di_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v2 – Organisation management
    # ------------------------------------------------------------------

    def get_organization_details(
        self, org_id: Optional[str] = None, org_name: Optional[str] = None
    ) -> dict:
        if org_id:
            url = self._frs_url(f"saas/api/v2/org/{org_id}")
        elif org_name:
            url = self._frs_url(f"saas/api/v2/org/name/{org_name}")
        else:
            url = self._frs_url("saas/api/v2/org")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def update_organization(self, payload: dict, org_id: Optional[str] = None) -> dict:
        path = f"saas/api/v2/org/{org_id}" if org_id else "saas/api/v2/org"
        url = self._frs_url(path)
        resp = requests.post(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    def delete_sub_organization(self, org_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/org/{org_id}")
        resp = requests.delete(url, headers=self._di_headers())
        return self._check(resp)

    def create_sub_organization(self, payload: dict) -> dict:
        url = self._frs_url("saas/api/v2/user/register")
        resp = requests.post(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v2 – Secure Agent management
    # ------------------------------------------------------------------

    def delete_secure_agent(self, agent_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/agent/{agent_id}")
        resp = requests.delete(url, headers=self._di_headers())
        return self._check(resp)

    def get_agent_installer_info(self, platform: str = "linux64") -> dict:
        url = self._frs_url(f"saas/api/v2/agent/installerInfo/{platform}")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v2 – Runtime Environment management
    # ------------------------------------------------------------------

    def create_runtime_environment(self, name: str, is_shared: bool = False) -> dict:
        url = self._frs_url("saas/api/v2/runtimeEnvironment")
        resp = requests.post(
            url, headers=self._di_headers(),
            json={"name": name, "isShared": is_shared}
        )
        return self._check(resp)

    def update_runtime_environment(self, env_id: str, payload: dict) -> dict:
        url = self._frs_url(f"saas/api/v2/runtimeEnvironment/{env_id}")
        resp = requests.post(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    def delete_runtime_environment(self, env_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/runtimeEnvironment/{env_id}")
        resp = requests.delete(url, headers=self._di_headers())
        return self._check(resp)

    def get_runtime_environment_selections(self, env_id: str, details: bool = False) -> dict:
        path = f"saas/api/v2/runtimeEnvironment/{env_id}/selections"
        if details:
            path += "/details"
        url = self._frs_url(path)
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def update_runtime_environment_selections(self, env_id: str, payload: dict) -> dict:
        url = self._frs_url(f"saas/api/v2/runtimeEnvironment/{env_id}/selections")
        resp = requests.put(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    def get_runtime_environment_configs(
        self, env_id: str, platform: str = "linux64", details: bool = False
    ) -> dict:
        endpoint = "configs/details" if details else "configs"
        url = self._frs_url(f"saas/api/v2/runtimeEnvironment/{env_id}/{endpoint}/{platform}")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def update_runtime_environment_configs(
        self, env_id: str, platform: str = "linux64", payload: dict = None
    ) -> dict:
        url = self._frs_url(f"saas/api/v2/runtimeEnvironment/{env_id}/configs/{platform}")
        resp = requests.put(url, headers=self._di_headers(), json=payload or {})
        return self._check(resp)

    def delete_runtime_environment_configs(self, env_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/runtimeEnvironment/{env_id}/configs")
        resp = requests.delete(url, headers=self._di_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v2 – Session logs & session validation
    # ------------------------------------------------------------------

    def get_session_log(
        self,
        log_id: str,
        item_id: Optional[str] = None,
        child_item_id: Optional[str] = None,
    ) -> bytes:
        path = f"saas/api/v2/activity/activityLog/{log_id}/sessionLog"
        params: dict = {}
        if item_id:
            params["itemId"] = item_id
        if child_item_id:
            params["childItemId"] = child_item_id
        url = self._frs_url(path)
        resp = requests.get(url, headers=self._di_headers(), params=params)
        return resp.content

    def validate_session(self, username: str) -> dict:
        url = self._frs_url("saas/api/v2/user/validSessionId")
        payload = {
            "@type": "validatedToken",
            "userName": username,
            "icToken": self.session.session_id,
        }
        resp = requests.post(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    def logout_all_sessions(self, username: str, password: str) -> dict:
        region = self.session.pod_region
        url = f"https://dm-{region}.informaticacloud.com/ma/api/v2/user/logoutall"
        resp = requests.post(
            url,
            headers=self._di_headers(),
            json={"@type": "logout", "username": username, "password": password},
        )
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Lookup & Objects
    # ------------------------------------------------------------------

    def lookup_object(self, objects: list) -> dict:
        url = self._v3_url("public/core/v3/lookup")
        resp = requests.post(url, headers=self._v3_headers(), json={"objects": objects})
        return self._check(resp)

    def list_assets(self, query: Optional[str] = None, limit: int = 200, skip: int = 0) -> dict:
        params: dict = {"limit": limit, "skip": skip}
        if query:
            params["q"] = query
        url = self._v3_url("public/core/v3/objects")
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    def list_project_assets_recursive(self, project_name: str) -> dict:
        """Two-phase recursive asset listing for a project.

        Phase 1 — fetch everything directly under the project root.
        Phase 2 — for every Folder found, fetch its contents in a second pass.
        Returns a unified list with project, folder, asset name, type, path,
        updatedBy, updateTime, description, and tags columns.
        """
        def _fetch(location: str) -> list:
            params = {"q": f"location=='{location}'", "limit": 200, "skip": 0}
            url = self._v3_url("public/core/v3/objects")
            all_objects = []
            while True:
                resp = requests.get(url, headers=self._v3_headers(), params=params)
                data = self._check(resp)
                batch = data.get("objects", [])
                all_objects.extend(batch)
                if len(batch) < params["limit"]:
                    break
                params["skip"] += params["limit"]
            return all_objects

        def _row(obj: dict, project: str) -> dict:
            path = obj.get("path", "")
            parts = path.split("/")
            asset_name = parts[-1] if parts else path
            # folder = everything between project and asset name
            folder = "/".join(parts[1:-1]) if len(parts) > 2 else ""
            return {
                "project": project,
                "folder": folder,
                "path": path,
                "asset_name": asset_name,
                "type": obj.get("type", ""),
                "updated_on": obj.get("updateTime", "")[:10] if obj.get("updateTime") else "",
                "updated_by": obj.get("updatedBy", ""),
                "description": obj.get("description") or "",
                "tags": ", ".join(obj.get("tags") or []),
            }

        # Phase 1 — root level
        root_objects = _fetch(project_name)

        folders = [o for o in root_objects if o.get("type") == "Folder"]
        non_folders = [o for o in root_objects if o.get("type") != "Folder" and o.get("type") != "Project"]

        rows = [_row(o, project_name) for o in non_folders]

        # Phase 2 — recurse into each subfolder
        for folder_obj in folders:
            folder_path = folder_obj.get("path", "")
            subfolder_objects = _fetch(folder_path)
            for o in subfolder_objects:
                if o.get("type") not in ("Folder", "Project"):
                    rows.append(_row(o, project_name))
            # One level deeper — nested subfolders
            nested_folders = [o for o in subfolder_objects if o.get("type") == "Folder"]
            for nf in nested_folders:
                for o in _fetch(nf.get("path", "")):
                    if o.get("type") not in ("Folder", "Project"):
                        rows.append(_row(o, project_name))

        rows.sort(key=lambda r: (r["folder"], r["type"], r["asset_name"]))

        return {
            "project": project_name,
            "total_assets": len(rows),
            "assets": rows,
        }

    def get_asset_dependencies(
        self, object_id: str, ref_type: str = "uses", limit: int = 25, skip: int = 0
    ) -> dict:
        url = self._v3_url(
            f"public/core/v3/objects/{object_id}/references"
        )
        params = {"refType": ref_type, "limit": limit, "skip": skip}
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Passwords
    # ------------------------------------------------------------------

    def reset_password(self, user_id: str, security_answer: str, new_password: str) -> dict:
        url = self._v3_url("public/core/v3/Users/ResetPassword")
        resp = requests.post(
            url, headers=self._v3_headers(),
            json={"userId": user_id, "securityAnswer": security_answer, "newPassword": new_password},
        )
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Object Permissions (update + check access)
    # ------------------------------------------------------------------

    def check_object_access(self, object_id: str, asset_type: Optional[str] = None) -> dict:
        path = f"public/core/v3/objects/{object_id}/permissions/checkAccess"
        params = {}
        if asset_type:
            params["type"] = asset_type
        url = self._v3_url(path)
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Projects & Folders (update/delete)
    # ------------------------------------------------------------------

    def update_project(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> dict:
        if project_id:
            url = self._v3_url(f"public/core/v3/projects/{project_id}")
        elif project_name:
            url = self._v3_url(f"public/core/v3/projects/name/{project_name}")
        else:
            raise ValueError("project_id or project_name required")
        payload: dict = {}
        if name:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        resp = requests.patch(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def delete_project(
        self,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> dict:
        if project_id:
            url = self._v3_url(f"public/core/v3/projects/{project_id}")
        elif project_name:
            url = self._v3_url(f"public/core/v3/projects/name/{project_name}")
        else:
            raise ValueError("project_id or project_name required")
        resp = requests.delete(url, headers=self._v3_headers())
        return self._check(resp)

    def update_folder(
        self,
        folder_id: Optional[str] = None,
        folder_name: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> dict:
        if project_id and folder_id:
            url = self._v3_url(f"public/core/v3/projects/{project_id}/folders/{folder_id}")
        elif project_name and folder_name:
            url = self._v3_url(f"public/core/v3/projects/name/{project_name}/folders/name/{folder_name}")
        elif folder_id:
            url = self._v3_url(f"public/core/v3/folders/{folder_id}")
        else:
            raise ValueError("Provide (project_id + folder_id) or (project_name + folder_name) or folder_id")
        payload: dict = {}
        if name:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        resp = requests.patch(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def delete_folder(
        self,
        folder_id: Optional[str] = None,
        folder_name: Optional[str] = None,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> dict:
        if project_id and folder_id:
            url = self._v3_url(f"public/core/v3/projects/{project_id}/folders/{folder_id}")
        elif project_name and folder_name:
            url = self._v3_url(f"public/core/v3/projects/name/{project_name}/folders/name/{folder_name}")
        elif folder_id:
            url = self._v3_url(f"public/core/v3/folders/{folder_id}")
        else:
            raise ValueError("Provide (project_id + folder_id) or (project_name + folder_name) or folder_id")
        resp = requests.delete(url, headers=self._v3_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Export / Import
    # ------------------------------------------------------------------

    def start_export_job(self, name: Optional[str], objects: list) -> dict:
        payload: dict = {"objects": objects}
        if name:
            payload["name"] = name
        url = self._v3_url("public/core/v3/export")
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def get_export_job_status(self, export_id: str, expand_objects: bool = False) -> dict:
        path = f"public/core/v3/export/{export_id}"
        if expand_objects:
            path += "?expand=objects"
        url = self._v3_url(path)
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    def download_export_package(self, export_id: str) -> bytes:
        url = self._v3_url(f"public/core/v3/export/{export_id}/package")
        resp = requests.get(url, headers=self._v3_headers())
        return resp.content

    def upload_import_package(self, file_path: str) -> dict:
        url = self._v3_url("public/core/v3/import/package")
        headers = {
            "INFA-SESSION-ID": self.session.v3_session_id,
            "Accept": "application/json",
        }
        with open(file_path, "rb") as f:
            resp = requests.post(url, headers=headers, files={"package": f})
        return self._check(resp)

    def start_import_job(
        self,
        import_job_id: str,
        name: Optional[str] = None,
        default_conflict_resolution: str = "REUSE",
        include_objects: Optional[list] = None,
    ) -> dict:
        payload: dict = {
            "importSpecification": {
                "defaultConflictResolution": default_conflict_resolution,
            }
        }
        if name:
            payload["name"] = name
        if include_objects:
            payload["importSpecification"]["includeObjects"] = include_objects
        url = self._v3_url(f"public/core/v3/import/{import_job_id}")
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def get_import_job_status(self, import_id: str, expand_objects: bool = False) -> dict:
        path = f"public/core/v3/import/{import_id}"
        if expand_objects:
            path += "?expand=objects"
        url = self._v3_url(path)
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Security Logs
    # ------------------------------------------------------------------

    def get_security_logs(
        self, query: Optional[str] = None, limit: int = 200, skip: int = 0
    ) -> dict:
        params: dict = {"limit": limit, "skip": skip}
        if query:
            params["q"] = query
        url = self._v3_url("public/core/v3/securityLog")
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – IP Addresses
    # ------------------------------------------------------------------

    def get_trusted_ips(self, org_id: str) -> dict:
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/TrustedIP")
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    def update_trusted_ips(
        self, org_id: str, enable_ip: Optional[bool] = None, ip_ranges: Optional[list] = None
    ) -> dict:
        payload: dict = {}
        if enable_ip is not None:
            payload["enableIP"] = enable_ip
        if ip_ranges:
            payload["ipRanges"] = [
                {"startIP": r["start_ip"], "endIP": r["end_ip"]} for r in ip_ranges
            ]
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/TrustedIP")
        resp = requests.put(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Key Rotation
    # ------------------------------------------------------------------

    def get_key_rotation_settings(self) -> dict:
        url = self._v3_url("public/core/v3/key/rotationSettings")
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    def update_key_rotation_settings(self, rotation_interval: str) -> dict:
        url = self._v3_url("public/core/v3/key/rotationSettings")
        resp = requests.patch(
            url, headers=self._v3_headers(), json={"rotationInterval": rotation_interval}
        )
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Sub-org License Management
    # ------------------------------------------------------------------

    def update_sub_org_license(self, org_id: str, payload: dict) -> dict:
        url = self._v3_url(f"public/core/v3/license/org/{org_id}")
        resp = requests.put(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Metering Data
    # ------------------------------------------------------------------

    def start_metering_export(
        self,
        start_date: str,
        end_date: str,
        job_type: str = "SUMMARY",
        all_linked_orgs: bool = False,
        callback_url: Optional[str] = None,
    ) -> dict:
        payload: dict = {
            "startDate": start_date,
            "endDate": end_date,
            "jobType": job_type,
            "allLinkedOrgs": str(all_linked_orgs).upper(),
        }
        if callback_url:
            payload["callbackUrl"] = callback_url
        url = self._v3_url("public/core/v3/license/metering/ExportMeteringData")
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def get_metering_export_status(self, job_id: str) -> dict:
        url = self._v3_url(f"public/core/v3/license/metering/ExportMeteringData/{job_id}")
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    def download_metering_data(self, job_id: str) -> bytes:
        url = self._v3_url(f"public/core/v3/license/metering/ExportMeteringData/{job_id}/download")
        resp = requests.get(url, headers=self._v3_headers())
        return resp.content

    # ------------------------------------------------------------------
    # Platform v3 – Object State Sync (fetchState / loadState)
    # ------------------------------------------------------------------

    def start_fetch_state(self, name: Optional[str], objects: list) -> dict:
        payload: dict = {"objects": objects}
        if name:
            payload["name"] = name
        url = self._v3_url("public/core/v3/fetchState")
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def get_fetch_state_status(self, job_id: str, expand_objects: bool = False) -> dict:
        path = f"public/core/v3/fetchState/{job_id}"
        if expand_objects:
            path += "?expand=objects"
        url = self._v3_url(path)
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    def download_object_states(self, job_id: str) -> bytes:
        url = self._v3_url(f"public/core/v3/fetchState/{job_id}/package")
        resp = requests.get(url, headers=self._v3_headers())
        return resp.content

    def upload_load_state_package(self, file_path: str) -> dict:
        url = self._v3_url("public/core/v3/loadState/package")
        headers = {
            "INFA-SESSION-ID": self.session.v3_session_id,
            "Accept": "application/json",
        }
        with open(file_path, "rb") as f:
            resp = requests.post(url, headers=headers, files={"package": f})
        return self._check(resp)

    def start_load_state(
        self,
        load_job_id: str,
        name: Optional[str] = None,
        include_objects: Optional[list] = None,
    ) -> dict:
        payload: dict = {}
        if name:
            payload["name"] = name
        if include_objects:
            payload["importSpecification"] = {"includeObjects": include_objects}
        url = self._v3_url(f"public/core/v3/loadState/{load_job_id}")
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def get_load_state_status(self, job_id: str, expand_objects: bool = False) -> dict:
        path = f"public/core/v3/loadState/{job_id}"
        if expand_objects:
            path += "?expand=objects"
        url = self._v3_url(path)
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – SAML Group & Role Mappings
    # ------------------------------------------------------------------

    def get_saml_group_mappings(self, org_id: str, query: Optional[str] = None) -> dict:
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/SAMLConfig/groupMappings")
        params = {}
        if query:
            params["q"] = query
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    def get_saml_role_mappings(self, org_id: str, query: Optional[str] = None) -> dict:
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/SAMLConfig/roleMappings")
        params = {}
        if query:
            params["q"] = query
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    def add_saml_group_mappings(
        self, org_id: str, group_mappings: list, reuse_group: bool = False
    ) -> dict:
        payload = {
            "groupMappings": [
                {"roleName": m["role_name"], "samlGroupNames": m["saml_group_names"]}
                for m in group_mappings
            ],
            "reuseGroup": str(reuse_group).lower(),
        }
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/addSamlGroupMappings")
        resp = requests.put(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def add_saml_role_mappings(self, org_id: str, role_mappings: list) -> dict:
        payload = {
            "roleMappings": [
                {"roleName": m["role_name"], "samlRoleNames": m["saml_role_names"]}
                for m in role_mappings
            ]
        }
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/addSamlRoleMappings")
        resp = requests.put(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def remove_saml_group_mappings(self, org_id: str, group_mappings: list) -> dict:
        payload = {
            "groupMappings": [
                {"roleName": m["role_name"], "samlGroupNames": m["saml_group_names"]}
                for m in group_mappings
            ]
        }
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/removeGroupMappings")
        resp = requests.put(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def remove_saml_role_mappings(self, org_id: str, role_mappings: list) -> dict:
        payload = {
            "roleMappings": [
                {"roleName": m["role_name"], "samlRoleNames": m["saml_role_names"]}
                for m in role_mappings
            ]
        }
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/removeSamlRoleMappings")
        resp = requests.put(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Identity Providers
    # ------------------------------------------------------------------

    def register_identity_provider(
        self,
        org_id: str,
        issuer_url: str,
        keys_url: str,
        token_claim: str = "sub",
        match_type: str = "uid",
        signing_algorithm: str = "RS256",
    ) -> dict:
        payload = {
            "type": "OIDC",
            "endPoints": {"issuer": issuer_url, "keys": keys_url},
            "accountPolicy": {"link": {"tokenClaim": token_claim, "matchType": match_type}},
            "signingAlgorithm": signing_algorithm,
        }
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/IdentityProviders")
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def get_identity_providers(self, org_id: str) -> dict:
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/IdentityProviders")
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    def update_identity_provider(self, org_id: str, idp_id: str, payload: dict) -> dict:
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/IdentityProviders/{idp_id}")
        resp = requests.put(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def delete_identity_provider(self, org_id: str, idp_id: str) -> dict:
        url = self._v3_url(f"public/core/v3/Orgs/{org_id}/IdentityProviders/{idp_id}")
        resp = requests.delete(url, headers=self._v3_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – SCIM Tokens
    # ------------------------------------------------------------------

    def list_scim_tokens(self) -> list:
        url = self._v3_url("public/core/v3/scimTokens")
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    def create_scim_token(self) -> dict:
        url = self._v3_url("public/core/v3/scimTokens")
        resp = requests.post(url, headers=self._v3_headers(), json={})
        return self._check(resp)

    def delete_scim_token(self, token_id: str) -> dict:
        url = self._v3_url(f"public/core/v3/scimTokens/{token_id}")
        resp = requests.delete(url, headers=self._v3_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Secure Agent Service (start/stop)
    # ------------------------------------------------------------------

    def manage_secure_agent_service(
        self, agent_id: str, service_name: str, service_action: str
    ) -> dict:
        url = self._v3_url("public/core/v3/agent/service")
        resp = requests.post(
            url,
            headers=self._v3_headers(),
            json={"agentId": agent_id, "serviceName": service_name, "serviceAction": service_action},
        )
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Tags
    # ------------------------------------------------------------------

    def assign_tags(self, tag_assignments: list) -> dict:
        url = self._v3_url("public/core/v3/TagObjects")
        payload = [{"id": a["id"], "tags": a["tags"]} for a in tag_assignments]
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def remove_asset_tags(self, tag_removals: list) -> dict:
        url = self._v3_url("public/core/v3/UntagObjects")
        payload = [{"id": a["id"], "tags": a["tags"]} for a in tag_removals]
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Platform v3 – Source Control
    # ------------------------------------------------------------------

    def pull_objects(self, commit_hash: str, objects: list) -> dict:
        url = self._v3_url("public/core/v3/pull")
        resp = requests.post(
            url, headers=self._v3_headers(),
            json={"commitHash": commit_hash, "objects": objects}
        )
        return self._check(resp)

    def checkout_objects(self, objects: list) -> dict:
        url = self._v3_url("public/core/v3/checkout")
        resp = requests.post(url, headers=self._v3_headers(), json={"objects": objects})
        return self._check(resp)

    def checkin_objects(self, objects: list, summary: str, description: str = "") -> dict:
        url = self._v3_url("public/core/v3/checkin")
        resp = requests.post(
            url, headers=self._v3_headers(),
            json={"objects": objects, "summary": summary, "description": description}
        )
        return self._check(resp)

    def undo_checkout(
        self,
        objects: Optional[list] = None,
        checkout_operation_id: Optional[str] = None,
    ) -> dict:
        payload: dict = {}
        if objects:
            payload["objects"] = objects
        if checkout_operation_id:
            payload["checkoutOperationId"] = checkout_operation_id
        url = self._v3_url("public/core/v3/undoCheckout")
        resp = requests.post(url, headers=self._v3_headers(), json=payload)
        return self._check(resp)

    def compare_object_versions(
        self, asset_id: str, source: str, destination: str, output_format: str = "JSON"
    ) -> dict:
        url = self._v3_url(f"public/core/v3/compare/{asset_id}")
        resp = requests.post(
            url, headers=self._v3_headers(),
            json={"source": source, "destination": destination, "outputFormat": output_format}
        )
        return self._check(resp)

    def get_commit_details(self, commit_hash: str) -> dict:
        url = self._v3_url(f"public/core/v3/commit/{commit_hash}")
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    def get_commit_history(
        self, query: Optional[str] = None, per_page: int = 100, page: int = 1
    ) -> dict:
        params: dict = {"perPage": per_page, "page": page}
        if query:
            params["q"] = query
        url = self._v3_url("public/core/v3/commitHistory")
        resp = requests.get(url, headers=self._v3_headers(), params=params)
        return self._check(resp)

    def get_source_control_action_status(
        self, action_id: str, expand_objects: bool = False
    ) -> dict:
        path = f"public/core/v3/sourceControlAction/{action_id}"
        if expand_objects:
            path += "?expand=objects"
        url = self._v3_url(path)
        resp = requests.get(url, headers=self._v3_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – Connections CRUD
    # ------------------------------------------------------------------

    def create_connection(self, payload: dict) -> dict:
        url = self._frs_url("saas/api/v2/connection")
        resp = requests.post(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    def update_connection(self, connection_id: str, payload: dict, partial: bool = False) -> dict:
        url = self._frs_url(f"saas/api/v2/connection/{connection_id}")
        headers = dict(self._di_headers())
        if partial:
            headers["Update-Mode"] = "PARTIAL"
        resp = requests.post(url, headers=headers, json=payload)
        return self._check(resp)

    def delete_connection(self, connection_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/connection/{connection_id}")
        resp = requests.delete(url, headers=self._di_headers())
        return self._check(resp)

    def test_connection(self, connection_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/connection/test/{connection_id}")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def migrate_connection(
        self, source_conn: str, target_conn: str, project_name: Optional[str] = None
    ) -> dict:
        payload: dict = {"sourceConn": source_conn, "targetConn": target_conn}
        if project_name:
            payload["projectName"] = project_name
        url = self._frs_url("saas/api/v2/connectionMigration/migrate")
        resp = requests.post(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – Connectors metadata
    # ------------------------------------------------------------------

    def list_connectors(self) -> list:
        url = self._frs_url("saas/api/v2/connector")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def get_connector_metadata(self, connector_name: str) -> dict:
        url = self._frs_url(f"saas/api/v2/connector/metadata?connectorName={connector_name}")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – Data Preview
    # ------------------------------------------------------------------

    def get_data_preview(
        self,
        connection_id: str,
        object_name: str,
        direction: str = "source",
        num_rows: int = 10,
    ) -> dict:
        di_id = self._resolve_di_connection_id(connection_id)
        url = self._frs_url(
            f"saas/api/v2/connection/{direction}/{di_id}/datapreview/{object_name}"
        )
        params = {"numRows": num_rows}
        resp = requests.get(url, headers=self._di_headers(), params=params)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – Mappings
    # ------------------------------------------------------------------

    def list_mappings(self) -> list:
        url = self._frs_url("saas/api/v2/mapping")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def get_mapping(
        self, mapping_id: Optional[str] = None, mapping_name: Optional[str] = None
    ) -> dict:
        if mapping_id:
            url = self._frs_url(f"saas/api/v2/mapping/{mapping_id}")
        elif mapping_name:
            url = self._frs_url(f"saas/api/v2/mapping/name/{mapping_name}")
        else:
            raise ValueError("mapping_id or mapping_name required")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def get_mapping_transformations(
        self,
        mapping_id: Optional[str] = None,
        mapping_name: Optional[str] = None,
        transformation_type: Optional[str] = None,
    ) -> dict:
        if mapping_id:
            path = f"saas/api/v2/mapping/additionalTransformationInfo/{mapping_id}"
        elif mapping_name:
            path = f"saas/api/v2/mapping/additionalTransformationInfoByName/{mapping_name}"
        else:
            raise ValueError("mapping_id or mapping_name required")
        params = {}
        if transformation_type:
            params["txType"] = transformation_type
        url = self._frs_url(path)
        resp = requests.get(url, headers=self._di_headers(), params=params)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – Mapping Tasks
    # ------------------------------------------------------------------

    def list_mapping_tasks(self) -> list:
        url = self._frs_url("saas/api/v2/task?type=MTT")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def get_mapping_task(
        self,
        task_id: Optional[str] = None,
        federated_id: Optional[str] = None,
        task_name: Optional[str] = None,
    ) -> dict:
        if task_id:
            url = self._frs_url(f"saas/api/v2/mttask/{task_id}")
        elif federated_id:
            url = self._frs_url(f"saas/api/v2/mttask/frs/{federated_id}")
        elif task_name:
            url = self._frs_url(f"saas/api/v2/mttask/name/{task_name}")
        else:
            raise ValueError("task_id, federated_id, or task_name required")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def create_mapping_task(self, payload: dict) -> dict:
        url = self._frs_url("saas/api/v2/mttask/")
        resp = requests.post(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    def update_mapping_task(
        self,
        payload: dict,
        task_id: Optional[str] = None,
        federated_id: Optional[str] = None,
        partial: bool = False,
    ) -> dict:
        if task_id:
            url = self._frs_url(f"saas/api/v2/mttask/{task_id}")
        elif federated_id:
            url = self._frs_url(f"saas/api/v2/mttask/frs/{federated_id}")
        else:
            raise ValueError("task_id or federated_id required")
        headers = dict(self._di_headers())
        if partial:
            headers["Update-Mode"] = "PARTIAL"
        resp = requests.post(url, headers=headers, json=payload)
        return self._check(resp)

    def delete_mapping_task(self, task_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/mttask/{task_id}")
        resp = requests.delete(url, headers=self._di_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – Linear Taskflows
    # ------------------------------------------------------------------

    def list_linear_taskflows(self) -> list:
        url = self._frs_url("saas/api/v2/workflow")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def get_linear_taskflow(
        self, workflow_id: Optional[str] = None, workflow_name: Optional[str] = None
    ) -> dict:
        if workflow_id:
            url = self._frs_url(f"saas/api/v2/workflow/{workflow_id}")
        elif workflow_name:
            url = self._frs_url(f"saas/api/v2/workflow/name/{workflow_name}")
        else:
            raise ValueError("workflow_id or workflow_name required")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def create_linear_taskflow(self, payload: dict) -> dict:
        url = self._frs_url("saas/api/v2/workflow")
        resp = requests.post(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    def update_linear_taskflow(self, workflow_id: str, payload: dict) -> dict:
        url = self._frs_url(f"saas/api/v2/workflow/{workflow_id}")
        resp = requests.post(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    def delete_linear_taskflow(self, workflow_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/workflow/{workflow_id}")
        resp = requests.delete(url, headers=self._di_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – Published Taskflows (active-bpel)
    # ------------------------------------------------------------------

    def get_taskflow_status(self, run_id: str, subtask_details: bool = False) -> dict:
        detail_param = "Yes" if subtask_details else "No"
        url = self._frs_url(
            f"active-bpel/services/tf/status/{run_id}?subtaskDetails={detail_param}"
        )
        resp = requests.get(url, headers=self._headers())
        return self._check(resp)

    def publish_taskflows(self, asset_paths: list) -> dict:
        url = self._frs_url("active-bpel/asset/v1/publish")
        headers = {
            "IDS-SESSION-ID": self.session.session_id,
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
        }
        payload = {"data": {"type": "publish", "attributes": {"assetPaths": asset_paths}}}
        resp = requests.post(url, headers=headers, json=payload)
        return self._check(resp)

    def unpublish_taskflows(self, asset_paths: list) -> dict:
        url = self._frs_url("active-bpel/asset/v1/unpublish")
        headers = {
            "IDS-SESSION-ID": self.session.session_id,
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
        }
        payload = {"data": {"type": "unpublish", "attributes": {"assetPaths": asset_paths}}}
        resp = requests.post(url, headers=headers, json=payload)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – Expression Validation
    # ------------------------------------------------------------------

    def validate_expression(
        self, expression: str, connection_id: str, object_name: str, is_source_type: bool = True
    ) -> dict:
        di_id = self._resolve_di_connection_id(connection_id)
        url = self._frs_url("saas/api/v2/expression/validate")
        resp = requests.post(
            url,
            headers=self._di_headers(),
            json={
                "@type": "expressionValidation",
                "expr": expression,
                "connectionId": di_id,
                "objectName": object_name,
                "isSourceType": is_source_type,
            },
        )
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – Operational Insights Job Log Entries
    # ------------------------------------------------------------------

    def get_di_job_log_entries(
        self,
        org_id: str,
        filter_str: Optional[str] = None,
        list_filter: Optional[str] = None,
        top: int = 500,
        skip: int = 0,
    ) -> dict:
        base = self._frs_url(
            f"cdiinsights-service/api/v1/analytical/Orgs({org_id})/JobLogEntries"
        )
        params: dict = {"$top": top, "$skip": skip, "$count": "true"}
        if filter_str:
            params["$filter"] = filter_str
        if list_filter:
            params["listFilter"] = list_filter
        resp = requests.get(base, headers=self._headers(), params=params)
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – Fixed-Width Configuration
    # ------------------------------------------------------------------

    def list_fwconfigs(self) -> list:
        url = self._frs_url("saas/api/v2/fwConfig")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def get_fwconfig(
        self, fwconfig_id: Optional[str] = None, fwconfig_name: Optional[str] = None
    ) -> dict:
        if fwconfig_id:
            url = self._frs_url(f"saas/api/v2/fwConfig/{fwconfig_id}")
        elif fwconfig_name:
            url = self._frs_url(f"saas/api/v2/fwConfig/name/{fwconfig_name}")
        else:
            raise ValueError("fwconfig_id or fwconfig_name required")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def create_fwconfig(self, payload: dict) -> dict:
        url = self._frs_url("saas/api/v2/fwConfig")
        resp = requests.post(url, headers=self._di_headers(), json=payload)
        return self._check(resp)

    def delete_fwconfig(self, fwconfig_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/fwConfig/{fwconfig_id}")
        resp = requests.delete(url, headers=self._di_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Integration – PowerCenter Mapplets
    # ------------------------------------------------------------------

    def list_pc_mapplets(self) -> list:
        url = self._frs_url("saas/api/v2/customFunc")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def get_pc_mapplet(
        self, mapplet_id: Optional[str] = None, mapplet_name: Optional[str] = None
    ) -> dict:
        if mapplet_id:
            url = self._frs_url(f"saas/api/v2/customFunc/{mapplet_id}")
        elif mapplet_name:
            url = self._frs_url(f"saas/api/v2/customFunc/name/{mapplet_name}")
        else:
            raise ValueError("mapplet_id or mapplet_name required")
        resp = requests.get(url, headers=self._di_headers())
        return self._check(resp)

    def delete_pc_mapplet(self, mapplet_id: str) -> dict:
        url = self._frs_url(f"saas/api/v2/customFunc/{mapplet_id}")
        resp = requests.delete(url, headers=self._di_headers())
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Ingestion & Replication – DBMI / APPMI Tasks
    # ------------------------------------------------------------------

    def _ing_headers(self) -> dict:
        """Headers for ingestion service (IDS-SESSION-ID)."""
        return {
            "IDS-SESSION-ID": self.session.session_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _ing_url(self, path: str) -> str:
        """Build URL for ingestion APIs using the frs base URL."""
        return self._frs_url(path)

    def create_ingestion_task(self, payload: dict) -> dict:
        url = self._ing_url("dbmi/public/api/v2/task/create")
        resp = requests.post(url, headers=self._ing_headers(), json=payload)
        return self._check(resp)

    def get_ingestion_task_id(
        self,
        task_name: str,
        project_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        page_no: int = 0,
        page_size: int = 25,
    ) -> dict:
        params: dict = {"taskName": task_name, "pageNo": page_no, "pageSize": page_size}
        if project_id:
            params["projectId"] = project_id
        if folder_id:
            params["folderId"] = folder_id
        url = self._ing_url("dbmi/public/api/v2/task/fetchId")
        resp = requests.get(url, headers=self._ing_headers(), params=params)
        return self._check(resp)

    def deploy_ingestion_task(self, task_id: int) -> dict:
        url = self._ing_url(f"dbmi/public/api/v2/task/deploy/{task_id}")
        resp = requests.post(url, headers=self._ing_headers(), json={})
        return self._check(resp)

    def get_ingestion_task_details(
        self,
        task_id: Optional[int] = None,
        project_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        page_no: int = 0,
        page_size: int = 25,
        order_by: Optional[str] = None,
    ) -> dict:
        params: dict = {"pageNo": page_no, "pageSize": page_size}
        if task_id:
            params["taskId"] = task_id
        if project_id:
            params["projectId"] = project_id
        if folder_id:
            params["folderId"] = folder_id
        if order_by:
            params["orderBy"] = order_by
        url = self._ing_url("dbmi/public/api/v2/task/details")
        resp = requests.get(url, headers=self._ing_headers(), params=params)
        return self._check(resp)

    def _get_ingestion_job_id_for_task(self, task_id: int) -> int:
        url = self._ing_url(f"dbmi/public/api/v2/task/fetch/{task_id}/job")
        resp = requests.get(url, headers=self._ing_headers())
        data = self._check(resp)
        return data["jobId"]

    def start_ingestion_job(self, job_id: int) -> dict:
        url = self._ing_url("dbmi/public/api/v2/job/start")
        resp = requests.post(url, headers=self._ing_headers(), json={"jobId": str(job_id)})
        return self._check(resp)

    def stop_ingestion_job(self, job_id: int) -> dict:
        url = self._ing_url("dbmi/public/api/v2/job/stop")
        resp = requests.post(url, headers=self._ing_headers(), json={"jobId": str(job_id)})
        return self._check(resp)

    def resume_ingestion_job(self, job_id: int, resume_options: Optional[dict] = None) -> dict:
        payload: dict = {"jobId": job_id, "parameters": {"resumeOptions": resume_options}}
        url = self._ing_url("dbmi/public/api/v2/job/resume")
        resp = requests.post(url, headers=self._ing_headers(), json=payload)
        return self._check(resp)

    def undeploy_ingestion_job(self, job_id: int) -> dict:
        url = self._ing_url("dbmi/public/api/v2/job/undeploy")
        resp = requests.post(url, headers=self._ing_headers(), json={"jobId": str(job_id)})
        return self._check(resp)

    def get_ingestion_job_status(self, job_id: int) -> dict:
        url = self._ing_url("dbmi/public/api/v2/job/status")
        resp = requests.post(url, headers=self._ing_headers(), json={"jobId": str(job_id)})
        return self._check(resp)

    def get_ingestion_job_metrics(
        self,
        job_id: int,
        state_filter: Optional[str] = None,
        sort: Optional[list] = None,
        search: str = "",
        limit: int = 25,
        offset: int = 0,
    ) -> dict:
        metrics_options: dict = {
            "stateFilter": state_filter,
            "sort": sort or ["srcTable", "asc"],
            "search": search,
            "limit": limit,
            "offset": offset,
        }
        url = self._ing_url("dbmi/public/api/v2/job/metrics")
        resp = requests.post(
            url, headers=self._ing_headers(),
            json={"jobId": job_id, "parameters": {"metricsOptions": metrics_options}}
        )
        return self._check(resp)

    # ------------------------------------------------------------------
    # Data Ingestion & Replication – File Ingestion (MI Tasks)
    # ------------------------------------------------------------------

    def run_mi_task_job(
        self, task_id: str, task_name: Optional[str] = None, parameters: Optional[dict] = None
    ) -> dict:
        payload: dict = {"taskId": task_id}
        if task_name:
            payload["taskName"] = task_name
        if parameters:
            payload["parameters"] = parameters
        url = self._frs_url("mftsaas/api/v1/job")
        resp = requests.post(url, headers=self._ing_headers(), json=payload)
        return self._check(resp)

    def get_mi_task_job_status(self, run_id: str) -> dict:
        url = self._frs_url(f"mftsaas/api/v1/job/{run_id}/status")
        resp = requests.get(url, headers=self._ing_headers())
        return self._check(resp)

    def get_mi_activity_log(
        self,
        task_id: Optional[str] = None,
        run_id: Optional[str] = None,
        offset: int = 0,
        row_limit: int = 25,
        job_type: str = "all",
        fetch_file_events: bool = False,
        file_events_limit: int = 100,
    ) -> dict:
        params: dict = {"offset": offset, "rowLimit": row_limit, "jobType": job_type}
        if task_id:
            params["taskId"] = task_id
        if run_id:
            params["runId"] = run_id
        if fetch_file_events:
            params["fetchFileEvents"] = "true"
            params["fileEventsLimit"] = file_events_limit
        url = self._frs_url("mftsaas/api/v2/mitasks/activityLog")
        resp = requests.get(url, headers=self._ing_headers(), params=params)
        return self._check(resp)

    def list_mi_tasks(self) -> dict:
        url = self._frs_url("mftsaas/api/v1/mitasks")
        resp = requests.get(url, headers=self._ing_headers())
        return self._check(resp)

    def create_mi_task(self, payload: dict) -> dict:
        url = self._frs_url("mftsaas/api/v1/mitasks")
        resp = requests.post(url, headers=self._ing_headers(), json=payload)
        return self._check(resp)

    def update_mi_task(self, task_id: str, payload: dict) -> dict:
        url = self._frs_url(f"mftsaas/api/v1/mitasks/{task_id}")
        resp = requests.put(url, headers=self._ing_headers(), json=payload)
        return self._check(resp)

    def delete_mi_task(self, task_id: str) -> dict:
        url = self._frs_url(f"mftsaas/api/v1/mitasks/{task_id}")
        resp = requests.delete(url, headers=self._ing_headers())
        return self._check(resp)

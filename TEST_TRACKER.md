# IDMC REST API MCP Server — Test Tracker

**Pod:** EM | **Org:** 010WXI | **User:** sucherukuri@informatica.com  
**Session Date:** 2026-06-16

---

## ✅ Completed Tests

### 1. `idmc_login`
- **Query:** `{ "pod_region": "em" }`
- **Result:** ✅ Logged in — session_id: `90IA5f29ECQiIhXbxGD0my`, base_url: `emw1-dqprofile.dm-em.informaticacloud.com`

### 1b. `idmc_login` *(Session 2 — 2026-06-16)*
- **Query:** `{ "pod_region": "em" }`
- **Result:** ✅ Logged in — session_id: `jBFpO5eSzExdFMqJ81m1uo`, base_url: `emw1-dqprofile.dm-em.informaticacloud.com`, org: `010WXI`

---

### 2. `idmc_get_users`
- **Query:** `{ "limit": 100 }`
- **Result:** ✅ Returned 88 users. All Native auth. States: 62 Enabled, 15 Disabled, 7 Provisioned, 1 Locked.

---

### 3. `idmc_get_user`
- **Query:** `{ "user_id": "tujain@informatica.com" }`
- **Result:** ✅ Returned full user details — Tushar Jain, Disabled, last login 2025-10-03, group: GCS_DQ, no roles.

---

### 4. `idmc_delete_user`
- **Query:** `{ "user_id": "7vv2HKGlzyfgpFlM2Dbvwr" }` (tujain@informatica.com)
- **Result:** ✅ HTTP 204 — User permanently deleted.

---

### 5. `idmc_get_user_groups`
- **Query:** `{ "limit": 100 }`
- **Result:** ✅ Returned 17 user groups. Largest: GCS_DQ (47 users, 33 roles). 6 groups have no roles.

---

### 6. `idmc_add_users_to_group`
- **Query:** `{ "group_id": "axRzV0QmfDwd1q0lBPn4QH", "users": ["sucherukuri@informatica.com"] }`
- **Result:** ✅ HTTP 204 — User added to Admin Group.

---

### 7. `idmc_remove_users_from_group`
- **Query:** `{ "group_id": "axRzV0QmfDwd1q0lBPn4QH", "users": ["sucherukuri@informatica.com"] }`
- **Result:** ✅ HTTP 204 — User removed from Admin Group.

---

### 8. `idmc_get_roles` — List all roles
- **Query:** `{ "limit": 200 }`
- **Result:** ✅ Returned 108 roles. 33 system roles, 75 custom roles. All Enabled.

---

### 9. `idmc_get_roles` — With expand=privileges (specific role)
- **Query:** `{ "query": "roleName==\"04927608_import\"", "expand": "privileges" }`
- **Result:** ✅ Returned role with 25 privileges across Admin, Profile, DQ services.

---

### 10. `idmc_get_roles` — Bulk expand without q= filter
- **Query:** `{ "limit": 200, "expand": "privileges" }`
- **Result:** ❌ HTTP 400 — API requires `q=` filter when using `expand=privileges`. Known API constraint — tool description updated.

---

### 11. `idmc_get_roles` — Find roles with disableDataValueStorage (108 calls)
- **Query:** `{ "query": "roleName==\"<each role>\"", "expand": "privileges" }` × 108
- **Result:** ✅ 8 roles found with `PROFILE.disableDataValueStorage`: arani_dq_ro_test_role, Customer_role_diable_data_value, Data_Prof_previewer, Disable_Data_Value_Storage, disable_data_value_storage_dnara, SophosDQFull, TEST_SC, testrole_syed.

---

## 🔲 Pending Tests

### User Management
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_create_user` | `{ "name": "testuser", "first_name": "Test", "last_name": "User", "email": "test@example.com", "roles": ["<role_id>"] }` | Create then delete |
| `idmc_add_user_roles` | `{ "user_id": "<id>", "roles": ["<role_id>"] }` | Add role to user |
| `idmc_remove_user_roles` | `{ "user_id": "<id>", "roles": ["<role_id>"] }` | Remove role from user |
| `idmc_add_user_groups` | `{ "user_id": "<id>", "groups": ["<group_id>"] }` | Add user to group via user endpoint |
| `idmc_remove_user_groups` | `{ "user_id": "<id>", "groups": ["<group_id>"] }` | Remove user from group via user endpoint |
| `idmc_change_password` | `{ "old_password": "...", "new_password": "..." }` | Session-based, no username needed |
| `idmc_reset_password` | `{ "user_id": "<id>", "security_answer": "...", "new_password": "..." }` | For expired/forgotten passwords |

### User Groups
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_get_user_group` | `{ "group_name": "Admin Group" }` | Test name-based lookup |
| `idmc_create_user_group` | `{ "name": "Test_Group", "roles": ["<role_id>"] }` | roles is required |
| `idmc_add_roles_to_group` | `{ "group_name": "Test_Group", "roles": ["Designer"] }` | Test name-based |
| `idmc_remove_roles_from_group` | `{ "group_name": "Test_Group", "roles": ["Designer"] }` | |
| `idmc_delete_user_group` | `{ "group_name": "Test_Group" }` | Test name-based delete |

### Roles & Privileges
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_get_privileges` | `{}` | Default — enabled only |
| `idmc_get_privileges` | `{ "query": "status==All" }` | All including disabled/unassigned |
| `idmc_create_role` | `{ "name": "Test_Role_sunil", "privileges": ["<priv_id>"] }` | |
| `idmc_add_role_privileges` | `{ "role_name": "Test_Role_sunil", "privileges": ["<priv_name>"] }` | Test name-based |
| `idmc_remove_role_privileges` | `{ "role_name": "Test_Role_sunil", "privileges": ["<priv_name>"] }` | |
| `idmc_delete_role` | `{ "role_name": "Test_Role_sunil" }` | Test name-based delete |

### Connections
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_list_connections` | `{}` | ✅ Tested — fetched `cn_oracle_sucherukrib` by name |
| `idmc_test_connection` | `{ "connection_id": "010WXI0B0000000000HF" }` | ✅ Tested — `cn_oracle_sucherukrib` passed |
| `idmc_create_connection` | `{ "name": "cn_oracle_sucherukric", "type": "Oracle", ... }` | ✅ Tested — created Oracle connection ID `010WXI0B0000000000LT` |
| `idmc_update_connection` | `{ ... }` | |
| `idmc_delete_connection` | `{ "connection_id": "<id>" }` | |
| `idmc_migrate_connection` | `{ ... }` | |

### Projects & Folders
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_list_projects` | `{}` | ✅ Tested — returned 552 projects (first 50 shown, paginated) |
| `idmc_list_projects` | `{ "name": "SUCHERUKURI" }` | ✅ Tested — returned project ID `kzWAOFV4rMpcNZIo9uNPOy`, 10 subfolders |
| `idmc_create_project` | `{ "name": "Test_Project_sunil" }` | |
| `idmc_update_project` | `{ "project_id": "<id>", ... }` | |
| `idmc_list_folders` | `{ "project_id": "<id>" }` | |
| `idmc_create_folder` | `{ "name": "Test_Folder", "project_id": "<id>" }` | |
| `idmc_update_folder` | `{ ... }` | |
| `idmc_delete_folder` | `{ "folder_id": "<id>" }` | |
| `idmc_delete_project` | `{ "project_id": "<id>" }` | |

### Runtime Environments & Agents
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_get_runtime_environments` | `{}` | |
| `idmc_get_secure_agents` | `{}` | ✅ Tested |
| `idmc_get_secure_agents` | `{ "agent_name": "invpanaceamax01.informatica.com" }` | ✅ Tested — name lookup |
| `idmc_get_secure_agents` | `{ "agent_id": "...", "include_service_details": true, "only_status": false }` | ✅ Tested — service status |
| `idmc_get_agent_installer_info` | `{}` | |
| `idmc_manage_secure_agent_service` | `{ ... }` | |
| `idmc_create_runtime_environment` | `{ ... }` | |
| `idmc_update_runtime_environment` | `{ ... }` | |
| `idmc_delete_runtime_environment` | `{ ... }` | |
| `idmc_delete_secure_agent` | `{ ... }` | |

### Data Profiling
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_list_profiles` | `{}` | |
| `idmc_get_profile` | `{ "profile_id": "<id>" }` | |
| `idmc_create_profile` | `{ ... }` | |
| `idmc_update_profile` | `{ ... }` | |
| `idmc_run_profile` | `{ "profile_id": "<id>" }` | |
| `idmc_delete_profile` | `{ "profile_id": "<id>" }` | |
| `idmc_list_columns` | `{ "profile_id": "<id>" }` | |
| `idmc_get_column` | `{ ... }` | |
| `idmc_get_value_frequencies` | `{ ... }` | |
| `idmc_get_column_datatypes` | `{ ... }` | |
| `idmc_get_column_patterns` | `{ ... }` | |
| `idmc_export_profile_results` | `{ "profile_id": "<id>" }` | |
| `idmc_get_top_n_runs` | `{ ... }` | |
| `idmc_get_top_n_profile_tasks` | `{ ... }` | |

### DI Jobs & Tasks
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_get_di_tasks` | `{}` | |
| `idmc_get_running_jobs` | `{}` | |
| `idmc_start_di_job` | `{ "task_id": "<id>" }` | |
| `idmc_stop_di_job` | `{ "task_id": "<id>" }` | |
| `idmc_get_job` | `{ "task_id": "<id>" }` | |
| `idmc_resume_job` | `{ "task_id": "<id>" }` | |
| `idmc_get_activity_log` | `{}` | |
| `idmc_get_activity_monitor` | `{}` | |
| `idmc_get_session_logs` | `{ ... }` | |
| `idmc_get_error_log` | `{ ... }` | |
| `idmc_get_di_job_log_entries` | `{ ... }` | |

### Schedules
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_get_schedules` | `{}` | |
| `idmc_create_schedule` | `{ "name": "Test_Schedule", ... }` | |
| `idmc_update_schedule` | `{ ... }` | |
| `idmc_delete_schedule` | `{ "schedule_id": "<id>" }` | |

### Mapping Tasks & Taskflows
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_list_mapping_tasks` | `{}` | |
| `idmc_get_mapping_task` | `{ "task_id": "<id>" }` | |
| `idmc_create_mapping_task` | `{ ... }` | |
| `idmc_update_mapping_task` | `{ ... }` | |
| `idmc_delete_mapping_task` | `{ "task_id": "<id>" }` | |
| `idmc_list_linear_taskflows` | `{}` | |
| `idmc_get_linear_taskflow` | `{ "taskflow_id": "<id>" }` | |
| `idmc_create_linear_taskflow` | `{ ... }` | |
| `idmc_update_linear_taskflow` | `{ ... }` | |
| `idmc_delete_linear_taskflow` | `{ "taskflow_id": "<id>" }` | |
| `idmc_publish_taskflows` | `{ ... }` | |
| `idmc_unpublish_taskflows` | `{ ... }` | |
| `idmc_get_taskflow_status` | `{ ... }` | |

### MI Tasks & Ingestion
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_list_mi_tasks` | `{}` | |
| `idmc_get_mi_task_job_status` | `{ ... }` | |
| `idmc_create_mi_task` | `{ ... }` | |
| `idmc_update_mi_task` | `{ ... }` | |
| `idmc_run_mi_task_job` | `{ ... }` | |
| `idmc_delete_mi_task` | `{ ... }` | |
| `idmc_get_ingestion_task_details` | `{ ... }` | |
| `idmc_start_ingestion_job` | `{ ... }` | |
| `idmc_stop_ingestion_job` | `{ ... }` | |
| `idmc_get_ingestion_job_status` | `{ ... }` | |
| `idmc_get_ingestion_job_metrics` | `{ ... }` | |

### Organization & Licensing
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_get_organization` | `{}` | |
| `idmc_get_organization_details` | `{}` | ✅ Tested — returned org 010WXI with 6 sub-orgs |
| `idmc_get_organization_details` | `{ "org_id": "011GAR" }` | ✅ Tested — sub-org GCS_DQ_CLOUD_EU_CDI_ADVANCE |
| `idmc_update_organization` | `{ ... }` | |
| `idmc_get_license` | `{}` | |
| `idmc_create_sub_organization` | `{ ... }` | |
| `idmc_delete_sub_organization` | `{ ... }` | |
| `idmc_update_sub_org_license` | `{ ... }` | |

### Audit, Security & Misc
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_get_audit_log` | `{}` | |
| `idmc_get_security_logs` | `{}` | Requires Admin role |
| `idmc_get_trusted_ips` | `{}` | |
| `idmc_update_trusted_ips` | `{ ... }` | |
| `idmc_get_server_time` | `{}` | |
| `idmc_validate_session` | `{}` | |
| `idmc_get_insights` | `{}` | |
| `idmc_update_insights` | `{ ... }` | |
| `idmc_get_metering_export_status` | `{ ... }` | |
| `idmc_download_metering_data` | `{ ... }` | |

### Source Control / Import-Export
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_start_export_job` | `{ ... }` | |
| `idmc_get_export_job_status` | `{ "job_id": "<id>" }` | |
| `idmc_download_export_package` | `{ "job_id": "<id>" }` | |
| `idmc_upload_import_package` | `{ ... }` | |
| `idmc_start_import_job` | `{ ... }` | |
| `idmc_get_import_job_status` | `{ "job_id": "<id>" }` | |
| `idmc_checkout_objects` | `{ ... }` | |
| `idmc_checkin_objects` | `{ ... }` | |
| `idmc_undo_checkout` | `{ ... }` | |
| `idmc_pull_objects` | `{ ... }` | |
| `idmc_get_commit_history` | `{ ... }` | |
| `idmc_compare_object_versions` | `{ ... }` | |

### Object Permissions & Assets
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_get_object_permissions` | `{ "object_id": "<id>" }` | |
| `idmc_create_object_permission` | `{ ... }` | |
| `idmc_update_object_permission` | `{ ... }` | |
| `idmc_delete_object_permission` | `{ ... }` | |
| `idmc_check_object_access` | `{ "object_id": "<id>" }` | |
| `idmc_list_assets` | `{}` | |
| `idmc_list_project_assets` | `{ "project_name": "SUCHERUKURI" }` | ✅ Tested — returned 116 assets across 10 folders (DMAPPLET, RULE_SPECIFICATION, PROFILE, DICTIONARY, APIM_API, etc.) |
| `idmc_assign_tags` | `{ ... }` | |
| `idmc_remove_asset_tags` | `{ ... }` | |
| `idmc_lookup_object` | `{ ... }` | |
| `idmc_get_asset_dependencies` | `{ "object_id": "<id>" }` | |

### SAML & Identity Providers
| Tool | Suggested Query | Notes |
|------|----------------|-------|
| `idmc_get_identity_providers` | `{}` | |
| `idmc_register_identity_provider` | `{ ... }` | |
| `idmc_update_identity_provider` | `{ ... }` | |
| `idmc_delete_identity_provider` | `{ ... }` | |
| `idmc_get_saml_group_mappings` | `{ "org_id": "azLMvNUOHCijD6tzD3fZE5" }` | |
| `idmc_get_saml_role_mappings` | `{ "org_id": "azLMvNUOHCijD6tzD3fZE5" }` | |
| `idmc_add_saml_group_mappings` | `{ ... }` | |
| `idmc_add_saml_role_mappings` | `{ ... }` | |
| `idmc_remove_saml_group_mappings` | `{ ... }` | |
| `idmc_remove_saml_role_mappings` | `{ ... }` | |

---

## Code Fixes Applied This Session

| Area | Fix | Files Changed |
|------|-----|--------------|
| User Groups | `limit`/`skip` not passed to API in `get_user_groups()` | api_client.py, tool_executor.py |
| User Groups | `roles` missing from required in `idmc_create_user_group` | tools.py |
| User Groups | User names vs IDs in add/remove users tools | tools.py |
| User Groups | Added `group_name` alternative to all group tools | tools.py, api_client.py, tool_executor.py |
| Change Password | Removed `username` from payload (session-based per doc) | tools.py, api_client.py, tool_executor.py |
| Privileges | Added `query` param to `idmc_get_privileges` | tools.py, api_client.py, tool_executor.py |
| Roles | `limit`/`offset` not passed to API in `get_roles()` | api_client.py, tool_executor.py |
| Roles | Added `role_name` alternative to add/remove privileges and delete | tools.py, api_client.py, tool_executor.py |
| Roles | Updated tool description: `expand` requires `q=` filter | tools.py |
| Secure Agents | Wrong header (`IDS-SESSION-ID` → `icSessionId`) and missing `saas/` URL prefix in `get_secure_agents()` | api_client.py |
| Secure Agents | Added `agent_name`, `include_unassigned_only`, `basic_info`, `include_service_details`, `only_status` params | tools.py, api_client.py, tool_executor.py |
| Secure Agents | Enriched `idmc_manage_secure_agent_service` description with all 11 response `serviceState` values | tools.py |
| Projects | **Critical** — `list_projects`, `create_project`, `list_folders`, `create_folder` were using wrong FRS API (`frs/v1/`) instead of `public/core/v3/` | api_client.py |
| Projects | Wrong headers (`_headers()` → `_v3_headers()`) for all project/folder ops | api_client.py |
| Projects | `create_folder` required `project_id` — doc allows Default project (no project needed) | tools.py, api_client.py, tool_executor.py |
| Projects | `list_folders` missing `project_name` alternative | tools.py, api_client.py, tool_executor.py |
| Folders | `update_folder`/`delete_folder` missing `project_name` + `folder_name` name-based URI support (doc: `/projects/name/<p>/folders/name/<f>`) | tools.py, api_client.py, tool_executor.py |
| Projects | `idmc_create_project` description said "profiling tasks" — updated to "assets. Max 500 per org" | tools.py |
| Object Permissions | `idmc_get_object_permissions` missing `acl_id` param (doc supports GET by specific ACL ID) | tools.py, api_client.py, tool_executor.py |
| Object Permissions | `idmc_create_object_permission` used opaque `payload` blob — replaced with explicit `principal_type`, `principal_name`, `read`, `update`, `delete`, `execute`, `change_permission` fields | tools.py, api_client.py, tool_executor.py |
| Object Permissions | `idmc_update_object_permission` same opaque payload + wrong param name `permission_id` → `acl_id` | tools.py, api_client.py, tool_executor.py |
| Object Permissions | **Critical** — `idmc_delete_object_permission` sent ACL ID in request body; doc requires it in URL path (`/permissions/<acl_id>`) | tools.py, api_client.py, tool_executor.py |

import sys
sys.path.insert(0, '.')
from shared.tools import TOOLS

categories = {
    'Authentication': ['idmc_login','idmc_logout','idmc_logout_all_sessions','idmc_validate_session','idmc_change_password'],
    'Users': ['idmc_get_users','idmc_get_user','idmc_create_user','idmc_delete_user','idmc_reset_password'],
    'User Groups': ['idmc_get_user_groups','idmc_get_user_group','idmc_create_user_group','idmc_delete_user_group','idmc_add_user_groups','idmc_remove_user_groups','idmc_add_users_to_group','idmc_remove_users_from_group'],
    'User Roles': ['idmc_add_user_roles','idmc_remove_user_roles'],
    'Roles & Privileges': ['idmc_get_roles','idmc_create_role','idmc_delete_role','idmc_get_privileges','idmc_add_role_privileges','idmc_remove_role_privileges','idmc_add_roles_to_group','idmc_remove_roles_from_group'],
    'SAML / Identity Providers': ['idmc_get_identity_providers','idmc_register_identity_provider','idmc_update_identity_provider','idmc_delete_identity_provider','idmc_get_saml_group_mappings','idmc_add_saml_group_mappings','idmc_remove_saml_group_mappings','idmc_get_saml_role_mappings','idmc_add_saml_role_mappings','idmc_remove_saml_role_mappings'],
    'Organization': ['idmc_get_organization','idmc_get_organization_details','idmc_update_organization','idmc_create_sub_organization','idmc_delete_sub_organization','idmc_update_sub_org_license','idmc_get_license','idmc_get_trusted_ips','idmc_update_trusted_ips','idmc_get_key_rotation_settings','idmc_update_key_rotation_settings','idmc_get_audit_log','idmc_get_security_logs','idmc_get_server_time'],
    'SCIM Tokens': ['idmc_list_scim_tokens','idmc_create_scim_token','idmc_delete_scim_token'],
    'Secure Agents': ['idmc_get_secure_agents','idmc_delete_secure_agent','idmc_manage_secure_agent_service','idmc_get_agent_installer_info'],
    'Runtime Environments': ['idmc_get_runtime_environments','idmc_create_runtime_environment','idmc_update_runtime_environment','idmc_delete_runtime_environment','idmc_get_runtime_environment_selections','idmc_update_runtime_environment_selections'],
    'Connections': ['idmc_list_connections','idmc_create_connection','idmc_update_connection','idmc_delete_connection','idmc_test_connection','idmc_migrate_connection','idmc_list_connectors','idmc_get_connector_metadata','idmc_get_connection_objects'],
    'Projects & Folders': ['idmc_list_projects','idmc_create_project','idmc_update_project','idmc_delete_project','idmc_list_folders','idmc_create_folder','idmc_update_folder','idmc_delete_folder','idmc_list_project_assets','idmc_list_assets'],
    'Schedules': ['idmc_get_schedules','idmc_create_schedule','idmc_update_schedule','idmc_delete_schedule'],
    'Mappings & Tasks': ['idmc_list_mappings','idmc_get_mapping','idmc_get_mapping_transformations','idmc_list_mapping_tasks','idmc_get_mapping_task','idmc_create_mapping_task','idmc_update_mapping_task','idmc_delete_mapping_task','idmc_list_pc_mapplets','idmc_get_pc_mapplet','idmc_delete_pc_mapplet'],
    'DI Jobs & Activity': ['idmc_get_di_tasks','idmc_start_di_job','idmc_stop_di_job','idmc_get_di_job_log_entries','idmc_get_job','idmc_get_running_jobs','idmc_stop_job','idmc_resume_job','idmc_get_activity_log','idmc_get_activity_monitor','idmc_get_run_detail','idmc_list_run_details','idmc_delete_run_details','idmc_get_top_n_runs','idmc_get_session_log','idmc_get_session_logs','idmc_get_error_log'],
    'Taskflows': ['idmc_list_linear_taskflows','idmc_get_linear_taskflow','idmc_create_linear_taskflow','idmc_update_linear_taskflow','idmc_delete_linear_taskflow','idmc_publish_taskflows','idmc_unpublish_taskflows','idmc_get_taskflow_status'],
    'Mass Ingestion': ['idmc_list_mi_tasks','idmc_create_mi_task','idmc_update_mi_task','idmc_delete_mi_task','idmc_run_mi_task_job','idmc_get_mi_task_job_status','idmc_get_mi_activity_log'],
    'Ingestion / CDC': ['idmc_get_ingestion_task_id','idmc_get_ingestion_task_details','idmc_create_ingestion_task','idmc_deploy_ingestion_task','idmc_undeploy_ingestion_job','idmc_start_ingestion_job','idmc_stop_ingestion_job','idmc_resume_ingestion_job','idmc_get_ingestion_job_status','idmc_get_ingestion_job_metrics'],
    'Data Profiling': ['idmc_list_profiles','idmc_get_profile','idmc_create_profile','idmc_update_profile','idmc_delete_profile','idmc_run_profile','idmc_suggest_profile_name','idmc_get_top_n_profile_tasks','idmc_export_profile_results','idmc_get_column','idmc_list_columns','idmc_get_column_datatypes','idmc_get_column_patterns','idmc_get_value_frequencies','idmc_get_rule_ids','idmc_get_data_preview','idmc_get_object_fields','idmc_validate_expression','idmc_get_insights','idmc_update_insights','idmc_execute_query'],
    'Queries': ['idmc_list_queries','idmc_get_query','idmc_create_query','idmc_update_query','idmc_delete_query','idmc_get_query_results'],
    'Firewall Configs': ['idmc_list_fwconfigs','idmc_get_fwconfig','idmc_create_fwconfig','idmc_delete_fwconfig'],
    'Asset Management & Version Control': ['idmc_lookup_object','idmc_assign_tags','idmc_remove_asset_tags','idmc_get_asset_dependencies','idmc_check_object_access','idmc_get_object_permissions','idmc_create_object_permission','idmc_update_object_permission','idmc_delete_object_permission','idmc_checkout_objects','idmc_checkin_objects','idmc_undo_checkout','idmc_get_commit_history','idmc_get_commit_details','idmc_compare_object_versions','idmc_pull_objects','idmc_get_source_control_action_status','idmc_download_object_states','idmc_get_fetch_state_status','idmc_start_fetch_state','idmc_get_load_state_status','idmc_start_load_state','idmc_upload_load_state_package','idmc_get_last_successful_run_key'],
    'Import / Export & Bundles': ['idmc_start_export_job','idmc_get_export_job_status','idmc_download_export_package','idmc_start_import_job','idmc_get_import_job_status','idmc_upload_import_package','idmc_get_bundle','idmc_install_bundle','idmc_uninstall_bundle'],
    'Metering': ['idmc_start_metering_export','idmc_get_metering_export_status','idmc_download_metering_data'],
}

tool_map = {t['name']: t.get('description', '(no description)') for t in TOOLS}

lines = []
lines.append('IDMC REST API MCP Server — Complete Tool Reference')
lines.append('=' * 70)
lines.append(f'Total tools: {len(TOOLS)}')
lines.append('')

categorized = set()
num = 1

for cat, names in categories.items():
    matching = [n for n in names if n in tool_map]
    if not matching:
        continue
    lines.append(f'## {cat} ({len(matching)} tools)')
    lines.append('-' * 70)
    for name in matching:
        desc = tool_map[name]
        desc = desc.replace('\n', ' ').strip() if isinstance(desc, str) else str(desc)
        lines.append(f'{num:3}. {name}')
        lines.append(f'       Description: {desc}')
        lines.append('')
        categorized.add(name)
        num += 1

remaining = [name for name in tool_map if name not in categorized]
if remaining:
    lines.append(f'## Uncategorized ({len(remaining)} tools)')
    lines.append('-' * 70)
    for name in sorted(remaining):
        desc = tool_map[name]
        desc = desc.replace('\n', ' ').strip() if isinstance(desc, str) else str(desc)
        lines.append(f'{num:3}. {name}')
        lines.append(f'       Description: {desc}')
        lines.append('')
        num += 1

lines.append('=' * 70)
lines.append(f'End of list — {len(TOOLS)} tools total')

output = '\n'.join(lines)
with open('idmc_tools_list.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print(output)
print()
print(f'>>> Saved to idmc_tools_list.txt ({len(TOOLS)} tools)')

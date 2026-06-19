# Least Privilege Recommendations (Mock Lab)

Generated from `sample_iam_bindings.json`. Educational output only.

| Identity | Resource | Current Permission | Risk | Recommended Permission | Rationale |
| --- | --- | --- | --- | --- | --- |
| student_user | console_device | use (assigned_lessons) | low | keep | Binding matches expected role baseline for the mock lab. |
| student_user | student_learning_records | read (self_only) | low | keep | Binding matches expected role baseline for the mock lab. |
| educator_admin | admin_console | administer (classroom) | low | keep | Binding matches expected role baseline for the mock lab. |
| educator_admin | student_learning_records | export (bulk_all_students) | high | export_class_scope_with_audit | Replace bulk export with class-scoped export, watermarking, and audit events. |
| service_agent | console_device | maintain (fleet) | low | keep | Binding matches expected role baseline for the mock lab. |
| service_agent | student_user | impersonate (support_sessions) | critical | impersonate_with_break_glass_approval | Support automation should require time-bound approval and audit before identity takeover. |
| research_operator | telemetry_bucket | read (deidentified_cohorts) | low | keep | Binding matches expected role baseline for the mock lab. |
| research_operator | model_config | write (experiment_profiles) | critical | write_with_dual_control | Model policy changes should require research lead approval and change tickets. |
| public_demo_guest | public_demo_app | use (sandbox) | low | keep | Binding matches expected role baseline for the mock lab. |
| public_demo_guest | telemetry_bucket | read (aggregate_metrics) | high | deny | Demo guests must stay inside the public sandbox; telemetry is fleet-scoped. |

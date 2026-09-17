window.VC_LIBRARY = {
  "tasks": [
    {
      "task_id": "vc_human_a11y_primary",
      "pack_id": "human_a11y",
      "title": "Human accessibility session \u2014 primary surfaces",
      "short_description": "Run planned accessibility tasks across Home, Vault, App Center, and related surfaces.",
      "purpose": "Collect human accessibility observations for J6; software readiness alone is not a PASS.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_HUMAN_A11Y_PACKET_READY"
      ],
      "estimated_minutes": 90,
      "safety_notes": [
        "Stop anytime",
        "Do not capture passwords or personal portfolio content"
      ],
      "participant_steps": [
        "Confirm consent on the consent screen",
        "Use only the assigned modality for this block",
        "Complete the primary task on the assigned surface",
        "Trigger one recoverable error and recover",
        "Rate the task and add comments"
      ],
      "moderator_steps": [
        "Record environment (device, SR version, zoom)",
        "Observe without coaching unless safety requires it",
        "File severity-1 issues immediately"
      ],
      "expected_result": "Observation form complete with evidence attachments for assigned surfaces.",
      "pass_rule": "Real participant sessions; required evidence; severity1_open==0; reviewer signoff; attestation.",
      "required_evidence": [
        "observation_form",
        "screenshot_or_log"
      ],
      "optional_evidence": [
        "screen_recording"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "focus",
        "name_role",
        "contrast",
        "keyboard_trap",
        "sr_silence",
        "other"
      ],
      "device_or_sku": "Student 14.5 / any shell surface",
      "requires_human": true,
      "requires_physical": false,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": "1",
      "gate_unlocked": "human_a11y_pass / J6_CLASS upgrade",
      "required_equipment": [
        "participant",
        "moderator",
        "optional screen reader"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_physical_printer",
      "pack_id": "physical_printer",
      "title": "Physical printer validation",
      "short_description": "Connect a named USB and/or LAN printer and complete the printer packet.",
      "purpose": "Clear PHYSICAL_PRINTER_PENDING only with real hardware evidence.",
      "evidence_class_target": "HUMAN_OBSERVED+SYSTEM_CAPTURED",
      "prerequisite_ids": [
        "CX4_PHYSICAL_PRINTER_PACKET_READY"
      ],
      "estimated_minutes": 120,
      "safety_notes": [
        "Use only approved printers",
        "Do not force paper jams"
      ],
      "participant_steps": [
        "Confirm printer is connected and powered",
        "Print the test page from Writer or Care",
        "Photograph output if consented",
        "Confirm job ID appears in system collector (or moderator attaches mock for UI drills only)"
      ],
      "moderator_steps": [
        "Run CUPS collector",
        "Record printer model and connection path",
        "Attach output photos"
      ],
      "expected_result": "Successful USB or LAN print with job IDs and output integrity evidence.",
      "pass_rule": "Real printer path + collector bundle + reviewer signoff.",
      "required_evidence": [
        "cups_collector_bundle",
        "output_photo_or_hash"
      ],
      "optional_evidence": [
        "lan_discovery_log"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "discovery",
        "job_failure",
        "output_quality",
        "other"
      ],
      "device_or_sku": "Student 14.5 / Docked",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": "2",
      "gate_unlocked": "PHYSICAL_PRINTER_PENDING clearance",
      "required_equipment": [
        "named USB or LAN printer"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_camera_mic_av",
      "pack_id": "camera_mic_av",
      "title": "Camera / microphone / AV validation",
      "short_description": "Exercise camera, mic, and AV permission flows on physical devices.",
      "purpose": "Clear PHYSICAL_CAMERA_MIC_AV_PENDING with field evidence.",
      "evidence_class_target": "HUMAN_OBSERVED+SYSTEM_CAPTURED",
      "prerequisite_ids": [
        "CX4_CAMERA_MIC_AV_PACKET_READY"
      ],
      "estimated_minutes": 120,
      "safety_notes": [
        "Respect media consent",
        "No recording of bystanders without consent"
      ],
      "participant_steps": [
        "Grant or deny camera permission as instructed",
        "Capture a short test clip only if media consent was accepted",
        "Speak a test phrase into the mic",
        "Note quality and permission UX"
      ],
      "moderator_steps": [
        "Run AV diagnostics collector",
        "Record device names",
        "File privacy issues"
      ],
      "expected_result": "AV checklist complete with diagnostics and human quality notes.",
      "pass_rule": "Field checklist complete; no severity-1 privacy failures; reviewer signoff.",
      "required_evidence": [
        "av_diagnostics",
        "quality_notes"
      ],
      "optional_evidence": [
        "short_clip"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "permission",
        "quality",
        "privacy",
        "other"
      ],
      "device_or_sku": "Student 14.5 / Handheld Hybrid",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": "3",
      "gate_unlocked": "PHYSICAL_CAMERA_MIC_AV_PENDING clearance",
      "required_equipment": [
        "physical camera/mic"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_physical_peripherals",
      "pack_id": "physical_peripherals",
      "title": "Physical peripheral matrix",
      "short_description": "Validate keyboard, mouse, touch, BT, dock, and Ring as available.",
      "purpose": "Prove peripheral matrix on real devices.",
      "evidence_class_target": "HUMAN_OBSERVED+SYSTEM_CAPTURED",
      "prerequisite_ids": [
        "CX4_PHYSICAL_PERIPHERAL_PACKET_READY"
      ],
      "estimated_minutes": 150,
      "safety_notes": [
        "Hot-plug carefully",
        "Do not force connectors"
      ],
      "participant_steps": [
        "Connect the assigned peripheral",
        "Complete a primary interaction",
        "Disconnect and reconnect once",
        "Note any lag or dropouts"
      ],
      "moderator_steps": [
        "Run peripheral collector",
        "Log reconnect mutations"
      ],
      "expected_result": "Per-device checks recorded with enumeration and reconnect logs.",
      "pass_rule": "Named peripherals checked on real hardware; reviewer signoff.",
      "required_evidence": [
        "peripheral_matrix_log"
      ],
      "optional_evidence": [
        "photo_of_setup"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "enumeration",
        "reconnect",
        "latency",
        "other"
      ],
      "device_or_sku": "Device Quartet + Dock + Rings",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": "4",
      "gate_unlocked": "physical_peripheral_pass",
      "required_equipment": [
        "named peripherals"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_evt_student_14_5",
      "pack_id": "device_quartet_evt",
      "title": "Student 14.5 EVT validation",
      "short_description": "Execute the EVT packet for Student 14.5.",
      "purpose": "Clear EVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_EVT_PACKET_READY"
      ],
      "estimated_minutes": 240,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "EVT report for Student 14.5.",
      "pass_rule": "EVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "evt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "Student 14.5",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "EVT_PENDING clearance",
      "required_equipment": [
        "EVT hardware for Student 14.5"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_evt_handheld_hybrid",
      "pack_id": "device_quartet_evt",
      "title": "Handheld Hybrid EVT validation",
      "short_description": "Execute the EVT packet for Handheld Hybrid.",
      "purpose": "Clear EVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_EVT_PACKET_READY"
      ],
      "estimated_minutes": 240,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "EVT report for Handheld Hybrid.",
      "pass_rule": "EVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "evt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "Handheld Hybrid",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "EVT_PENDING clearance",
      "required_equipment": [
        "EVT hardware for Handheld Hybrid"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_evt_ds_xl_coder",
      "pack_id": "device_quartet_evt",
      "title": "DS-XL Coder EVT validation",
      "short_description": "Execute the EVT packet for DS-XL Coder.",
      "purpose": "Clear EVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_EVT_PACKET_READY"
      ],
      "estimated_minutes": 240,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "EVT report for DS-XL Coder.",
      "pass_rule": "EVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "evt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "DS-XL Coder",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "EVT_PENDING clearance",
      "required_equipment": [
        "EVT hardware for DS-XL Coder"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_evt_edge_io_rings",
      "pack_id": "device_quartet_evt",
      "title": "Edge I/O Rings EVT validation",
      "short_description": "Execute the EVT packet for Edge I/O Rings.",
      "purpose": "Clear EVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_EVT_PACKET_READY"
      ],
      "estimated_minutes": 240,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "EVT report for Edge I/O Rings.",
      "pass_rule": "EVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "evt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "Edge I/O Rings",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "EVT_PENDING clearance",
      "required_equipment": [
        "EVT hardware for Edge I/O Rings"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_evt_first_party_dock",
      "pack_id": "device_quartet_evt",
      "title": "First-party Dock EVT validation",
      "short_description": "Execute the EVT packet for First-party Dock.",
      "purpose": "Clear EVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_EVT_PACKET_READY"
      ],
      "estimated_minutes": 240,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "EVT report for First-party Dock.",
      "pass_rule": "EVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "evt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "First-party Dock",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "EVT_PENDING clearance",
      "required_equipment": [
        "EVT hardware for First-party Dock"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_dvt_student_14_5",
      "pack_id": "device_quartet_dvt",
      "title": "Student 14.5 DVT validation",
      "short_description": "Execute the DVT packet for Student 14.5.",
      "purpose": "Clear DVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_DVT_PACKET_READY"
      ],
      "estimated_minutes": 480,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "DVT report for Student 14.5.",
      "pass_rule": "DVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "dvt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "Student 14.5",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "DVT_PENDING clearance",
      "required_equipment": [
        "DVT hardware for Student 14.5"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_dvt_handheld_hybrid",
      "pack_id": "device_quartet_dvt",
      "title": "Handheld Hybrid DVT validation",
      "short_description": "Execute the DVT packet for Handheld Hybrid.",
      "purpose": "Clear DVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_DVT_PACKET_READY"
      ],
      "estimated_minutes": 480,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "DVT report for Handheld Hybrid.",
      "pass_rule": "DVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "dvt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "Handheld Hybrid",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "DVT_PENDING clearance",
      "required_equipment": [
        "DVT hardware for Handheld Hybrid"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_dvt_ds_xl_coder",
      "pack_id": "device_quartet_dvt",
      "title": "DS-XL Coder DVT validation",
      "short_description": "Execute the DVT packet for DS-XL Coder.",
      "purpose": "Clear DVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_DVT_PACKET_READY"
      ],
      "estimated_minutes": 480,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "DVT report for DS-XL Coder.",
      "pass_rule": "DVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "dvt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "DS-XL Coder",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "DVT_PENDING clearance",
      "required_equipment": [
        "DVT hardware for DS-XL Coder"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_dvt_edge_io_rings",
      "pack_id": "device_quartet_dvt",
      "title": "Edge I/O Rings DVT validation",
      "short_description": "Execute the DVT packet for Edge I/O Rings.",
      "purpose": "Clear DVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_DVT_PACKET_READY"
      ],
      "estimated_minutes": 480,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "DVT report for Edge I/O Rings.",
      "pass_rule": "DVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "dvt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "Edge I/O Rings",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "DVT_PENDING clearance",
      "required_equipment": [
        "DVT hardware for Edge I/O Rings"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_dvt_first_party_dock",
      "pack_id": "device_quartet_dvt",
      "title": "First-party Dock DVT validation",
      "short_description": "Execute the DVT packet for First-party Dock.",
      "purpose": "Clear DVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_DVT_PACKET_READY"
      ],
      "estimated_minutes": 480,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "DVT report for First-party Dock.",
      "pass_rule": "DVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "dvt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "First-party Dock",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "DVT_PENDING clearance",
      "required_equipment": [
        "DVT hardware for First-party Dock"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_pvt_student_14_5",
      "pack_id": "device_quartet_pvt",
      "title": "Student 14.5 PVT validation",
      "short_description": "Execute the PVT packet for Student 14.5.",
      "purpose": "Clear PVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_PVT_PACKET_READY"
      ],
      "estimated_minutes": 480,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "PVT report for Student 14.5.",
      "pass_rule": "PVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "pvt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "Student 14.5",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "PVT_PENDING clearance",
      "required_equipment": [
        "PVT hardware for Student 14.5"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_pvt_handheld_hybrid",
      "pack_id": "device_quartet_pvt",
      "title": "Handheld Hybrid PVT validation",
      "short_description": "Execute the PVT packet for Handheld Hybrid.",
      "purpose": "Clear PVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_PVT_PACKET_READY"
      ],
      "estimated_minutes": 480,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "PVT report for Handheld Hybrid.",
      "pass_rule": "PVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "pvt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "Handheld Hybrid",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "PVT_PENDING clearance",
      "required_equipment": [
        "PVT hardware for Handheld Hybrid"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_pvt_ds_xl_coder",
      "pack_id": "device_quartet_pvt",
      "title": "DS-XL Coder PVT validation",
      "short_description": "Execute the PVT packet for DS-XL Coder.",
      "purpose": "Clear PVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_PVT_PACKET_READY"
      ],
      "estimated_minutes": 480,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "PVT report for DS-XL Coder.",
      "pass_rule": "PVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "pvt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "DS-XL Coder",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "PVT_PENDING clearance",
      "required_equipment": [
        "PVT hardware for DS-XL Coder"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_pvt_edge_io_rings",
      "pack_id": "device_quartet_pvt",
      "title": "Edge I/O Rings PVT validation",
      "short_description": "Execute the PVT packet for Edge I/O Rings.",
      "purpose": "Clear PVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_PVT_PACKET_READY"
      ],
      "estimated_minutes": 480,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "PVT report for Edge I/O Rings.",
      "pass_rule": "PVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "pvt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "Edge I/O Rings",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "PVT_PENDING clearance",
      "required_equipment": [
        "PVT hardware for Edge I/O Rings"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_pvt_first_party_dock",
      "pack_id": "device_quartet_pvt",
      "title": "First-party Dock PVT validation",
      "short_description": "Execute the PVT packet for First-party Dock.",
      "purpose": "Clear PVT_PENDING only with real hardware stage evidence.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_PVT_PACKET_READY"
      ],
      "estimated_minutes": 480,
      "safety_notes": [
        "Do not fabricate hardware",
        "Follow lab ESD rules"
      ],
      "participant_steps": [
        "Confirm board/SKU identity",
        "Follow the stage packet checklist",
        "Record failures with severity",
        "Attach stage report evidence"
      ],
      "moderator_steps": [
        "Verify hardware identity",
        "Store stage report under evidence store"
      ],
      "expected_result": "PVT report for First-party Dock.",
      "pass_rule": "PVT gates green per SKU packet + reviewer signoff.",
      "required_evidence": [
        "pvt_report"
      ],
      "optional_evidence": [
        "thermal_log",
        "photo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "bringup",
        "thermal",
        "mechanical",
        "wireless",
        "other"
      ],
      "device_or_sku": "First-party Dock",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "5",
      "gate_unlocked": "PVT_PENDING clearance",
      "required_equipment": [
        "PVT hardware for First-party Dock"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_firmware_lifecycle",
      "pack_id": "firmware_lifecycle",
      "title": "Firmware lifecycle field check",
      "short_description": "Run firmware inventory and failed-update recovery on real devices (simulation \u2260 PASS).",
      "purpose": "Collect field firmware evidence; simulation harness remains distinct.",
      "evidence_class_target": "SYSTEM_CAPTURED+HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_FIRMWARE_LIFECYCLE_PACKET_READY"
      ],
      "estimated_minutes": 90,
      "safety_notes": [
        "Do not brick devices",
        "Keep recovery media ready"
      ],
      "participant_steps": [
        "Confirm current firmware version",
        "Attempt approved update path",
        "Verify recovery path if instructed"
      ],
      "moderator_steps": [
        "Capture firmware inventory",
        "Distinguish sim vs physical"
      ],
      "expected_result": "Firmware inventory + recovery notes with clear sim vs physical labeling.",
      "pass_rule": "Physical device evidence only; simulation never sets physical_pass.",
      "required_evidence": [
        "firmware_inventory"
      ],
      "optional_evidence": [
        "recovery_log"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "update_fail",
        "recovery",
        "other"
      ],
      "device_or_sku": "any",
      "requires_human": true,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": null,
      "gate_unlocked": null,
      "required_equipment": [
        "target device"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_support_care_rma",
      "pack_id": "support_repair_rma",
      "title": "Support / Care / repair / RMA walkthrough",
      "short_description": "Exercise support bundle and repair intake templates with a facilitator.",
      "purpose": "Validate support/repair readiness packets with human operators.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_SUPPORT_BUNDLE_READY",
        "CX4_REPAIR_RMA_PACKET_READY"
      ],
      "estimated_minutes": 60,
      "safety_notes": [
        "Do not include real customer PII in drills"
      ],
      "participant_steps": [
        "Open Care",
        "Generate a support bundle (or attach mock)",
        "Complete repair intake draft"
      ],
      "moderator_steps": [
        "Redact PII",
        "Confirm bundle hashes"
      ],
      "expected_result": "Support bundle + intake draft stored locally.",
      "pass_rule": "Operator completes intake; reviewer signoff; no PII leakage.",
      "required_evidence": [
        "support_bundle_or_intake"
      ],
      "optional_evidence": [
        "screenshot"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "intake",
        "bundle",
        "privacy",
        "other"
      ],
      "device_or_sku": "any",
      "requires_human": true,
      "requires_physical": false,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": null,
      "gate_unlocked": null,
      "required_equipment": [],
      "active_by_default": false
    },
    {
      "task_id": "vc_external_chat_meeting",
      "pack_id": "external_chat_meeting",
      "title": "External chat / meeting provider validation",
      "short_description": "Live validation against provider contracts when credentials exist.",
      "purpose": "Collect external provider integration evidence without claiming PASS from contracts alone.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_CHAT_MEETING_PROVIDER_READINESS_PASS"
      ],
      "estimated_minutes": 120,
      "safety_notes": [
        "Use approved test accounts only"
      ],
      "participant_steps": [
        "Join test meeting",
        "Send test chat",
        "Verify AV permissions"
      ],
      "moderator_steps": [
        "Capture live traces",
        "Do not store credentials in evidence"
      ],
      "expected_result": "Live traces attached; credentials never stored.",
      "pass_rule": "Live provider session + reviewer signoff.",
      "required_evidence": [
        "live_trace_notes"
      ],
      "optional_evidence": [
        "screenshot"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "auth",
        "av",
        "chat",
        "other"
      ],
      "device_or_sku": "any",
      "requires_human": true,
      "requires_physical": false,
      "requires_external_provider": true,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "6",
      "gate_unlocked": "external_provider_integration evidence",
      "required_equipment": [
        "provider credentials"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_institutional_issuer",
      "pack_id": "institutional_issuer",
      "title": "Institutional issuer onboarding checks",
      "short_description": "Human review checklist for issuer onboarding engagement.",
      "purpose": "Track issuer engagement; certification_claimed stays false unless earned.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_EXTERNAL_ISSUER_PACKET_READY"
      ],
      "estimated_minutes": 180,
      "safety_notes": [
        "Do not claim certification from checklist alone"
      ],
      "participant_steps": [
        "Review onboarding packet",
        "Record issuer contact outcome",
        "Attach trust-exchange notes if any"
      ],
      "moderator_steps": [
        "Keep certification_claimed=false unless earned"
      ],
      "expected_result": "Onboarding checklist progress recorded.",
      "pass_rule": "Real issuer engagement evidence + reviewer signoff; no auto-certify.",
      "required_evidence": [
        "issuer_checklist_notes"
      ],
      "optional_evidence": [
        "email_redacted"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "trust",
        "revocation",
        "other"
      ],
      "device_or_sku": "n/a",
      "requires_human": true,
      "requires_physical": false,
      "requires_external_provider": true,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "7",
      "gate_unlocked": "external issuer evidence",
      "required_equipment": [
        "willing issuer org"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_privacy_review",
      "pack_id": "privacy_review",
      "title": "Privacy review checklist",
      "short_description": "Human checklist for privacy review checklist (preparation \u2260 approval).",
      "purpose": "Collect review evidence; never auto-set legal/cert/mfg PASS.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_PRIVACY_REVIEW_PACKET_READY"
      ],
      "estimated_minutes": 120,
      "safety_notes": [
        "Counsel/lab conclusions only from signed review",
        "Matrix alone never certifies"
      ],
      "participant_steps": [
        "Open checklist",
        "Mark each row with notes",
        "Attach supporting docs if any"
      ],
      "moderator_steps": [
        "Ensure legal_approval/certified/manufacturing_pass remain false without signed evidence"
      ],
      "expected_result": "Checklist progress with attachments.",
      "pass_rule": "Signed review/lab evidence + reviewer signoff; never from packet alone.",
      "required_evidence": [
        "checklist_notes"
      ],
      "optional_evidence": [
        "signed_memo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "gap",
        "risk",
        "other"
      ],
      "device_or_sku": "n/a",
      "requires_human": true,
      "requires_physical": false,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "8",
      "gate_unlocked": "legal_approval",
      "required_equipment": [
        "counsel or lab"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_rights_review",
      "pack_id": "rights_review",
      "title": "Rights review checklist",
      "short_description": "Human checklist for rights review checklist (preparation \u2260 approval).",
      "purpose": "Collect review evidence; never auto-set legal/cert/mfg PASS.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_RIGHTS_REGISTER_READY"
      ],
      "estimated_minutes": 120,
      "safety_notes": [
        "Counsel/lab conclusions only from signed review",
        "Matrix alone never certifies"
      ],
      "participant_steps": [
        "Open checklist",
        "Mark each row with notes",
        "Attach supporting docs if any"
      ],
      "moderator_steps": [
        "Ensure legal_approval/certified/manufacturing_pass remain false without signed evidence"
      ],
      "expected_result": "Checklist progress with attachments.",
      "pass_rule": "Signed review/lab evidence + reviewer signoff; never from packet alone.",
      "required_evidence": [
        "checklist_notes"
      ],
      "optional_evidence": [
        "signed_memo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "gap",
        "risk",
        "other"
      ],
      "device_or_sku": "n/a",
      "requires_human": true,
      "requires_physical": false,
      "requires_external_provider": false,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "8",
      "gate_unlocked": "legal_approval",
      "required_equipment": [
        "counsel or lab"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_certification_evidence",
      "pack_id": "certification",
      "title": "Certification evidence collection",
      "short_description": "Human checklist for certification evidence collection (preparation \u2260 approval).",
      "purpose": "Collect review evidence; never auto-set legal/cert/mfg PASS.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_CERTIFICATION_MATRIX_READY"
      ],
      "estimated_minutes": 120,
      "safety_notes": [
        "Counsel/lab conclusions only from signed review",
        "Matrix alone never certifies"
      ],
      "participant_steps": [
        "Open checklist",
        "Mark each row with notes",
        "Attach supporting docs if any"
      ],
      "moderator_steps": [
        "Ensure legal_approval/certified/manufacturing_pass remain false without signed evidence"
      ],
      "expected_result": "Checklist progress with attachments.",
      "pass_rule": "Signed review/lab evidence + reviewer signoff; never from packet alone.",
      "required_evidence": [
        "checklist_notes"
      ],
      "optional_evidence": [
        "signed_memo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "gap",
        "risk",
        "other"
      ],
      "device_or_sku": "n/a",
      "requires_human": true,
      "requires_physical": false,
      "requires_external_provider": true,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": "9",
      "gate_unlocked": "certified",
      "required_equipment": [
        "counsel or lab"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_manufacturing_evidence",
      "pack_id": "manufacturing",
      "title": "Manufacturing evidence collection",
      "short_description": "Human checklist for manufacturing evidence collection (preparation \u2260 approval).",
      "purpose": "Collect review evidence; never auto-set legal/cert/mfg PASS.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [
        "CX4_MANUFACTURING_PACKET_READY"
      ],
      "estimated_minutes": 120,
      "safety_notes": [
        "Counsel/lab conclusions only from signed review",
        "Matrix alone never certifies"
      ],
      "participant_steps": [
        "Open checklist",
        "Mark each row with notes",
        "Attach supporting docs if any"
      ],
      "moderator_steps": [
        "Ensure legal_approval/certified/manufacturing_pass remain false without signed evidence"
      ],
      "expected_result": "Checklist progress with attachments.",
      "pass_rule": "Signed review/lab evidence + reviewer signoff; never from packet alone.",
      "required_evidence": [
        "checklist_notes"
      ],
      "optional_evidence": [
        "signed_memo"
      ],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "gap",
        "risk",
        "other"
      ],
      "device_or_sku": "n/a",
      "requires_human": true,
      "requires_physical": false,
      "requires_external_provider": true,
      "status": "pending_external",
      "version": "v1",
      "edmund_action_id": null,
      "gate_unlocked": "manufacturing_pass",
      "required_equipment": [
        "mfg partner"
      ],
      "active_by_default": false
    },
    {
      "task_id": "vc_software_smoke_walkthrough",
      "pack_id": "validation_center_smoke",
      "title": "Validation Center software walkthrough (non-gate)",
      "short_description": "Exercise UI flows without claiming human/physical PASS.",
      "purpose": "Qualify Validation Center software only.",
      "evidence_class_target": "HUMAN_OBSERVED",
      "prerequisite_ids": [],
      "estimated_minutes": 15,
      "safety_notes": [
        "This walkthrough never promotes human/physical gates"
      ],
      "participant_steps": [
        "Accept consent",
        "Start the task",
        "Mark steps complete",
        "Attach a text note as evidence",
        "Complete ratings",
        "Submit task"
      ],
      "moderator_steps": [
        "Confirm no gate tokens flip"
      ],
      "expected_result": "Session can be submitted for software QA only.",
      "pass_rule": "N/A \u2014 software qualification only; does not unlock product gates.",
      "required_evidence": [
        "text_note"
      ],
      "optional_evidence": [],
      "rating_schema": {
        "completion": [
          "completed_successfully",
          "completed_with_difficulty",
          "could_not_complete",
          "not_attempted_skipped"
        ],
        "ease": {
          "1": "Very difficult",
          "2": "Difficult",
          "3": "Neutral",
          "4": "Easy",
          "5": "Very easy"
        },
        "confidence": {
          "1": "Not confident",
          "2": "Slightly confident",
          "3": "Neutral",
          "4": "Confident",
          "5": "Very confident"
        },
        "satisfaction": {
          "1": "Very dissatisfied",
          "2": "Dissatisfied",
          "3": "Neutral",
          "4": "Satisfied",
          "5": "Very satisfied"
        },
        "accessibility_impact": [
          "none",
          "minor_friction",
          "moderate_barrier",
          "major_barrier",
          "blocking_barrier"
        ],
        "physical_comfort_optional": [
          "comfortable",
          "slight_discomfort",
          "moderate_discomfort",
          "severe_discomfort",
          "stop_test"
        ],
        "free_text": [
          "comment",
          "what_was_confusing",
          "what_would_make_easier"
        ]
      },
      "issue_categories": [
        "ui",
        "other"
      ],
      "device_or_sku": "host",
      "requires_human": true,
      "requires_physical": false,
      "requires_external_provider": false,
      "status": "available",
      "version": "v1",
      "edmund_action_id": null,
      "gate_unlocked": null,
      "required_equipment": [],
      "active_by_default": true
    }
  ],
  "packs": [
    {
      "pack_id": "human_a11y",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": false,
      "requires_external_provider": false,
      "status": "available",
      "task_ids": [
        "vc_human_a11y_primary"
      ]
    },
    {
      "pack_id": "physical_printer",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "task_ids": [
        "vc_physical_printer"
      ]
    },
    {
      "pack_id": "camera_mic_av",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "task_ids": [
        "vc_camera_mic_av"
      ]
    },
    {
      "pack_id": "physical_peripherals",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "task_ids": [
        "vc_physical_peripherals"
      ]
    },
    {
      "pack_id": "device_quartet_evt",
      "task_count": 5,
      "active_by_default_count": 0,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "task_ids": [
        "vc_evt_student_14_5",
        "vc_evt_handheld_hybrid",
        "vc_evt_ds_xl_coder",
        "vc_evt_edge_io_rings",
        "vc_evt_first_party_dock"
      ]
    },
    {
      "pack_id": "device_quartet_dvt",
      "task_count": 5,
      "active_by_default_count": 0,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "task_ids": [
        "vc_dvt_student_14_5",
        "vc_dvt_handheld_hybrid",
        "vc_dvt_ds_xl_coder",
        "vc_dvt_edge_io_rings",
        "vc_dvt_first_party_dock"
      ]
    },
    {
      "pack_id": "device_quartet_pvt",
      "task_count": 5,
      "active_by_default_count": 0,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "pending_external",
      "task_ids": [
        "vc_pvt_student_14_5",
        "vc_pvt_handheld_hybrid",
        "vc_pvt_ds_xl_coder",
        "vc_pvt_edge_io_rings",
        "vc_pvt_first_party_dock"
      ]
    },
    {
      "pack_id": "firmware_lifecycle",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": true,
      "requires_external_provider": false,
      "status": "available",
      "task_ids": [
        "vc_firmware_lifecycle"
      ]
    },
    {
      "pack_id": "support_repair_rma",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": false,
      "requires_external_provider": false,
      "status": "available",
      "task_ids": [
        "vc_support_care_rma"
      ]
    },
    {
      "pack_id": "external_chat_meeting",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": false,
      "requires_external_provider": true,
      "status": "pending_external",
      "task_ids": [
        "vc_external_chat_meeting"
      ]
    },
    {
      "pack_id": "institutional_issuer",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": false,
      "requires_external_provider": true,
      "status": "pending_external",
      "task_ids": [
        "vc_institutional_issuer"
      ]
    },
    {
      "pack_id": "privacy_review",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": false,
      "requires_external_provider": false,
      "status": "pending_external",
      "task_ids": [
        "vc_privacy_review"
      ]
    },
    {
      "pack_id": "rights_review",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": false,
      "requires_external_provider": false,
      "status": "pending_external",
      "task_ids": [
        "vc_rights_review"
      ]
    },
    {
      "pack_id": "certification",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": false,
      "requires_external_provider": true,
      "status": "pending_external",
      "task_ids": [
        "vc_certification_evidence"
      ]
    },
    {
      "pack_id": "manufacturing",
      "task_count": 1,
      "active_by_default_count": 0,
      "requires_physical": false,
      "requires_external_provider": true,
      "status": "pending_external",
      "task_ids": [
        "vc_manufacturing_evidence"
      ]
    },
    {
      "pack_id": "validation_center_smoke",
      "task_count": 1,
      "active_by_default_count": 1,
      "requires_physical": false,
      "requires_external_provider": false,
      "status": "available",
      "task_ids": [
        "vc_software_smoke_walkthrough"
      ]
    }
  ],
  "edmund": {
    "packet_path": "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/cx4-validation-center-human-field-ui/docs/complete-experience/cx4_readiness/CX4_EDMUND_ACTION_PACKET.md",
    "packet_exists": true,
    "actions": [
      {
        "edmund_action_id": "1",
        "title": "Human accessibility session",
        "prerequisite": "`CX4_HUMAN_A11Y_PACKET_READY`",
        "estimated_time": "6\u20138 hours total (plan).",
        "required_equipment_or_person": "Execute `HUMAN_A11Y_VALIDATION_PACKET.md` with planned participants; store evidence under `artifacts/complete_experience/cx4_0/human_a11y/`.",
        "exact_evidence": "observation forms, issues, screenshots/logs",
        "gate_unlocked": "human a11y PASS / J6 class upgrade (only after real sessions)",
        "task_ids": [
          "vc_human_a11y_primary"
        ],
        "ui_visible": true
      },
      {
        "edmund_action_id": "2",
        "title": "Physical printer session",
        "prerequisite": "real printer hardware",
        "estimated_time": "90\u2013120 minutes.",
        "required_equipment_or_person": "Connect named USB and/or LAN printer; run `PHYSICAL_PRINTER_VALIDATION_PACKET.md`; run cups collector.",
        "exact_evidence": "collector bundle + output photos/hashes",
        "gate_unlocked": "`PHYSICAL_PRINTER_PENDING` clearance",
        "task_ids": [
          "vc_physical_printer"
        ],
        "ui_visible": true
      },
      {
        "edmund_action_id": "3",
        "title": "Camera / mic / AV session",
        "prerequisite": "physical camera/mic",
        "estimated_time": "~2 hours.",
        "required_equipment_or_person": "Execute `CAMERA_MIC_AV_VALIDATION_PACKET.md` on physical devices; capture diagnostics.",
        "exact_evidence": "AV diag + quality notes",
        "gate_unlocked": "`PHYSICAL_CAMERA_MIC_AV_PENDING` clearance",
        "task_ids": [
          "vc_camera_mic_av"
        ],
        "ui_visible": true
      },
      {
        "edmund_action_id": "4",
        "title": "Peripheral matrix session",
        "prerequisite": "named peripherals",
        "estimated_time": "2\u20133 hours.",
        "required_equipment_or_person": "Run peripheral matrix with keyboard/mouse/touch/BT/dock/Ring as available.",
        "exact_evidence": "mutation/reconnect logs",
        "gate_unlocked": "physical peripheral PASS",
        "task_ids": [
          "vc_physical_peripherals"
        ],
        "ui_visible": true
      },
      {
        "edmund_action_id": "5",
        "title": "Device Quartet EVT \u2192 DVT \u2192 PVT",
        "prerequisite": "hardware availability",
        "estimated_time": "multi-day to multi-week (plan).",
        "required_equipment_or_person": "Follow per-SKU EVT/DVT/PVT packets; do not fabricate hardware.",
        "exact_evidence": "stage reports",
        "gate_unlocked": "EVT/DVT/PVT pending clearance",
        "task_ids": [
          "vc_evt_student_14_5",
          "vc_evt_handheld_hybrid",
          "vc_evt_ds_xl_coder",
          "vc_evt_edge_io_rings",
          "vc_evt_first_party_dock",
          "vc_dvt_student_14_5",
          "vc_dvt_handheld_hybrid",
          "vc_dvt_ds_xl_coder",
          "vc_dvt_edge_io_rings",
          "vc_dvt_first_party_dock",
          "vc_pvt_student_14_5",
          "vc_pvt_handheld_hybrid",
          "vc_pvt_ds_xl_coder",
          "vc_pvt_edge_io_rings",
          "vc_pvt_first_party_dock"
        ],
        "ui_visible": true
      },
      {
        "edmund_action_id": "6",
        "title": "External chat/meeting provider credentials",
        "prerequisite": "provider access",
        "estimated_time": "~2 hours once credentials exist.",
        "required_equipment_or_person": "Obtain provider account; run live validation against contracts.",
        "exact_evidence": "live traces",
        "gate_unlocked": "external provider integration evidence (may upgrade J4)",
        "task_ids": [
          "vc_external_chat_meeting"
        ],
        "ui_visible": true
      },
      {
        "edmund_action_id": "7",
        "title": "Institutional issuer engagement",
        "prerequisite": "willing issuer",
        "estimated_time": "multi-day (plan).",
        "required_equipment_or_person": "Follow `CX4_INSTITUTIONAL_ISSUER_ONBOARDING.md` with a real issuer org.",
        "exact_evidence": "trust exchange + verify + revocation",
        "gate_unlocked": "external issuer evidence (`certification_claimed` stays false unless earned)",
        "task_ids": [
          "vc_institutional_issuer"
        ],
        "ui_visible": true
      },
      {
        "edmund_action_id": "8",
        "title": "Legal / privacy / rights review",
        "prerequisite": "registers ready",
        "estimated_time": "calendar days (plan).",
        "required_equipment_or_person": "Submit privacy + rights registers for counsel review.",
        "exact_evidence": "signed review memo",
        "gate_unlocked": "`legal_approval`",
        "task_ids": [
          "vc_privacy_review",
          "vc_rights_review"
        ],
        "ui_visible": true
      },
      {
        "edmund_action_id": "9",
        "title": "Certification lab engagement",
        "prerequisite": "EVT+/DVT hardware",
        "estimated_time": "multi-month (plan).",
        "required_equipment_or_person": "Engage labs per `CERTIFICATION_MATRIX.json` rows when hardware maturity allows.",
        "exact_evidence": "certificates/reports",
        "gate_unlocked": "`certified` (never from matrix alone)",
        "task_ids": [
          "vc_certification_evidence"
        ],
        "ui_visible": true
      },
      {
        "edmund_action_id": "10",
        "title": "WAIKE release dependency (do not modify release)",
        "prerequisite": "WAIKE release owners",
        "estimated_time": "blocked on release train.",
        "required_equipment_or_person": "Wait for genuine WAIKE accepted-main earned evidence; then re-verify CX3 earned token.",
        "exact_evidence": "real earned completion artifacts",
        "gate_unlocked": "`CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS`",
        "task_ids": [],
        "ui_visible": true,
        "status": "pending_external_dependency",
        "note": "WAIKE release dependency \u2014 do not modify release; not a VC executable task."
      }
    ],
    "CX4_EDMUND_ACTION_PACKET_UI_MAPPED": true,
    "markdown_preserved": true
  },
  "consent_text": "This Validation Center session collects task ratings, comments, and optional evidence\nto improve gunnchOS. You may stop at any time. We use a participant alias, not your\nlegal name, by default. Data is stored locally on this device unless a moderator\nexplicitly configures otherwise. Photo, audio, and video are optional and require\nseparate consent. Do not share passwords or personal portfolio content.",
  "MINORS_MODE_DISABLED_BY_DEFAULT": true
};

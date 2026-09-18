package com.gunnchos.capsule.bridge

/**
 * Strict allowlist of JS→Kotlin capabilities.
 * Arbitrary method invocation is forbidden.
 */
object BridgeSchemas {
    const val APPASSETS_ORIGIN = "https://appassets.androidplatform.net"

    val ALLOWED_CAPABILITIES = setOf(
        "files",
        "share",
        "clipboard",
        "camera",
        "microphone",
        "notifications",
        "network",
        "battery",
        "thermal",
        "bluetooth",
        "usb_metadata",
        "display",
        "haptics",
        "permissions",
        "open_url",
        "open_android_app",
        "file_picker",
        "document_create",
        "document_open",
        "downloads",
        "session_get",
        "session_put",
        "care_snapshot",
        "linux_guest_status",
        "games_launch",
        "waike_launch",
        "gunnchai_launch",
        "app_center_list",
        "vault_list",
        "vault_op",
        "connect_action",
        "assist_settings",
        "exit_capsule",
        "shell_boot_stage",
        "shell_ready",
        "shell_fatal",
    )

    /** Exact origins only — no wildcards, no prefix matches. */
    val ALLOWED_ORIGINS = setOf(
        APPASSETS_ORIGIN,
    )

    fun isOriginAllowed(origin: String?): Boolean {
        if (origin.isNullOrBlank()) return false
        return origin in ALLOWED_ORIGINS
    }
}

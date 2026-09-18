package com.gunnchos.capsule.bridge

/**
 * Strict allowlist of JS→Kotlin capabilities.
 * Arbitrary method invocation is forbidden.
 */
object BridgeSchemas {
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
    )

    val ALLOWED_ORIGINS = setOf(
        "file://",
        "file://capsule",
        "null",
        "file:///android_asset/shell/index.html",
        "https://gunnchos.local",
    )

    fun isOriginAllowed(origin: String?): Boolean {
        if (origin.isNullOrBlank()) return false
        if (origin in ALLOWED_ORIGINS) return true
        if (origin.startsWith("file:///android_asset/")) return true
        return false
    }
}

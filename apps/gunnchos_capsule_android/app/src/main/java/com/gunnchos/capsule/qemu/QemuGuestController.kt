package com.gunnchos.capsule.qemu

import android.app.ActivityManager
import android.content.Context
import org.json.JSONObject
import java.io.File

/**
 * Rootless QEMU TCG spike probe for optional Linux guest.
 * On-device QEMU binaries are uncommon; boot_pass is earned only when a real boot is observed.
 * Capsule never claims CAPSULE_QEMU_GUEST_BOOT_PASS without evidence.
 */
class QemuGuestController(private val context: Context) {
    fun probe(): JSONObject {
        val am = context.getSystemService(ActivityManager::class.java)
        val mem = ActivityManager.MemoryInfo().also { am.getMemoryInfo(it) }
        val ramMb = when {
            mem.availMem > 3L * 1024 * 1024 * 1024 -> 1536
            else -> 1024
        }
        val candidates = listOf(
            File(context.filesDir, "qemu/qemu-system-aarch64"),
            File("/data/local/tmp/qemu-system-aarch64"),
        )
        val binary = candidates.firstOrNull { it.canExecute() }
        return JSONObject()
            .put("available", binary != null)
            .put("binary", binary?.absolutePath)
            .put("arch", "aarch64")
            .put("ram_mb", ramMb)
            .put("vcpus", 2)
            .put("networking", "user")
            .put("disk", "sparse")
            .put("display", "headless_first")
            .put("boot_pass", false)
            .put("note", if (binary == null) {
                "no_on_device_qemu_binary_boot_pass_unearned"
            } else {
                "binary_present_boot_not_yet_validated"
            })
    }
}

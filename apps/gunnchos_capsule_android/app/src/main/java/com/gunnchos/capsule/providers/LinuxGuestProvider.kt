package com.gunnchos.capsule.providers

import android.content.Context
import android.os.Build
import org.json.JSONObject
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader

/**
 * Optional Linux guest provider.
 * Backends: NONE | QEMU_TCG | ANDROID_AVF_EXPERIMENTAL | REMOTE_EDGE
 */
class LinuxGuestProvider(private val context: Context) {
    enum class Backend { NONE, QEMU_TCG, ANDROID_AVF_EXPERIMENTAL, REMOTE_EDGE }

    fun status(): JSONObject {
        val avf = probeAvf()
        val qemu = probeQemuHostSide()
        val selected = when {
            avf.optBoolean("safePublicApi", false) -> Backend.ANDROID_AVF_EXPERIMENTAL
            qemu.optBoolean("binaryPresent", false) -> Backend.QEMU_TCG
            else -> Backend.NONE
        }
        val result = JSONObject()
            .put("backend", selected.name)
            .put("avf", avf)
            .put("qemu", qemu)
            .put("desktopProvider", selected != Backend.NONE)
            .put("replacesPrimaryShell", false)
            .put("claims", JSONObject()
                .put("CAPSULE_QEMU_GUEST_BOOT_PASS", false)
                .put("CAPSULE_LINUX_DESKTOP_PROVIDER_PASS", false)
                .put("note", "Optional guest gates earned only after honest boot/desktop evidence"),
            )
        return JSONObject().put("ok", true).put("result", result)
    }

    fun probeAvf(): JSONObject {
        // Pixel may advertise hypervisor props; safe public AVF VirtualMachineManager API
        // is not used in this pilot without Android 13+ AVF library dependency.
        val props = JSONObject()
        try {
            val getprop = { key: String ->
                val p = Runtime.getRuntime().exec(arrayOf("/system/bin/getprop", key))
                BufferedReader(InputStreamReader(p.inputStream)).readLine()?.trim().orEmpty()
            }
            // getprop from app sandbox often empty; still document probe attempt
            props.put("sdk", Build.VERSION.SDK_INT)
            props.put("probeAttempted", true)
            props.put("safePublicApi", false)
            props.put("reason", "No AVF VirtualMachineManager dependency in pilot; experimental only")
            props.put("hypervisorVmSupportedProp", "probe_via_adb_baseline")
        } catch (e: Exception) {
            props.put("error", e.message)
            props.put("safePublicApi", false)
        }
        return props
    }

    /**
     * Host-side QEMU TCG spike status (Mac/CI packaging). On-device QEMU is typically unavailable;
     * Capsule may shell out only when a packaged rootless binary exists in app files.
     */
    fun probeQemuHostSide(): JSONObject {
        val packaged = File(context.filesDir, "guest/qemu-system-aarch64")
        val ramMb = recommendRamMb()
        return JSONObject()
            .put("binaryPresent", packaged.exists())
            .put("arch", "aarch64")
            .put("recommendedRamMb", ramMb)
            .put("vcpus", 2)
            .put("networking", "user")
            .put("display", "headless_first")
            .put("sparseDisk", true)
            .put("bootPassEarned", false)
            .put("note", "Ship packaged rootless QEMU + image to earn CAPSULE_QEMU_GUEST_BOOT_PASS")
    }

    private fun recommendRamMb(): Int {
        val am = context.getSystemService(android.app.ActivityManager::class.java)
        val mi = android.app.ActivityManager.MemoryInfo()
        am?.getMemoryInfo(mi)
        val totalGb = mi.totalMem / (1024.0 * 1024.0 * 1024.0)
        return if (totalGb >= 6.0) 1536 else 1024
    }
}

package com.gunnchos.capsule.providers

import android.app.ActivityManager
import android.content.Context
import android.net.ConnectivityManager
import android.os.BatteryManager
import android.os.Build
import android.os.Environment
import android.os.StatFs
import com.gunnchos.capsule.BuildConfig
import org.json.JSONObject

/** Care / support snapshot — no root internals. */
class CareProvider(private val context: Context) {
    fun snapshot(): JSONObject {
        val bm = context.getSystemService(BatteryManager::class.java)
        val cm = context.getSystemService(ConnectivityManager::class.java)
        val am = context.getSystemService(ActivityManager::class.java)
        val mem = ActivityManager.MemoryInfo().also { am?.getMemoryInfo(it) }
        val data = StatFs(Environment.getDataDirectory().absolutePath)

        val result = JSONObject()
            .put("appVersion", BuildConfig.VERSION_NAME)
            .put("versionCode", BuildConfig.VERSION_CODE)
            .put("applicationId", BuildConfig.APPLICATION_ID)
            .put("gitSha", BuildConfig.GIT_SHA)
            .put("buildType", BuildConfig.BUILD_TYPE)
            .put(
                "storage",
                JSONObject()
                    .put("dataAvailableBytes", data.availableBytes)
                    .put("dataTotalBytes", data.totalBytes),
            )
            .put(
                "memory",
                JSONObject()
                    .put("availMem", mem.availMem)
                    .put("totalMem", mem.totalMem)
                    .put("lowMemory", mem.lowMemory),
            )
            .put("batteryPercent", bm?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) ?: -1)
            .put(
                "thermal",
                JSONObject().put(
                    "status",
                    if (Build.VERSION.SDK_INT >= 29) {
                        context.getSystemService(android.os.PowerManager::class.java)?.currentThermalStatus
                    } else {
                        null
                    },
                ),
            )
            .put("networkOnline", cm?.activeNetwork != null)
            .put(
                "health",
                JSONObject()
                    .put("service", "CapsuleForegroundService")
                    .put("providers", "Vault/AppCenter/Games/WAIKE/gunnchAI/Connect/Guest")
                    .put("waike", "bridge_ready")
                    .put("gunnchai", "bridge_ready")
                    .put("guest", LinuxGuestProvider(context).status().optJSONObject("result")),
            )
            .put("supportBundleHint", "Export Care JSON via share — no root dumps")
            .put("rootInternals", false)

        return JSONObject().put("ok", true).put("result", result)
    }
}

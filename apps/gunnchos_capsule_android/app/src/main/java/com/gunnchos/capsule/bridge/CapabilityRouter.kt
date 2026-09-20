package com.gunnchos.capsule.bridge

import android.Manifest
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.ConnectivityManager
import android.net.Uri
import android.os.BatteryManager
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import androidx.core.content.ContextCompat
import com.gunnchos.capsule.CapsuleActivity
import com.gunnchos.capsule.CapsuleForegroundService
import com.gunnchos.capsule.R
import com.gunnchos.capsule.providers.AppCenterProvider
import com.gunnchos.capsule.providers.AssistProvider
import com.gunnchos.capsule.providers.CareProvider
import com.gunnchos.capsule.providers.ConnectProvider
import com.gunnchos.capsule.providers.GamesProvider
import com.gunnchos.capsule.providers.GunnchAiProvider
import com.gunnchos.capsule.providers.LinuxGuestProvider
import com.gunnchos.capsule.providers.SessionStore
import com.gunnchos.capsule.providers.VaultProvider
import com.gunnchos.capsule.providers.WaikeProvider
import org.json.JSONObject

class CapabilityRouter(private val activity: CapsuleActivity) {
    private val vault = VaultProvider(activity)
    private val appCenter = AppCenterProvider(activity)
    private val waike = WaikeProvider(activity)
    private val gunnchai = GunnchAiProvider(activity)
    private val games = GamesProvider(activity)
    private val connect = ConnectProvider(activity)
    private val assist = AssistProvider(activity)
    private val care = CareProvider(activity)
    private val guest = LinuxGuestProvider(activity)
    private val session = SessionStore(activity)

    fun dispatch(capability: String, payload: JSONObject?): JSONObject {
        return when (capability) {
            "clipboard" -> clipboard(payload)
            "share" -> share(payload)
            "network" -> network()
            "battery" -> battery()
            "thermal" -> thermal()
            "display" -> display(payload)
            "haptics" -> haptics(payload)
            "permissions" -> permissions(payload)
            "open_url" -> openUrl(payload)
            "open_android_app" -> openAndroidApp(payload)
            "notifications" -> notifications(payload)
            "bluetooth" -> bluetoothMeta()
            "usb_metadata" -> usbMeta()
            "camera" -> gatedMedia("camera", Manifest.permission.CAMERA)
            "microphone" -> gatedMedia("microphone", Manifest.permission.RECORD_AUDIO)
            "files", "file_picker", "document_create", "document_open", "downloads", "vault_list", "vault_op" ->
                vault.handle(capability, payload)
            "session_get" -> session.get()
            "session_put" -> session.put(payload)
            "care_snapshot" -> care.snapshot()
            "linux_guest_status" -> guest.status()
            "games_launch" -> games.launch(payload)
            "games_list" -> games.matrixSnapshot()
            "waike_launch" -> waike.launch(payload)
            "gunnchai_launch" -> gunnchai.launch(payload)
            "app_center_list" -> appCenter.list(payload)
            "connect_action" -> connect.action(payload)
            "assist_settings" -> assist.settings(payload)
            "shell_boot_stage" -> {
                val stage = payload?.optString("stage").orEmpty()
                activity.runOnUiThread { activity.onShellBootStage(stage) }
                JSONObject().put("stage", stage).put("acked", true)
            }
            "shell_ready" -> {
                activity.runOnUiThread { activity.onShellReady() }
                JSONObject().put("ready", true)
            }
            "shell_fatal" -> {
                val message = payload?.optString("message").orEmpty().ifBlank { "shell_fatal" }
                activity.runOnUiThread { activity.onShellFatal(message) }
                JSONObject().put("fatal", true).put("message", message)
            }
            "exit_capsule" -> {
                activity.runOnUiThread { activity.exitCapsuleToAndroid() }
                JSONObject().put("exited", true)
            }
            else -> throw IllegalArgumentException("unhandled_capability")
        }
    }

    private fun clipboard(payload: JSONObject?): JSONObject {
        val cm = activity.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val action = payload?.optString("action", "read") ?: "read"
        return if (action == "write") {
            val text = payload?.optString("text").orEmpty()
            if (text.length > 64_000) throw IllegalArgumentException("clipboard_too_large")
            cm.setPrimaryClip(ClipData.newPlainText("capsule", text))
            JSONObject().put("written", true)
        } else {
            val text = cm.primaryClip?.getItemAt(0)?.coerceToText(activity)?.toString().orEmpty()
            JSONObject().put("text", text.take(64_000))
        }
    }

    private fun share(payload: JSONObject?): JSONObject {
        val text = payload?.optString("text").orEmpty()
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, text.take(8_000))
        }
        activity.startActivity(Intent.createChooser(intent, "Share from gunnchOS"))
        return JSONObject().put("shared", true)
    }

    private fun network(): JSONObject {
        val cm = activity.getSystemService(ConnectivityManager::class.java)
        val active = cm.activeNetwork != null
        return JSONObject().put("online", active).put("validated", active)
    }

    private fun battery(): JSONObject {
        val bm = activity.getSystemService(BatteryManager::class.java)
        val pct = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        return JSONObject().put("percent", pct).put("charging", bm.isCharging)
    }

    private fun thermal(): JSONObject {
        val status = if (Build.VERSION.SDK_INT >= 29) {
            activity.getSystemService(android.os.PowerManager::class.java)?.currentThermalStatus ?: -1
        } else -1
        return JSONObject().put("status", status).put("api", "PowerManager.currentThermalStatus")
    }

    private fun display(payload: JSONObject?): JSONObject {
        val immersive = payload?.optBoolean("immersive", true) ?: true
        activity.runOnUiThread { activity.setImmersiveMode(immersive) }
        val dm = activity.resources.displayMetrics
        return JSONObject()
            .put("widthPx", dm.widthPixels)
            .put("heightPx", dm.heightPixels)
            .put("densityDpi", dm.densityDpi)
            .put("immersive", immersive)
    }

    private fun haptics(payload: JSONObject?): JSONObject {
        val ms = payload?.optLong("ms", 20L) ?: 20L
        val vibrator = if (Build.VERSION.SDK_INT >= 31) {
            activity.getSystemService(VibratorManager::class.java).defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            activity.getSystemService(Vibrator::class.java)
        }
        vibrator.vibrate(
            VibrationEffect.createOneShot(ms.coerceIn(1, 200), VibrationEffect.DEFAULT_AMPLITUDE),
        )
        return JSONObject().put("vibrated", true)
    }

    private fun permissions(payload: JSONObject?): JSONObject {
        val name = payload?.optString("permission").orEmpty()
        val perm = when (name) {
            "camera" -> Manifest.permission.CAMERA
            "microphone" -> Manifest.permission.RECORD_AUDIO
            "notifications" -> if (Build.VERSION.SDK_INT >= 33) Manifest.permission.POST_NOTIFICATIONS else null
            "bluetooth" -> Manifest.permission.BLUETOOTH_CONNECT
            else -> null
        }
        val granted = if (perm == null) true else
            ContextCompat.checkSelfPermission(activity, perm) == PackageManager.PERMISSION_GRANTED
        return JSONObject().put("permission", name).put("granted", granted)
    }

    private fun openUrl(payload: JSONObject?): JSONObject {
        val url = payload?.optString("url").orEmpty()
        if (!url.startsWith("https://") && !url.startsWith("http://") && !url.startsWith("mailto:")) {
            throw IllegalArgumentException("url_scheme_rejected")
        }
        activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        return JSONObject().put("opened", true)
    }

    fun openExternalUrl(url: String) {
        try {
            openUrl(JSONObject().put("url", url))
        } catch (_: Exception) {
        }
    }

    private fun openAndroidApp(payload: JSONObject?): JSONObject {
        val pkg = payload?.optString("package").orEmpty()
        if (!pkg.matches(Regex("^[a-zA-Z0-9._]+$"))) throw IllegalArgumentException("invalid_package")
        val launch = activity.packageManager.getLaunchIntentForPackage(pkg)
            ?: throw IllegalArgumentException("app_not_found")
        activity.startActivity(launch)
        return JSONObject().put("launched", pkg).put("install_attempted", false)
    }

    private fun notifications(payload: JSONObject?): JSONObject {
        if (Build.VERSION.SDK_INT >= 33) {
            val granted = ContextCompat.checkSelfPermission(
                activity,
                Manifest.permission.POST_NOTIFICATIONS,
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) {
                return JSONObject().put("posted", false).put("consent_required", true)
            }
        }
        val title = payload?.optString("title", "gunnchOS").orEmpty().take(80)
        val text = payload?.optString("text", "").orEmpty().take(240)
        val nm = activity.getSystemService(android.app.NotificationManager::class.java)
        val n = androidx.core.app.NotificationCompat.Builder(activity, CapsuleForegroundService.CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setAutoCancel(true)
            .build()
        nm.notify(7200 + (title.hashCode() and 0xfff), n)
        return JSONObject().put("posted", true)
    }

    private fun bluetoothMeta(): JSONObject {
        return JSONObject()
            .put("adapter_present", activity.packageManager.hasSystemFeature(PackageManager.FEATURE_BLUETOOTH))
            .put("scanning", false)
            .put("note", "metadata_only")
    }

    private fun usbMeta(): JSONObject {
        return JSONObject()
            .put("host_mode_feature", activity.packageManager.hasSystemFeature(PackageManager.FEATURE_USB_HOST))
            .put("accessory_feature", activity.packageManager.hasSystemFeature(PackageManager.FEATURE_USB_ACCESSORY))
            .put("note", "metadata_only_no_device_enumeration")
    }

    private fun gatedMedia(kind: String, permission: String): JSONObject {
        val granted = ContextCompat.checkSelfPermission(activity, permission) == PackageManager.PERMISSION_GRANTED
        return JSONObject()
            .put("kind", kind)
            .put("granted", granted)
            .put("consent_required", !granted)
            .put("capture_started", false)
            .put("note", "permission_mediated_stub_ready_for_intent_launch")
    }
}

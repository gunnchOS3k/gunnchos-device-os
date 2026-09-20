package com.gunnchos.capsule.providers

import android.content.Context
import android.content.Intent
import org.json.JSONObject

/**
 * Four-game launch matrix.
 * Modes: ANDROID_NATIVE | CAPSULE_WEB | LINUX_GUEST | UNAVAILABLE
 */
class GamesProvider(private val context: Context) {
    private val matrix = mapOf(
        "anime-aggressors" to GameEntry(
            "Anime Aggressors",
            preferred = "CAPSULE_WEB",
            webUrl = "https://gunnchos.local/games/anime-aggressors/",
            androidPackage = null,
            linuxGuest = true,
        ),
        "pedestrian-pursuit" to GameEntry(
            "Pedestrian Pursuit",
            preferred = "CAPSULE_WEB",
            webUrl = "https://gunnchos.local/games/pedestrian-pursuit/",
            androidPackage = null,
            linuxGuest = true,
        ),
        "archive-of-life" to GameEntry(
            "Archive of Life",
            preferred = "CAPSULE_WEB",
            webUrl = "https://gunnchos.local/games/archive-of-life/",
            androidPackage = null,
            linuxGuest = false,
        ),
        "beatlink-party" to GameEntry(
            "BeatLink Party",
            preferred = "CAPSULE_WEB",
            webUrl = "https://gunnchos.local/games/beatlink-party/",
            androidPackage = null,
            linuxGuest = false,
        ),
    )

    fun launch(payload: JSONObject?): JSONObject {
        val p = payload ?: JSONObject()
        val id = p.optString("id", p.optString("game", ""))
        val entry = matrix[id] ?: return JSONObject().put("ok", false).put("error", "unknown_game")
        val mode = p.optString("mode", entry.preferred)

        val result = JSONObject()
            .put("game", id)
            .put("title", entry.title)
            .put("mode", mode)
            .put("returnToCapsule", true)
            .put("sessionPersist", mode != "UNAVAILABLE")

        when (mode) {
            "ANDROID_NATIVE" -> {
                val pkg = entry.androidPackage
                if (pkg == null) {
                    result.put("mode", "UNAVAILABLE")
                    result.put("reason", "no_android_native_package_in_pilot")
                    return JSONObject().put("ok", true).put("result", result)
                }
                val launch = context.packageManager.getLaunchIntentForPackage(pkg)
                if (launch == null) {
                    result.put("mode", "UNAVAILABLE")
                    return JSONObject().put("ok", true).put("result", result)
                }
                context.startActivity(launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            }
            "CAPSULE_WEB" -> {
                // In-capsule relative asset path preferred; external URL only if bundled missing
                result.put("launchPath", "games://${id}")
                result.put("bundledHint", "Place web build under assets/games/$id when available")
            }
            "LINUX_GUEST" -> {
                if (!entry.linuxGuest) {
                    result.put("mode", "UNAVAILABLE")
                    result.put("reason", "linux_guest_not_mapped")
                } else {
                    result.put("provider", "LinuxGuestProvider")
                    result.put("note", "Requires CAPSULE_QEMU_GUEST_BOOT_PASS or AVF")
                }
            }
            else -> result.put("mode", "UNAVAILABLE")
        }
        return JSONObject().put("ok", true).put("result", result)
    }

    fun matrixSnapshot(): JSONObject {
        val out = JSONObject()
        matrix.forEach { (id, e) ->
            out.put(
                id,
                JSONObject()
                    .put("title", e.title)
                    .put("preferred", e.preferred)
                    .put("androidNative", e.androidPackage != null)
                    .put("capsuleWeb", true)
                    .put("linuxGuest", e.linuxGuest),
            )
        }
        return JSONObject().put("ok", true).put("result", out)
    }

    private data class GameEntry(
        val title: String,
        val preferred: String,
        val webUrl: String,
        val androidPackage: String?,
        val linuxGuest: Boolean,
    )
}

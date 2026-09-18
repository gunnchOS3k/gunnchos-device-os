package com.gunnchos.capsule.providers

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * App Center catalog for Capsule.
 * Kinds: CAPSULE_INTERNAL | ANDROID_EXTERNAL | WEB_PWA | LINUX_GUEST | REMOTE_PROVIDER | UNAVAILABLE
 * Never silently installs packages.
 */
class AppCenterProvider(private val context: Context) {
    fun list(payload: JSONObject?): JSONObject {
        val q = payload?.optString("q", "").orEmpty().lowercase()
        val apps = catalog().filter {
            q.isBlank() ||
                it.getString("name").lowercase().contains(q) ||
                it.getString("id").lowercase().contains(q)
        }
        return JSONObject()
            .put("ok", true)
            .put(
                "result",
                JSONObject()
                    .put("provider", "capsule-android")
                    .put("silentInstallForbidden", true)
                    .put("apps", JSONArray(apps)),
            )
    }

    private fun catalog(): List<JSONObject> = listOf(
        app("vault", "Vault", "CAPSULE_INTERNAL", "1.0.0", true),
        app("connect", "Connect", "CAPSULE_INTERNAL", "1.0.0", true),
        app("assist", "Assist", "CAPSULE_INTERNAL", "1.0.0", true),
        app("care", "Care", "CAPSULE_INTERNAL", "1.0.0", true),
        app("waike", "WAIKE Learning", "WEB_PWA", "hub", true),
        app("gunnchai", "gunnchAI", "CAPSULE_INTERNAL", "assistant", true),
        app("anime-aggressors", "Anime Aggressors", "CAPSULE_WEB", "matrix", true),
        app("pedestrian-pursuit", "Pedestrian Pursuit", "CAPSULE_WEB", "matrix", true),
        app("archive-of-life", "Archive of Life", "CAPSULE_WEB", "matrix", true),
        app("beatlink-party", "BeatLink Party", "CAPSULE_WEB", "matrix", true),
        app("linux-guest", "Linux Guest Desktop", "LINUX_GUEST", "optional", false),
        app("com.android.chrome", "Chrome (Android)", "ANDROID_EXTERNAL", "device", false),
        app("remote-edge", "Remote Edge Provider", "REMOTE_PROVIDER", "optional", false),
    )

    private fun app(
        id: String,
        name: String,
        kind: String,
        version: String,
        installed: Boolean,
    ) = JSONObject()
        .put("id", id)
        .put("name", name)
        .put("source", kind)
        .put("kind", kind)
        .put("version", version)
        .put("installed", installed)
        .put("permissions", JSONArray())
        .put("provenance", "capsule-android-catalog")
        .put("silentInstall", false)
}

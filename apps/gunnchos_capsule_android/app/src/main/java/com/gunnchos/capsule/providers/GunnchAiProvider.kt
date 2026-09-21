package com.gunnchos.capsule.providers

import android.content.Context
import org.json.JSONObject

/**
 * gunnchAI assistant launch.
 * Kirby / frontier only behind experimental flags.
 */
class GunnchAiProvider(private val context: Context) {
    fun launch(payload: JSONObject?): JSONObject {
        val experimentalKirby = payload?.optBoolean("experimentalKirby", false) == true ||
            context.getSharedPreferences("capsule", Context.MODE_PRIVATE)
                .getBoolean("EXPERIMENTAL_KIRBY", false)
        val prompt = payload?.optString("prompt").orEmpty()
        val offline = payload?.optBoolean("offline", false) == true

        val result = JSONObject()
            .put("surface", "gunnchAI")
            .put("openAssistant", true)
            .put("textHelp", true)
            .put("provenance", "capsule-gunnchai-local-deterministic")
            .put("runtimeLabel", if (offline) "Local deterministic" else "Local deterministic")
            .put("runtimeKind", "local_deterministic")
            .put("permissionGatedTools", true)
            .put("waikeHandoff", true)
            .put("offlineFallback", true)
            .put("kirbyEnabled", experimentalKirby)
            .put("kirbyNote", if (experimentalKirby) "experimental" else "disabled_by_default")

        if (prompt.isNotBlank()) {
            result.put(
                "reply",
                deterministicReply(prompt),
            )
        }

        return JSONObject().put("ok", true).put("result", result)
    }

    private fun deterministicReply(prompt: String): String {
        val q = prompt.lowercase()
        return when {
            q.contains("nearby") || q.contains("on-device") ->
                "Nearby Mac is an edge runtime, not on-device AI. This Capsule reply is local deterministic help."
            q.contains("waike") || q.contains("learn") ->
                "Open the WAIKE surface for learning. Offline honesty stays visible when the hub cannot sync."
            q.contains("game") ->
                "Use the Games library for first-party titles. Install state stays honest when builds are missing."
            else ->
                "Local deterministic help only. Ask about WAIKE, Vault, Games, Settings, or Connect — no frontier model is claimed."
        }
    }
}

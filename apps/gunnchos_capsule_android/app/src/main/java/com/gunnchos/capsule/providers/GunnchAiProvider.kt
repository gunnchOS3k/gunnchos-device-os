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

        val result = JSONObject()
            .put("surface", "gunnchAI")
            .put("openAssistant", true)
            .put("textHelp", true)
            .put("provenance", "capsule-gunnchai")
            .put("permissionGatedTools", true)
            .put("waikeHandoff", true)
            .put("offlineFallback", true)
            .put("kirbyEnabled", experimentalKirby)
            .put("kirbyNote", if (experimentalKirby) "experimental" else "disabled_by_default")

        return JSONObject().put("ok", true).put("result", result)
    }
}

package com.gunnchos.capsule.providers

import android.content.Context
import android.content.Intent
import android.net.Uri
import org.json.JSONObject

/** WAIKE Capsule surface — prefer mobile web/PWA; do not duplicate UI. */
class WaikeProvider(private val context: Context) {
    fun launch(payload: JSONObject?): JSONObject {
        val p = payload ?: JSONObject()
        val mode = p.optString("mode", "WEB_PWA")
        val offline = p.optBoolean("offline", false)
        val prefs = context.getSharedPreferences("capsule", Context.MODE_PRIVATE)
        val configuredUrl = prefs.getString("WAIKE_HUB_URL", "").orEmpty()
        val result = JSONObject()
            .put("surface", "WAIKE")
            .put("mode", if (mode == "UNAVAILABLE") "UNAVAILABLE" else "FULL_VIA_ADAPTER")
            .put("uiDuplicated", false)
            .put("offlineHubProvenance", offline)
            .put("provenance", "capsule-waike-bridge")
            .put("classification", "FULL_VIA_ADAPTER")
        when (mode) {
            "WEB_PWA", "mobile_web" -> {
                result.put("launch", "in_capsule_webview_or_custom_tab")
                result.put(
                    "urlHint",
                    configuredUrl.ifBlank { "bundled or https hub — owner configures WAIKE_HUB_URL" },
                )
                val url = p.optString("url", configuredUrl)
                if (url.startsWith("https://")) {
                    context.startActivity(
                        Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
                    )
                    result.put("opened", url)
                }
            }
            else -> result.put("mode", "UNAVAILABLE")
        }
        return JSONObject().put("ok", true).put("result", result)
    }
}

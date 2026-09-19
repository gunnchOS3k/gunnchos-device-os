package com.gunnchos.capsule.bridge

import android.webkit.JavascriptInterface
import android.webkit.WebView
import com.gunnchos.capsule.CapsuleActivity
import org.json.JSONObject

/**
 * Strict allowlisted WebView bridge. No arbitrary JS→Kotlin dispatch.
 * Validates via [BridgeSecurity], routes via [CapabilityRouter].
 */
class CapsuleBridge(
    private val activity: CapsuleActivity,
    @Suppress("UNUSED_PARAMETER") private val webView: WebView,
) {
    private val router = CapabilityRouter(activity)

    @JavascriptInterface
    fun invoke(requestJson: String): String {
        val (obj, err) = BridgeSecurity.validateRequest(requestJson)
        if (err != null) {
            val id = try {
                JSONObject(requestJson).optString("id")
            } catch (_: Exception) {
                null
            }
            return BridgeSecurity.error(id, err)
        }
        val id = obj!!.getString("id")
        val capability = obj.getString("capability")
        val payload = obj.optJSONObject("payload")
        return try {
            val result = router.dispatch(capability, payload)
            val ok = result.optBoolean("ok", true)
            if (!ok) {
                BridgeSecurity.error(
                    id,
                    result.optString("error", "capability_failed"),
                    result.optBoolean("consent_required", false),
                )
            } else {
                BridgeSecurity.ok(id, result.opt("result") ?: result)
            }
        } catch (e: Exception) {
            BridgeSecurity.error(id, e.message ?: "bridge_exception")
        }
    }

    fun openExternalUrl(url: String) {
        router.dispatch("open_url", JSONObject().put("url", url))
    }
}

package com.gunnchos.capsule.bridge

import org.json.JSONObject

object BridgeSecurity {
    fun validateRequest(raw: String): Pair<JSONObject?, String?> {
        val obj = try {
            JSONObject(raw)
        } catch (_: Exception) {
            return null to "invalid_json"
        }
        val id = obj.optString("id")
        val capability = obj.optString("capability")
        val origin = obj.optString("origin")
        if (id.isBlank()) return null to "missing_id"
        if (capability.isBlank() || capability !in BridgeSchemas.ALLOWED_CAPABILITIES) {
            return null to "capability_not_allowlisted"
        }
        if (!BridgeSchemas.isOriginAllowed(origin)) {
            return null to "origin_rejected"
        }
        val payload = obj.optJSONObject("payload")
        if (payload != null) {
            val keys = payload.keys()
            while (keys.hasNext()) {
                val k = keys.next()
                if (k.equals("eval", true) || k.equals("javascript", true) || k.equals("code", true)) {
                    return null to "forbidden_payload_key"
                }
            }
        }
        return obj to null
    }

    fun error(id: String?, message: String, consentRequired: Boolean = false): String {
        return JSONObject()
            .put("id", id ?: "unknown")
            .put("ok", false)
            .put("error", message)
            .put("consent_required", consentRequired)
            .toString()
    }

    fun ok(id: String, result: Any?): String {
        val out = JSONObject().put("id", id).put("ok", true)
        when (result) {
            null -> out.put("result", JSONObject.NULL)
            is JSONObject -> out.put("result", result)
            is org.json.JSONArray -> out.put("result", result)
            is String, is Number, is Boolean -> out.put("result", result)
            else -> out.put("result", result.toString())
        }
        return out.toString()
    }
}

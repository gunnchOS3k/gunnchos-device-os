package com.gunnchos.capsule.providers

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.Instant

/** Durable Capsule session in app-private storage. */
class SessionStore(private val context: Context) {
    private val file: File
        get() = File(context.filesDir, "capsule_session_v1.json")

    fun get(): JSONObject = getSessionJson()

    fun put(payload: JSONObject?): JSONObject {
        val session = payload?.optJSONObject("session") ?: payload ?: JSONObject()
        putSession(session)
        return JSONObject().put("saved", true)
    }

    fun getSessionJson(): JSONObject {
        if (!file.exists()) {
            return JSONObject()
                .put("version", 1)
                .put("surface", "home")
                .put("history", JSONArray().put("home"))
                .put("offline", false)
                .put("highContrast", false)
                .put("reduceMotion", false)
                .put("scale", 1)
                .put("updatedAt", JSONObject.NULL)
        }
        return JSONObject(file.readText())
    }

    fun putSession(session: JSONObject) {
        session.put("version", 1)
        if (!session.has("updatedAt") || session.isNull("updatedAt")) {
            session.put("updatedAt", Instant.now().toString())
        }
        file.writeText(session.toString())
    }

    fun touchResume() {
        val s = getSessionJson()
        s.put("lastResumeAt", Instant.now().toString())
        file.writeText(s.toString())
    }

    fun touchPause() {
        val s = getSessionJson()
        s.put("lastPauseAt", Instant.now().toString())
        file.writeText(s.toString())
    }
}

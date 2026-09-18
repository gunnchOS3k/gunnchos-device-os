package com.gunnchos.capsule.providers

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.CalendarContract
import android.provider.ContactsContract
import org.json.JSONObject

/** Connect via Android intents — browser/email/calendar/contacts/camera/mic/share. */
class ConnectProvider(private val context: Context) {
    fun action(payload: JSONObject?): JSONObject {
        val p = payload ?: JSONObject()
        val action = p.optString("action", "")
        return when (action) {
            "browser" -> open(Intent(Intent.ACTION_VIEW, Uri.parse(p.optString("url", "https://example.com"))))
            "email" -> open(
                Intent(Intent.ACTION_SENDTO, Uri.parse("mailto:${p.optString("to", "")}")),
            )
            "calendar" -> open(Intent(Intent.ACTION_INSERT).setData(CalendarContract.Events.CONTENT_URI))
            "contacts" -> open(Intent(Intent.ACTION_VIEW, ContactsContract.Contacts.CONTENT_URI))
            "meetings" -> open(Intent(Intent.ACTION_VIEW, Uri.parse("https://meet.google.com")))
            "camera" -> JSONObject().put("ok", true).put(
                "result",
                JSONObject().put("consent_required", true).put("via", "android_camera_permission"),
            )
            "microphone" -> JSONObject().put("ok", true).put(
                "result",
                JSONObject().put("consent_required", true).put("via", "android_mic_permission"),
            )
            "share" -> {
                val send = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_TEXT, p.optString("text", ""))
                }
                open(Intent.createChooser(send, "Share"))
            }
            else -> JSONObject().put("ok", false).put("error", "unknown_connect_action")
        }
    }

    private fun open(intent: Intent): JSONObject {
        return try {
            context.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            JSONObject().put("ok", true).put("result", JSONObject().put("opened", true))
        } catch (e: Exception) {
            JSONObject().put("ok", false).put("error", e.message ?: "intent_failed")
        }
    }
}

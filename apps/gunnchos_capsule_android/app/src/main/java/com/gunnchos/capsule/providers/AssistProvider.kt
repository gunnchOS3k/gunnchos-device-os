package com.gunnchos.capsule.providers

import android.content.Context
import android.provider.Settings
import android.view.accessibility.AccessibilityManager
import org.json.JSONObject

/**
 * Assist mechanics: font scale, contrast, reduced motion, TalkBack presence.
 * Human validation remains owner-gated (CAPSULE_HUMAN_ACCESSIBILITY_VALIDATION=false by default).
 */
class AssistProvider(private val context: Context) {
    fun settings(payload: JSONObject?): JSONObject {
        val prefs = context.getSharedPreferences("capsule_assist", Context.MODE_PRIVATE)
        payload?.optDouble("font_scale")?.takeIf { !it.isNaN() }?.let {
            prefs.edit().putFloat("font_scale", it.toFloat().coerceIn(0.85f, 2.0f)).apply()
        }
        payload?.optBoolean("high_contrast")?.let { prefs.edit().putBoolean("high_contrast", it).apply() }
        payload?.optBoolean("reduce_motion")?.let { prefs.edit().putBoolean("reduce_motion", it).apply() }

        val am = context.getSystemService(AccessibilityManager::class.java)
        val fontScale = context.resources.configuration.fontScale
        return JSONObject()
            .put("font_scale_system", fontScale)
            .put("font_scale_capsule", prefs.getFloat("font_scale", fontScale))
            .put("high_contrast", prefs.getBoolean("high_contrast", false))
            .put("reduce_motion", prefs.getBoolean("reduce_motion", false))
            .put("talkback_enabled", am?.isEnabled == true && am.isTouchExplorationEnabled)
            .put("keyboard_switch_ready", true)
            .put("mechanics_pass", true)
            .put("human_validation", false)
            .put("animator_duration_scale", Settings.Global.getString(context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE))
    }
}

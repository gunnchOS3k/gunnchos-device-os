package com.gunnchos.capsule

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager

class CapsuleApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        val channel = NotificationChannel(
            CapsuleForegroundService.CHANNEL_ID,
            getString(R.string.capsule_channel_name),
            NotificationManager.IMPORTANCE_LOW,
        ).apply {
            description = getString(R.string.capsule_channel_desc)
        }
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(channel)
    }
}

package com.gunnchos.capsule

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat

/**
 * Foreground service for long-lived Capsule session / optional guest work.
 * Does not require root. Does not wipe device data.
 */
class CapsuleForegroundService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val launch = Intent(this, CapsuleActivity::class.java)
        val pi = PendingIntent.getActivity(
            this,
            0,
            launch,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notification: Notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.capsule_service_title))
            .setContentText(getString(R.string.capsule_service_text))
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentIntent(pi)
            .setOngoing(true)
            .build()
        startForeground(NOTIFICATION_ID, notification)
        return START_STICKY
    }

    companion object {
        const val CHANNEL_ID = "gunnchos_capsule"
        private const val NOTIFICATION_ID = 7101

        fun start(context: Context) {
            val intent = Intent(context, CapsuleForegroundService::class.java)
            context.startForegroundService(intent)
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, CapsuleForegroundService::class.java))
        }
    }
}

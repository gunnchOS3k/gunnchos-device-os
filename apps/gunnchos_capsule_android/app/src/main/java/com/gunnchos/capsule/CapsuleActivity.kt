package com.gunnchos.capsule

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.view.WindowManager
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.gunnchos.capsule.bridge.CapsuleBridge
import com.gunnchos.capsule.providers.SessionStore

/**
 * Single main Activity hosting the production gunnch_shell WebView.
 * Experience parity only — stock Android host, no root / bootloader / wipe.
 */
class CapsuleActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private lateinit var bridge: CapsuleBridge
    private var immersive = true

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        webView = WebView(this).apply {
            layoutParams = android.widget.FrameLayout.LayoutParams(
                android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
                android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
            )
            setBackgroundColor(0xFF0B1220.toInt())
        }
        setContentView(webView)

        bridge = CapsuleBridge(this, webView)
        configureWebView(webView)
        applyImmersive()

        onBackPressedDispatcher.addCallback(
            this,
            object : OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    when {
                        webView.canGoBack() -> webView.goBack()
                        else -> {
                            // Capsule home semantics: ask shell to navigate home via JS; else finish
                            webView.evaluateJavascript(
                                "(function(){try{window.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));}catch(e){}})();",
                                null,
                            )
                            // Second back after short delay exits Android app intentionally
                            isEnabled = false
                            onBackPressedDispatcher.onBackPressed()
                            isEnabled = true
                        }
                    }
                }
            },
        )

        CapsuleForegroundService.start(this)
        webView.loadUrl("file:///android_asset/shell/index.html")
    }

    private fun configureWebView(wv: WebView) {
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG)
        wv.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            mediaPlaybackRequiresUserGesture = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            cacheMode = WebSettings.LOAD_DEFAULT
            setSupportZoom(false)
            builtInZoomControls = false
            displayZoomControls = false
            useWideViewPort = true
            loadWithOverviewMode = true
            textZoom = 100
        }
        wv.addJavascriptInterface(bridge, "AndroidCapsuleBridge")
        wv.webChromeClient = WebChromeClient()
        wv.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val url = request?.url ?: return false
                // Keep shell navigation in-capsule; external http(s) goes through bridge open_url
                if (url.scheme == "file" || url.scheme == "about") return false
                bridge.openExternalUrl(url.toString())
                return true
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                view?.evaluateJavascript(
                    """
                    (function(){
                      window.__GUNNCH_HOST__='ANDROID_CAPSULE';
                      window.__GUNNCH_CAPSULE_BRIDGE__=true;
                    })();
                    """.trimIndent(),
                    null,
                )
            }
        }
    }

    private fun applyImmersive() {
        val controller = WindowInsetsControllerCompat(window, window.decorView)
        if (immersive) {
            controller.hide(WindowInsetsCompat.Type.systemBars())
            controller.systemBarsBehavior =
                WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        } else {
            controller.show(WindowInsetsCompat.Type.systemBars())
        }
        window.decorView.systemUiVisibility =
            (View.SYSTEM_UI_FLAG_LAYOUT_STABLE or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN)
    }

    override fun onResume() {
        super.onResume()
        applyImmersive()
        SessionStore(this).touchResume()
    }

    override fun onPause() {
        SessionStore(this).touchPause()
        super.onPause()
    }

    override fun onDestroy() {
        CapsuleForegroundService.stop(this)
        webView.destroy()
        super.onDestroy()
    }

    fun setImmersiveMode(enabled: Boolean) {
        immersive = enabled
        applyImmersive()
    }

    fun exitCapsuleToAndroid() {
        val home = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME)
        home.flags = Intent.FLAG_ACTIVITY_NEW_TASK
        startActivity(home)
        finish()
    }
}

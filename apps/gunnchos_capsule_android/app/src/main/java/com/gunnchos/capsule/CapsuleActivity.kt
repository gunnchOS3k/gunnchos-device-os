package com.gunnchos.capsule

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.View
import android.view.WindowManager
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.webkit.WebViewAssetLoader
import com.gunnchos.capsule.bridge.BridgeSchemas
import com.gunnchos.capsule.bridge.CapsuleBridge
import com.gunnchos.capsule.providers.SessionStore
import java.io.File

/**
 * Single main Activity hosting the production gunnch_shell WebView via WebViewAssetLoader.
 * Never silent black screen — branded overlay until shell_ready or diagnostic failure UI.
 */
class CapsuleActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private lateinit var bridge: CapsuleBridge
    private lateinit var overlay: View
    private lateinit var statusView: TextView
    private lateinit var detailView: TextView
    private lateinit var failureActions: LinearLayout
    private var immersive = true
    private var shellReady = false
    private var lastStage = "NATIVE_ACTIVITY_CREATED"
    private val mainHandler = Handler(Looper.getMainLooper())
    private val shellTimeoutMs = 12_000L

    private val shellTimeout = Runnable {
        if (!shellReady) {
            onShellFatal("Timed out waiting for GUNNCHOS_SHELL_READY (last=$lastStage)")
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        setContentView(R.layout.activity_capsule)

        webView = findViewById(R.id.capsule_webview)
        overlay = findViewById(R.id.capsule_startup_overlay)
        statusView = findViewById(R.id.capsule_startup_status)
        detailView = findViewById(R.id.capsule_startup_detail)
        failureActions = findViewById(R.id.capsule_failure_actions)
        findViewById<Button>(R.id.capsule_retry).setOnClickListener { reloadShell() }
        findViewById<Button>(R.id.capsule_diagnostics).setOnClickListener { showDiagnostics() }
        findViewById<Button>(R.id.capsule_exit).setOnClickListener { exitCapsuleToAndroid() }

        applyBrandMark()
        setStartupStatus("NATIVE_ACTIVITY_CREATED", "gunnchOS Capsule host starting")

        bridge = CapsuleBridge(this, webView)
        configureWebView(webView)
        applyImmersive()

        onBackPressedDispatcher.addCallback(
            this,
            object : OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    when {
                        !shellReady -> exitCapsuleToAndroid()
                        webView.canGoBack() -> webView.goBack()
                        else -> {
                            webView.evaluateJavascript(
                                "(function(){try{window.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));}catch(e){}})();",
                                null,
                            )
                        }
                    }
                }
            },
        )

        CapsuleForegroundService.start(this)
        reloadShell()
    }

    private fun applyBrandMark() {
        val image = findViewById<ImageView>(R.id.capsule_brand_mark)
        val brandingCandidates = listOf(
            File(filesDir, "branding/gunnchos-logo-master.jpg"),
            File(getExternalFilesDir(null), "branding/gunnchos-logo-master.jpg"),
        )
        val assetIntake = try {
            assets.open("branding/gunnchos-logo-master.jpg").use { input ->
                BitmapFactory.decodeStream(input)
            }
        } catch (_: Exception) {
            null
        }
        val fileBmp = brandingCandidates.firstOrNull { it.isFile }?.let { BitmapFactory.decodeFile(it.absolutePath) }
        val bmp: Bitmap? = assetIntake ?: fileBmp
        if (bmp != null) {
            image.setImageBitmap(bmp)
            detailView.text = "Branded startup (logo asset loaded)"
        } else {
            image.setImageResource(R.drawable.ic_launcher_foreground)
            detailView.text =
                "ASSET_INTAKE: branding/gunnchos-logo-master.jpg not present — using temporary launcher mark"
            Log.w(TAG_NAV, "branding asset missing; temporary launcher mark in use")
        }
    }

    private fun reloadShell() {
        shellReady = false
        failureActions.visibility = View.GONE
        overlay.visibility = View.VISIBLE
        setStartupStatus("MAIN_DOCUMENT_REQUESTED", "Loading production shell via WebViewAssetLoader")
        mainHandler.removeCallbacks(shellTimeout)
        mainHandler.postDelayed(shellTimeout, shellTimeoutMs)
        webView.loadUrl(SHELL_URL)
    }

    private fun configureWebView(wv: WebView) {
        WebView.setWebContentsDebuggingEnabled(true)
        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        wv.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
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
        wv.setBackgroundColor(0xFF0B1220.toInt())
        wv.addJavascriptInterface(bridge, "AndroidCapsuleBridge")

        wv.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(consoleMessage: ConsoleMessage?): Boolean {
                val msg = consoleMessage?.message().orEmpty()
                val line = consoleMessage?.lineNumber() ?: -1
                val src = consoleMessage?.sourceId().orEmpty()
                Log.i(TAG_WEB, "[$line] $msg ($src)")
                return true
            }
        }

        wv.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView?,
                request: WebResourceRequest?,
            ): WebResourceResponse? {
                val url = request?.url ?: return null
                return try {
                    assetLoader.shouldInterceptRequest(url)
                } catch (e: Exception) {
                    Log.e(TAG_ERR, "shouldInterceptRequest failed for $url: ${e.message}")
                    null
                }
            }

            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val url = request?.url ?: return false
                if (url.host == "appassets.androidplatform.net") {
                    return false // keep appassets internal
                }
                if (url.scheme == "about") return false
                Log.i(TAG_NAV, "externalize url=$url")
                bridge.openExternalUrl(url.toString())
                return true
            }

            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                Log.i(TAG_NAV, "onPageStarted url=$url")
                setStartupStatus("MAIN_DOCUMENT_STARTED", url.orEmpty())
            }

            override fun onPageCommitVisible(view: WebView?, url: String?) {
                Log.i(TAG_NAV, "onPageCommitVisible url=$url")
                setStartupStatus("MAIN_DOCUMENT_COMMITTED", url.orEmpty())
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                Log.i(TAG_NAV, "onPageFinished url=$url")
                view?.evaluateJavascript(
                    """
                    (function(){
                      window.__GUNNCH_HOST__='ANDROID_CAPSULE';
                      window.__GUNNCH_CAPSULE_BRIDGE__=true;
                      try { console.log('GUNNCH_HOST_INJECTED origin=' + location.origin); } catch (e) {}
                    })();
                    """.trimIndent(),
                    null,
                )
                if (!shellReady) {
                    setStartupStatus("MAIN_DOCUMENT_FINISHED", "Waiting for JS shell_ready…")
                }
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?,
            ) {
                val desc = error?.description?.toString().orEmpty()
                val url = request?.url?.toString().orEmpty()
                Log.e(TAG_ERR, "onReceivedError main=${request?.isForMainFrame} url=$url desc=$desc")
                if (request?.isForMainFrame == true) {
                    onShellFatal("Main document error: $desc")
                }
            }

            override fun onReceivedHttpError(
                view: WebView?,
                request: WebResourceRequest?,
                errorResponse: WebResourceResponse?,
            ) {
                Log.e(
                    TAG_ERR,
                    "onReceivedHttpError url=${request?.url} status=${errorResponse?.statusCode}",
                )
            }

            override fun onRenderProcessGone(
                view: WebView?,
                detail: android.webkit.RenderProcessGoneDetail?,
            ): Boolean {
                Log.e(TAG_ERR, "onRenderProcessGone didCrash=${detail?.didCrash()}")
                onShellFatal("WebView render process gone (crash=${detail?.didCrash()})")
                return true
            }
        }
    }

    fun onShellBootStage(stage: String) {
        lastStage = stage
        Log.i(TAG_NAV, "shell_boot_stage=$stage")
        setStartupStatus(stage, "Shell boot progressing")
    }

    fun onShellReady() {
        if (shellReady) return
        shellReady = true
        lastStage = "GUNNCHOS_SHELL_READY"
        mainHandler.removeCallbacks(shellTimeout)
        Log.i(TAG_NAV, "shell_ready — hiding overlay")
        setStartupStatus("GUNNCHOS_SHELL_READY", "Production shell interactive")
        overlay.visibility = View.GONE
        failureActions.visibility = View.GONE
    }

    fun onShellFatal(message: String) {
        shellReady = false
        mainHandler.removeCallbacks(shellTimeout)
        Log.e(TAG_ERR, "shell_fatal: $message")
        overlay.visibility = View.VISIBLE
        failureActions.visibility = View.VISIBLE
        statusView.text = "Capsule failed to render"
        detailView.text = "$message\nlast_stage=$lastStage\nurl=$SHELL_URL\norigin=${BridgeSchemas.APPASSETS_ORIGIN}"
    }

    private fun setStartupStatus(stage: String, detail: String) {
        lastStage = stage
        statusView.text = stage
        if (detail.isNotBlank()) detailView.text = detail
    }

    private fun showDiagnostics() {
        val text =
            "stage=$lastStage ready=$shellReady url=$SHELL_URL origin=${BridgeSchemas.APPASSETS_ORIGIN}"
        Toast.makeText(this, text, Toast.LENGTH_LONG).show()
        Log.i(TAG_NAV, "diagnostics $text")
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
        mainHandler.removeCallbacks(shellTimeout)
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

    companion object {
        const val SHELL_URL = "https://appassets.androidplatform.net/assets/shell/index.html"
        private const val TAG_WEB = "GUNNCH_CAPSULE_WEB"
        private const val TAG_NAV = "GUNNCH_CAPSULE_NAV"
        private const val TAG_ERR = "GUNNCH_CAPSULE_ERROR"
    }
}

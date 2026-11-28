package com.videoextractor.app.ui

import android.annotation.SuppressLint
import android.graphics.Bitmap
import android.webkit.CookieManager
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.videoextractor.app.core.HttpClients
import com.videoextractor.app.core.UrlUtils
import com.videoextractor.app.engine.DouyinExtractor
import com.videoextractor.app.engine.SniffHelper
import com.videoextractor.app.engine.XianyuExtractor
import com.videoextractor.app.model.ExtractResult
import com.videoextractor.app.model.ExtractedVideo
import org.json.JSONObject

/**
 * Interactive local WebView modal:
 * - Lets users sign in or pass verification on their own device (cookies stay local in CookieManager).
 * - Simultaneously sniffs any loaded video stream or MTOP JSON and surfaces a one-tap extract banner.
 */
@SuppressLint("SetJavaScriptEnabled")
@Composable
fun InteractiveWebViewDialog(
    initialUrl: String,
    onCaptured: (ExtractedVideo) -> Unit,
    onDismiss: (reExtract: Boolean) -> Unit,
) {
    var loadProgress by remember { mutableIntStateOf(0) }
    var currentTitle by remember { mutableStateOf("内置浏览器嗅探") }
    var capturedVideo by remember { mutableStateOf<ExtractedVideo?>(null) }
    var webViewRef by remember { mutableStateOf<WebView?>(null) }

    Dialog(
        onDismissRequest = { onDismiss(false) },
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = BgDark,
        ) {
            Column(modifier = Modifier.fillMaxSize()) {
                // Top action bar
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(SurfaceDark)
                        .padding(horizontal = 8.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    IconButton(onClick = { onDismiss(false) }) {
                        Icon(Icons.Default.Close, contentDescription = "关闭", tint = TextPrimary)
                    }
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .padding(horizontal = 6.dp),
                    ) {
                        Text(
                            text = currentTitle,
                            color = TextPrimary,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.SemiBold,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                        Text(
                            text = "本地登录 Cookie 仅存于本机；播放视频即可自动嗅探",
                            color = TextMuted,
                            fontSize = 11.sp,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                    IconButton(onClick = { webViewRef?.reload() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "刷新", tint = TextPrimary)
                    }
                    TextButton(onClick = { onDismiss(true) }) {
                        Text("重试解析", color = AccentSky, fontWeight = FontWeight.SemiBold)
                    }
                }

                if (loadProgress in 1..99) {
                    LinearProgressIndicator(
                        progress = { loadProgress / 100f },
                        modifier = Modifier.fillMaxWidth(),
                        color = AccentSky,
                        trackColor = SurfaceVariantDark,
                    )
                }

                // Floating capture banner when media is detected
                capturedVideo?.let { video ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(ColorBannerBg)
                            .padding(horizontal = 12.dp, vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                            Text(
                                text = "已嗅探到 ${video.platform} 视频",
                                color = SuccessGreen,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                            )
                            Text(
                                text = video.title,
                                color = TextPrimary,
                                fontSize = 12.sp,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                        }
                        Button(
                            onClick = { onCaptured(video) },
                            shape = RoundedCornerShape(10.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = SuccessGreen),
                        ) {
                            Text("立即提取", color = BgDark, fontWeight = FontWeight.Bold)
                        }
                    }
                }

                Box(modifier = Modifier.weight(1f).fillMaxWidth()) {
                    AndroidView(
                        modifier = Modifier.fillMaxSize(),
                        factory = { ctx ->
                            CookieManager.getInstance().setAcceptCookie(true)
                            WebView(ctx).apply {
                                settings.javaScriptEnabled = true
                                settings.domStorageEnabled = true
                                settings.mediaPlaybackRequiresUserGesture = false
                                settings.mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
                                settings.userAgentString = if (UrlUtils.isDouyin(initialUrl)) {
                                    HttpClients.IPHONE_UA
                                } else {
                                    HttpClients.MOBILE_UA
                                }
                                CookieManager.getInstance().setAcceptThirdPartyCookies(this, true)

                                val platform = UrlUtils.platformOf(initialUrl)

                                fun recordVideo(rawUrl: String, engineTag: String, titleOverride: String? = null, thumb: String? = null) {
                                    val clean = if (UrlUtils.isDouyin(initialUrl)) DouyinExtractor.dewatermark(rawUrl) else rawUrl
                                    val vid = ExtractedVideo(
                                        title = (titleOverride ?: currentTitle).trim().ifBlank { "${platform}视频" }.take(120),
                                        directUrl = clean,
                                        pageUrl = initialUrl,
                                        platform = platform,
                                        engine = engineTag,
                                        thumbnailUrl = thumb,
                                        headers = mapOf(
                                            "User-Agent" to settings.userAgentString,
                                            "Referer" to SniffHelper.defaultRefererFor(initialUrl),
                                        ),
                                    )
                                    post { capturedVideo = vid }
                                }

                                addJavascriptInterface(
                                    object {
                                        @JavascriptInterface
                                        fun onEvent(type: String, value: String) {
                                            when (type) {
                                                "douyin_router" -> {
                                                    val parsed = DouyinExtractor.parseRouterDataJson(value, initialUrl)
                                                    if (parsed is ExtractResult.Success) {
                                                        post {
                                                            capturedVideo = parsed.video.copy(engine = "browser-router")
                                                        }
                                                    }
                                                }
                                                "video" -> {
                                                    if (SniffHelper.looksLikeMediaUrl(value)) {
                                                        recordVideo(value, "browser-dom")
                                                    }
                                                }
                                                "mtop" -> {
                                                    try {
                                                        val json = JSONObject(value)
                                                        val vq = XianyuExtractor.parseVideoQuery(json)
                                                        if (!vq.isNullOrBlank()) {
                                                            recordVideo(vq, "browser-mtop")
                                                            return
                                                        }
                                                        val parsed = XianyuExtractor.parseDetailPayload(json, initialUrl)
                                                        val ok = parsed.result as? ExtractResult.Success
                                                        if (ok != null) {
                                                            post {
                                                                capturedVideo = ok.video.copy(engine = "browser-mtop")
                                                            }
                                                        }
                                                    } catch (_: Exception) {
                                                        // ignore
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "VEBridge",
                                )

                                webChromeClient = object : WebChromeClient() {
                                    override fun onProgressChanged(view: WebView?, newProgress: Int) {
                                        loadProgress = newProgress
                                    }

                                    override fun onReceivedTitle(view: WebView?, title: String?) {
                                        if (!title.isNullOrBlank()) currentTitle = title
                                    }
                                }

                                webViewClient = object : WebViewClient() {
                                    override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                                        super.onPageStarted(view, url, favicon)
                                        view?.evaluateJavascript(SniffHelper.HOOK_JS, null)
                                    }

                                    override fun onPageFinished(view: WebView?, url: String?) {
                                        super.onPageFinished(view, url)
                                        view?.evaluateJavascript(SniffHelper.HOOK_JS, null)
                                    }

                                    override fun shouldInterceptRequest(
                                        view: WebView?,
                                        request: WebResourceRequest?,
                                    ): WebResourceResponse? {
                                        val reqUrl = request?.url?.toString()
                                        if (SniffHelper.looksLikeMediaUrl(reqUrl)) {
                                            recordVideo(reqUrl!!, "browser-sniff")
                                        }
                                        return super.shouldInterceptRequest(view, request)
                                    }
                                }

                                webViewRef = this
                                loadUrl(initialUrl)
                            }
                        },
                        onRelease = { wv ->
                            wv.stopLoading()
                            wv.removeJavascriptInterface("VEBridge")
                            wv.destroy()
                        },
                    )
                }
            }
        }
    }
}

private val ColorBannerBg = androidx.compose.ui.graphics.Color(0xFF064E3B)

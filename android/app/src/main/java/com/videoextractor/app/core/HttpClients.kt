package com.videoextractor.app.core

import android.webkit.CookieManager
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

object HttpClients {
    const val DESKTOP_UA =
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    const val MOBILE_UA =
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"

    const val IPHONE_UA =
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 " +
            "(KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1"

    val default: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .followRedirects(true)
            .followSslRedirects(true)
            .connectTimeout(12, TimeUnit.SECONDS)
            .readTimeout(20, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .build()
    }

    val download: OkHttpClient by lazy {
        val dispatcher = okhttp3.Dispatcher().apply {
            maxRequests = 32
            maxRequestsPerHost = 16
        }
        OkHttpClient.Builder()
            .dispatcher(dispatcher)
            .connectionPool(okhttp3.ConnectionPool(16, 5, TimeUnit.MINUTES))
            .followRedirects(true)
            .followSslRedirects(true)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)
            .build()
    }

    /**
     * Dedicated HTTP/1.1 client for parallel Range chunk downloads.
     * Forcing HTTP/1.1 ensures each worker opens an independent TCP socket instead of
     * multiplexing all chunks onto a single HTTP/2 connection (which CDNs like Douyin/Bilibili
     * throttle per TCP connection).
     */
    val downloadH1: OkHttpClient by lazy {
        val dispatcher = okhttp3.Dispatcher().apply {
            maxRequests = 32
            maxRequestsPerHost = 16
        }
        OkHttpClient.Builder()
            .protocols(listOf(okhttp3.Protocol.HTTP_1_1))
            .dispatcher(dispatcher)
            .connectionPool(okhttp3.ConnectionPool(16, 5, TimeUnit.MINUTES))
            .followRedirects(true)
            .followSslRedirects(true)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)
            .build()
    }

    /** Safely reads cookies stored in local Android WebView CookieManager for a URL. */
    fun webViewCookiesFor(url: String): String? {
        return try {
            CookieManager.getInstance().getCookie(url)?.takeIf { it.isNotBlank() }
        } catch (_: Throwable) {
            null
        }
    }

    /** Parses a Cookie header string (`a=1; b=2`) into a mutable key-value map. */
    fun parseCookieHeader(cookieHeader: String?): MutableMap<String, String> {
        val out = linkedMapOf<String, String>()
        if (cookieHeader.isNullOrBlank()) return out
        for (part in cookieHeader.split(';')) {
            val idx = part.indexOf('=')
            if (idx <= 0) continue
            val k = part.substring(0, idx).trim()
            val v = part.substring(idx + 1).trim()
            if (k.isNotEmpty()) out[k] = v
        }
        return out
    }
}

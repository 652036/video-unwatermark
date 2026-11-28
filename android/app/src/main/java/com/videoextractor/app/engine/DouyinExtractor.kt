package com.videoextractor.app.engine

import com.videoextractor.app.core.HttpClients
import com.videoextractor.app.core.UrlUtils
import com.videoextractor.app.model.ExtractResult
import com.videoextractor.app.model.ExtractedVideo
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject

object DouyinExtractor {
    private val ROUTER_DATA_RE = Regex("""window\._ROUTER_DATA\s*=\s*(\{.*?\})\s*</script>""", RegexOption.DOT_MATCHES_ALL)
    private val VIDEO_MP4_RE = Regex("""https?://[^\s"'<>\\]+?aweme/v1/play(?:wm)?/\?[^\s"'<>\\]+""", RegexOption.IGNORE_CASE)

    fun dewatermark(url: String): String {
        val normalized = normalizeUrl(url) ?: return url
        return normalized.replace("/playwm/", "/play/")
    }

    fun normalizeUrl(raw: String?): String? {
        if (raw.isNullOrBlank()) return null
        val u = raw.trim()
            .replace("\\u002F", "/")
            .replace("\\/", "/")
            .replace("&amp;", "&")
        return when {
            u.startsWith("https://") -> u
            u.startsWith("http://") -> "https://" + u.removePrefix("http://")
            u.startsWith("//") -> "https:$u"
            else -> null
        }
    }

    fun parseRouterDataJson(jsonText: String, pageUrl: String): ExtractResult? {
        return try {
            val root = JSONObject(jsonText)
            val item = findItemInfo(root) ?: return null
            val title = item.optString("desc").ifBlank { "抖音视频" }.lines().first().take(120)
            val video = item.optJSONObject("video")
            val playAddr = video?.optJSONObject("play_addr")
            val urlList = playAddr?.optJSONArray("url_list")
            val rawDirect = firstHttp(urlList)
                ?: video?.optString("vid")?.takeIf { it.isNotBlank() }?.let {
                    "https://aweme.snssdk.com/aweme/v1/play/?video_id=$it&ratio=1080p&line=0"
                }
            val cover = firstHttp(video?.optJSONObject("cover")?.optJSONArray("url_list"))
                ?: firstHttp(video?.optJSONObject("origin_cover")?.optJSONArray("url_list"))

            if (rawDirect.isNullOrBlank()) return null
            ExtractResult.Success(
                ExtractedVideo(
                    title = title,
                    directUrl = dewatermark(rawDirect),
                    pageUrl = pageUrl,
                    platform = "抖音",
                    engine = "douyin-share",
                    thumbnailUrl = cover,
                    headers = mapOf(
                        "User-Agent" to HttpClients.IPHONE_UA,
                        "Referer" to "https://www.iesdouyin.com/",
                    ),
                )
            )
        } catch (_: Exception) {
            null
        }
    }

    fun parseShareHtml(html: String, pageUrl: String): ExtractResult? {
        val match = ROUTER_DATA_RE.find(html)
        if (match != null) {
            parseRouterDataJson(match.groupValues[1], pageUrl)?.let { return it }
        }

        val fallback = VIDEO_MP4_RE.find(html)?.value
        if (fallback != null) {
            return ExtractResult.Success(
                ExtractedVideo(
                    title = "抖音视频",
                    directUrl = dewatermark(fallback),
                    pageUrl = pageUrl,
                    platform = "抖音",
                    engine = "douyin-share",
                    headers = mapOf(
                        "User-Agent" to HttpClients.IPHONE_UA,
                        "Referer" to "https://www.iesdouyin.com/",
                    ),
                )
            )
        }
        return null
    }

    private fun findItemInfo(obj: Any?, depth: Int = 0): JSONObject? {
        if (obj == null || depth > 8) return null
        when (obj) {
            is JSONObject -> {
                if (obj.has("video") && (obj.has("aweme_id") || obj.has("desc"))) {
                    return obj
                }
                obj.optJSONArray("item_list")?.let { arr ->
                    if (arr.length() > 0) arr.optJSONObject(0)?.let { return it }
                }
                val keys = obj.keys()
                while (keys.hasNext()) {
                    val found = findItemInfo(obj.opt(keys.next()), depth + 1)
                    if (found != null) return found
                }
            }
            is JSONArray -> {
                for (i in 0 until minOf(obj.length(), 15)) {
                    val found = findItemInfo(obj.opt(i), depth + 1)
                    if (found != null) return found
                }
            }
        }
        return null
    }

    private fun firstHttp(arr: JSONArray?): String? {
        if (arr == null) return null
        for (i in 0 until arr.length()) {
            val u = normalizeUrl(arr.optString(i))
            if (u != null) return u
        }
        return null
    }

    fun extract(url: String, client: OkHttpClient = HttpClients.default): ExtractResult? {
        val awemeId = UrlUtils.awemeIdOf(url) ?: return null
        val shareUrl = "https://www.iesdouyin.com/share/video/$awemeId/"
        val reqBuilder = Request.Builder()
            .url(shareUrl)
            .header("User-Agent", HttpClients.IPHONE_UA)
            .header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            .header("Accept-Language", "zh-CN,zh;q=0.9")
        HttpClients.webViewCookiesFor(shareUrl)?.let { reqBuilder.header("Cookie", it) }

        return try {
            client.newCall(reqBuilder.build()).execute().use { resp ->
                if (!resp.isSuccessful) return null
                val html = resp.body?.string().orEmpty()
                parseShareHtml(html, url)
            }
        } catch (_: Exception) {
            null
        }
    }
}

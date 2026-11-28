package com.videoextractor.app

import com.videoextractor.app.engine.BilibiliExtractor
import com.videoextractor.app.engine.DouyinExtractor
import com.videoextractor.app.engine.FacebookExtractor
import com.videoextractor.app.engine.GenericHtmlExtractor
import com.videoextractor.app.engine.InstagramExtractor
import com.videoextractor.app.engine.KuaishouExtractor
import com.videoextractor.app.engine.RedditExtractor
import com.videoextractor.app.engine.SniffHelper
import com.videoextractor.app.engine.TikTokExtractor
import com.videoextractor.app.engine.VimeoExtractor
import com.videoextractor.app.engine.XTwitterExtractor
import com.videoextractor.app.engine.XianyuExtractor
import com.videoextractor.app.engine.XiaohongshuExtractor
import com.videoextractor.app.engine.YouTubeExtractor
import com.videoextractor.app.model.ExtractResult
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ParsersTest {

    @Test
    fun douyinShareHtmlParsesAndRemovesPlaywm() {
        val html = """
            <html><script>window._ROUTER_DATA = {
              "loaderData": {
                "video_(id)/page": {
                  "videoInfoRes": {
                    "item_list": [{
                      "aweme_id": "7321000000000000001",
                      "desc": "测试抖音标题",
                      "video": {
                        "play_addr": {"url_list": ["https://aweme.snssdk.com/aweme/v1/playwm/?video_id=v0200&ratio=720p"]},
                        "cover": {"url_list": ["https://p3.douyinpic.com/cover.jpeg"]}
                      }
                    }]
                  }
                }
              }
            }</script></html>
        """.trimIndent()
        val res = DouyinExtractor.parseShareHtml(html, "https://www.douyin.com/video/7321000000000000001")
        assertTrue(res is ExtractResult.Success)
        val vid = (res as ExtractResult.Success).video
        assertEquals("测试抖音标题", vid.title)
        assertEquals("https://aweme.snssdk.com/aweme/v1/play/?video_id=v0200&ratio=720p", vid.directUrl)
    }

    @Test
    fun kuaishouShareHtmlRanksCleanMp4First() {
        val html = """
            <script>window.INIT_STATE = {
              "photo": {
                "caption": "快手测试",
                "photoUrl": "https://txmov2.a.kwaicdn.com/upic/2026/video_clean.mp4",
                "previewUrl": "https://cdn.example.com/preview_video.mp4"
              }
            };</script>
        """.trimIndent()
        val res = KuaishouExtractor.parseShareHtml(html, "https://www.kuaishou.com/short-video/3xabc123")
        assertTrue(res is ExtractResult.Success)
        val vid = (res as ExtractResult.Success).video
        assertEquals("https://txmov2.a.kwaicdn.com/upic/2026/video_clean.mp4", vid.directUrl)
    }

    @Test
    fun xianyuParsesPcItemDoH5ItemDoImageOnlyAndRisk() {
        val pcJson = JSONObject(
            """
            {
              "ret": ["SUCCESS::调用成功"],
              "data": {
                "itemDO": {
                  "itemId": "1101224115545",
                  "title": "PC 测试商品",
                  "videoPlayInfo": {
                    "playUrl": "https://cloud.video.taobao.com/play/u/1/p/1/e/6/t/1/sd.mp4",
                    "mtsVid": "55667788"
                  }
                }
              }
            }
            """.trimIndent()
        )
        val pcParsed = XianyuExtractor.parseDetailPayload(pcJson, "https://h5.m.goofish.com/item?id=1101224115545")
        assertTrue(pcParsed.result is ExtractResult.Success)
        assertEquals("55667788", pcParsed.mtsVid)

        val h5Json = JSONObject(
            """
            {
              "ret": ["SUCCESS::调用成功"],
              "data": {
                "itemDo": {
                  "itemId": "1101224115545",
                  "desc": "H5 游客商品",
                  "videoPlayInfo": {
                    "sd480pUrl": "//cloud.video.taobao.com/play/h5_480p.mp4"
                  }
                }
              }
            }
            """.trimIndent()
        )
        val h5Parsed = XianyuExtractor.parseDetailPayload(h5Json, "https://h5.m.goofish.com/item?id=1101224115545")
        assertTrue(h5Parsed.result is ExtractResult.Success)
        assertEquals(
            "https://cloud.video.taobao.com/play/h5_480p.mp4",
            (h5Parsed.result as ExtractResult.Success).video.directUrl,
        )

        val vqJson = JSONObject(
            """{"data":{"cdnVideo":{"resources":[{"video_url":"https://cloud.video.taobao.com/play/ud_hd.mp4"}]}}}"""
        )
        assertEquals("https://cloud.video.taobao.com/play/ud_hd.mp4", XianyuExtractor.parseVideoQuery(vqJson))

        val imageOnly = JSONObject(
            """{"ret":["SUCCESS::调用成功"],"data":{"itemDO":{"itemId":"123","title":"仅图片","imageInfos":[{"url":"https://img.alicdn.com/a.jpg"}]}}}"""
        )
        assertTrue(XianyuExtractor.parseDetailPayload(imageOnly, "https://h5.m.goofish.com/item?id=123").result is ExtractResult.NoVideo)

        val risk = JSONObject(
            """{"ret":["RGV587_ERROR::SM::被挤爆啦"],"data":{"url":"https://passport.goofish.com/mini_login.htm"}}"""
        )
        assertTrue(XianyuExtractor.parseDetailPayload(risk, "https://h5.m.goofish.com/item?id=123").result is ExtractResult.NeedsAuth)
    }

    @Test
    fun xhsParsesInitialStateWithUndefinedAndOriginVideoKey() {
        val html = """
            <html><script>window.__INITIAL_STATE__ = {"note":{"title":"小红书测试","extra":undefined,"video":{"consumer":{"originVideoKey":"spectrum/abc123.mp4"}}}}</script></html>
        """.trimIndent()
        val res = XiaohongshuExtractor.parseHtml(html, "https://www.xiaohongshu.com/explore/66a1b2c3000000001e01abcd")
        assertTrue(res is ExtractResult.Success)
        val vid = (res as ExtractResult.Success).video
        assertEquals("https://sns-video-bd.xhscdn.com/spectrum/abc123.mp4", vid.directUrl)
    }

    @Test
    fun bilibiliParsesViewAndProgressivePlayUrl() {
        val view = JSONObject("""{"code":0,"data":{"bvid":"BV1xx411c7mD","cid":123456,"title":"B站测试","pic":"http://i0.hdslb.com/cover.jpg"}}""")
        val info = BilibiliExtractor.parseViewPayload(view)
        assertEquals("BV1xx411c7mD", info?.bvid)
        assertEquals(123456L, info?.cid)

        val play = JSONObject("""{"code":0,"data":{"durl":[{"url":"https://upos-sz-mirror.bilivideo.com/test.mp4","size":9876543}]}}""")
        val (url, size) = BilibiliExtractor.parsePlayUrlPayload(play)!!
        assertEquals("https://upos-sz-mirror.bilivideo.com/test.mp4", url)
        assertEquals(9876543L, size)
    }

    @Test
    fun genericHtmlAndSniffHelper() {
        val html = """<html><head><meta property="og:title" content="测试网页"/><meta property="og:video" content="https://cdn.example.com/demo.mp4"/></head></html>"""
        val res = GenericHtmlExtractor.parseHtml(html, "https://example.com/post/1")
        assertTrue(res is ExtractResult.Success)
        assertEquals("https://cdn.example.com/demo.mp4", (res as ExtractResult.Success).video.directUrl)

        assertTrue(SniffHelper.looksLikeMediaUrl("https://cloud.video.taobao.com/play/u/1/test.mp4"))
        assertTrue(SniffHelper.looksLikeMediaUrl("https://video.twimg.com/ext_tw_video/1/pu/vid/720x1280/a.mp4"))
        assertTrue(SniffHelper.looksLikeMediaUrl("https://v9-colds.douyinvod.com/abc/video/tos/cn/tos-cn-ve-15/xyz"))
        assertTrue(SniffHelper.looksLikeMediaUrl("https://v5-dy-ov-experiment.zjcdn.com/abc/video/tos/cn/xyz"))
        assertFalse(SniffHelper.looksLikeMediaUrl("https://bixi.alicdn.com/punish/captcha.mp4"))
        assertFalse(SniffHelper.looksLikeMediaUrl("https://cdn.example.com/static/app.js"))
    }

    @Test
    fun youtubeParsesProgressiveMp4AndLoginWall() {
        val okJson = JSONObject(
            """
            {
              "playabilityStatus": {"status": "OK"},
              "videoDetails": {"title": "Demo YT Video", "thumbnail": {"thumbnails": [{"url": "https://i.ytimg.com/vi/abc/hq.jpg"}]}},
              "streamingData": {
                "formats": [
                  {"mimeType": "video/mp4; codecs=\"avc1\"", "height": 360, "url": "https://rr1.googlevideo.com/videoplayback?itag=18"},
                  {"mimeType": "video/mp4; codecs=\"avc1\"", "height": 720, "contentLength": "12345678", "url": "https://rr1.googlevideo.com/videoplayback?itag=22"}
                ]
              }
            }
            """.trimIndent()
        )
        val okRes = YouTubeExtractor.parsePlayerResponse(okJson, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assertTrue(okRes is ExtractResult.Success)
        val vid = (okRes as ExtractResult.Success).video
        assertEquals("https://rr1.googlevideo.com/videoplayback?itag=22", vid.directUrl)
        assertEquals(12345678L, vid.filesizeBytes)

        val loginJson = JSONObject("""{"playabilityStatus": {"status": "LOGIN_REQUIRED", "reason": "Sign in to confirm you're not a bot"}}""")
        assertTrue(YouTubeExtractor.parsePlayerResponse(loginJson, "https://www.youtube.com/watch?v=dQw4w9WgXcQ") is ExtractResult.NeedsAuth)
    }

    @Test
    fun tiktokParsesUniversalRehydrationData() {
        val html = """
            <html><script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">
            {"__DEFAULT_SCOPE__":{"webapp.video-detail":{"itemInfo":{"itemStruct":{"desc":"TikTok Demo","video":{"playAddr":"https://v16.tiktokcdn.com/video/tos/clean.mp4","cover":"https://p16.tiktokcdn.com/cover.jpg"}}}}}}
            </script></html>
        """.trimIndent()
        val res = TikTokExtractor.parseHtml(html, "https://www.tiktok.com/@demo/video/7321000000000000001")
        assertTrue(res is ExtractResult.Success)
        assertEquals("https://v16.tiktokcdn.com/video/tos/clean.mp4", (res as ExtractResult.Success).video.directUrl)
    }

    @Test
    fun xTwitterSelectsHighestBitrateMp4() {
        val syn = JSONObject(
            """
            {
              "text": "Hello X video",
              "mediaDetails": [{
                "media_url_https": "https://pbs.twimg.com/thumb.jpg",
                "video_info": {
                  "variants": [
                    {"content_type": "application/x-mpegURL", "url": "https://video.twimg.com/a.m3u8"},
                    {"content_type": "video/mp4", "bitrate": 832000, "url": "https://video.twimg.com/sd.mp4"},
                    {"content_type": "video/mp4", "bitrate": 2176000, "url": "https://video.twimg.com/hd.mp4"}
                  ]
                }
              }]
            }
            """.trimIndent()
        )
        val res = XTwitterExtractor.parseSyndicationPayload(syn, "https://x.com/i/status/1850000000000000001")
        assertTrue(res is ExtractResult.Success)
        assertEquals("https://video.twimg.com/hd.mp4", (res as ExtractResult.Success).video.directUrl)
    }

    @Test
    fun instagramFacebookRedditAndVimeoParsers() {
        val igHtml = """<html><meta property="og:title" content="IG Reel"/><script>{"video_url":"https:\/\/scontent.cdninstagram.com\/v\/reel.mp4"}</script></html>"""
        val igRes = InstagramExtractor.parseHtml(igHtml, "https://www.instagram.com/reel/C9AbCdEf123/")
        assertTrue(igRes is ExtractResult.Success)
        assertEquals("https://scontent.cdninstagram.com/v/reel.mp4", (igRes as ExtractResult.Success).video.directUrl)

        val fbHtml = """<html><meta property="og:title" content="FB Clip"/><script>{"browser_native_hd_url":"https:\/\/video.fbcdn.net\/hd.mp4","browser_native_sd_url":"https:\/\/video.fbcdn.net\/sd.mp4"}</script></html>"""
        val fbRes = FacebookExtractor.parseHtml(fbHtml, "https://www.facebook.com/watch/?v=123")
        assertTrue(fbRes is ExtractResult.Success)
        assertEquals("https://video.fbcdn.net/hd.mp4", (fbRes as ExtractResult.Success).video.directUrl)

        val redditJson = """[{"data":{"children":[{"data":{"title":"Reddit Clip","secure_media":{"reddit_video":{"fallback_url":"https://v.redd.it/abc/DASH_720.mp4"}}}}]}}]"""
        val redditRes = RedditExtractor.parseListingJson(redditJson, "https://www.reddit.com/r/videos/comments/abc/demo/")
        assertTrue(redditRes is ExtractResult.Success)
        assertEquals("https://v.redd.it/abc/DASH_720.mp4", (redditRes as ExtractResult.Success).video.directUrl)

        val vimeoCfg = JSONObject("""{"video":{"title":"Vimeo Film","thumbs":{"1280":"https://i.vimeocdn.com/t.jpg"}},"request":{"files":{"progressive":[{"height":360,"url":"https://vod.vimeocdn.com/360.mp4"},{"height":1080,"url":"https://vod.vimeocdn.com/1080.mp4"}]}}}""")
        val vimeoRes = VimeoExtractor.parsePlayerConfig(vimeoCfg, "https://vimeo.com/76979871")
        assertTrue(vimeoRes is ExtractResult.Success)
        assertEquals("https://vod.vimeocdn.com/1080.mp4", (vimeoRes as ExtractResult.Success).video.directUrl)
    }

    @Test
    fun downloaderRangeChunkingAndProbeParsing() {
        assertEquals(1, com.videoextractor.app.download.MediaDownloader.chooseThreadCount(300_000L))
        assertEquals(4, com.videoextractor.app.download.MediaDownloader.chooseThreadCount(1_000_000L))
        assertEquals(6, com.videoextractor.app.download.MediaDownloader.chooseThreadCount(6_000_000L))
        assertEquals(8, com.videoextractor.app.download.MediaDownloader.chooseThreadCount(20_000_000L))

        val total = 10L * 1024 * 1024
        val segments = com.videoextractor.app.download.MediaDownloader.computeSegments(total, 6)
        assertTrue(segments.size >= 6)
        assertEquals(0L, segments.first().first)
        assertEquals(total - 1, segments.last().last)
        for (i in 1 until segments.size) {
            assertEquals(segments[i - 1].last + 1, segments[i].first)
        }

        assertEquals(
            28083412L,
            com.videoextractor.app.download.MediaDownloader.parseTotalFromContentRange("bytes 0-1/28083412"),
        )
    }
}

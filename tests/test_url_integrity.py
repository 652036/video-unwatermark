"""Offline regressions for escaped URLs and platform host boundaries."""
from __future__ import annotations

import unittest

from app.urls import is_cn_short_video, is_douyin, is_kuaishou, variants_for, ytdlp_url
from app.util import _clean_url, extract_url, hostname_of, is_blocked, platform_of


class UrlIntegrityTests(unittest.TestCase):
    def test_signed_query_is_preserved(self) -> None:
        url = "https://cdn.example.invalid/a.mp4?signature=A%2FB%2BC%3D&metadata=x%26y%3Dz"
        self.assertEqual(extract_url(url), url)

    def test_reserved_path_characters_stay_escaped(self) -> None:
        for escaped in ("%2F", "%3F", "%23", "%20", "%25", "%29", "%E4%BD%A0"):
            with self.subTest(escaped=escaped):
                url = f"https://example.invalid/video/{escaped}"
                self.assertEqual(extract_url(url), url)

    def test_share_text_removes_outer_punctuation_not_encoded_payload(self) -> None:
        url = "https://example.invalid/video/id%29?token=abc%26def"
        self.assertEqual(extract_url(f"分享视频：{url}。 后续文字"), url)

    def test_cleaning_does_not_repeatedly_decode_nested_escapes(self) -> None:
        url = "https://example.invalid/video/id%252Fpart?token=%2526value"
        self.assertEqual(_clean_url(_clean_url(url)), url)

    def test_plain_url_and_missing_url_behavior_is_unchanged(self) -> None:
        self.assertEqual(extract_url("see https://example.invalid/video/123。"),
                         "https://example.invalid/video/123")
        self.assertIsNone(extract_url("no link here"))
        self.assertIsNone(extract_url(""))

    def test_real_platform_domains_and_subdomains_match(self) -> None:
        for domain, predicate in (
            ("douyin.com", is_douyin), ("iesdouyin.com", is_douyin),
            ("kuaishou.com", is_kuaishou), ("kuaishouapp.com", is_kuaishou),
            ("chenzhongtech.com", is_kuaishou), ("kwai.com", is_kuaishou),
            ("gifshow.com", is_kuaishou),
        ):
            for prefix in ("", "www.", "v.m."):
                with self.subTest(domain=domain, prefix=prefix):
                    self.assertTrue(predicate(f"https://{prefix}{domain}/video/123"))

    def test_prefix_lookalikes_are_not_platform_hosts(self) -> None:
        for domain in ("douyin.com", "iesdouyin.com", "kuaishou.com", "kuaishouapp.com",
                       "chenzhongtech.com", "kwai.com", "gifshow.com"):
            with self.subTest(domain=domain):
                self.assertFalse(is_cn_short_video(f"https://not{domain}/video/123"))

    def test_platform_text_outside_the_hostname_does_not_match(self) -> None:
        for url in (
            "https://douyin.com.example.invalid/video/123",
            "https://douyin.com@example.invalid/video/123",
            "https://example.invalid/douyin.com/video/123",
            "https://example.invalid/?next=https://kuaishou.com/short-video/abc",
        ):
            with self.subTest(url=url):
                self.assertFalse(is_cn_short_video(url))

    def test_lookalike_urls_are_not_rewritten_to_unrelated_platform_videos(self) -> None:
        for url in ("https://notdouyin.com/video/123", "https://notkuaishou.com/short-video/abc"):
            with self.subTest(url=url):
                self.assertEqual(ytdlp_url(url), url)
                self.assertEqual(variants_for(url), [url])

    def test_known_platform_rewrite_remains_supported(self) -> None:
        self.assertEqual(ytdlp_url("https://www.iesdouyin.com/share/video/123"),
                         "https://www.douyin.com/video/123")

    def test_dns_root_dot_is_normalized_consistently(self) -> None:
        self.assertEqual(hostname_of("https://WWW.DOUYIN.COM./video/1"), "douyin.com")
        self.assertTrue(is_douyin("https://WWW.DOUYIN.COM./video/1"))
        self.assertEqual(platform_of("https://WWW.KUAISHOU.COM./short-video/abc"), "快手")

    def test_existing_platform_blocklist_also_handles_dns_root_dot(self) -> None:
        self.assertEqual(is_blocked("https://www.netflix.com./title/1"), "Netflix")
        self.assertEqual(is_blocked("https://v.qq.com./video/1"), "腾讯视频")
        self.assertIsNone(is_blocked("https://example.invalid/video/1"))


if __name__ == "__main__":
    unittest.main()

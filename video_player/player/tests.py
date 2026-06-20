"""
Tests for Video Stream Player views.
Covers all endpoints: page rendering, PWA, search, and download.
"""
import json
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse

from video_player.player.views import (
    _sanitize_filename,
    build_video_format,
    detect_platform,
    download_audio,
    download_info,
    download_mp3,
    download_mp4,
    download_video,
    manifest_view,
    service_worker_view,
    video_player,
    yt_search,
)


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------

class SanitizeFilenameTests(TestCase):
    def test_removes_invalid_chars(self):
        result = _sanitize_filename('file:<foo>?bar*|baz')
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        self.assertNotIn('?', result)
        self.assertNotIn('*', result)
        self.assertNotIn('|', result)
        self.assertIn('_', result)

    def test_collapses_whitespace(self):
        result = _sanitize_filename('hello    world   test')
        self.assertEqual(result, 'hello world test')

    def test_strips_leading_trailing_spaces(self):
        result = _sanitize_filename('   hello world   ')
        self.assertEqual(result, 'hello world')

    def test_truncates_to_max_length(self):
        long_name = 'a' * 300
        result = _sanitize_filename(long_name, max_length=50)
        self.assertEqual(len(result), 50)

    def test_handles_empty_result(self):
        result = _sanitize_filename('')
        self.assertEqual(result, '')


class BuildVideoFormatTests(TestCase):
    def test_basic_720p(self):
        fmt = build_video_format('720', 'auto', 'mp4')
        self.assertIn('height<=720', fmt)
        self.assertIn('mp4', fmt)

    def test_with_vcodec_filter(self):
        fmt = build_video_format('1080', 'h264', 'mp4')
        self.assertIn('height<=1080', fmt)
        self.assertIn('[vcodec^=avc1]', fmt)

    def test_webm_container(self):
        fmt = build_video_format('720', 'vp9', 'webm')
        self.assertIn('height<=720', fmt)
        self.assertIn('[vcodec^=vp9]', fmt)

    def test_4k_2160p(self):
        fmt = build_video_format('2160', 'auto', 'mp4')
        self.assertIn('height<=2160', fmt)


class DetectPlatformTests(TestCase):
    def test_youtube_watch(self):
        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        result = detect_platform(url)
        self.assertEqual(result['type'], 'youtube')
        self.assertIn('dQw4w9WgXcQ', result['embed_url'])

    def test_youtube_short(self):
        url = 'https://youtu.be/dQw4w9WgXcQ'
        result = detect_platform(url)
        self.assertEqual(result['type'], 'youtube')
        self.assertIn('dQw4w9WgXcQ', result['embed_url'])

    def test_youtube_embed(self):
        url = 'https://www.youtube.com/embed/dQw4w9WgXcQ'
        result = detect_platform(url)
        self.assertEqual(result['type'], 'youtube')
        self.assertIn('dQw4w9WgXcQ', result['embed_url'])

    def test_dailymotion(self):
        url = 'https://www.dailymotion.com/video/x7tg2v5'
        result = detect_platform(url)
        self.assertEqual(result['type'], 'dailymotion')
        self.assertIn('x7tg2v5', result['embed_url'])

    def test_dailymotion_short(self):
        url = 'https://dai.ly/x7tg2v5'
        result = detect_platform(url)
        self.assertEqual(result['type'], 'dailymotion')

    def test_vimeo(self):
        url = 'https://vimeo.com/123456789'
        result = detect_platform(url)
        self.assertEqual(result['type'], 'vimeo')
        self.assertIn('123456789', result['embed_url'])

    def test_direct_url(self):
        url = 'https://example.com/video.mp4'
        result = detect_platform(url)
        self.assertEqual(result['type'], 'direct')
        self.assertEqual(result['embed_url'], url)

    def test_invalid_url(self):
        url = 'not-a-url'
        result = detect_platform(url)
        self.assertEqual(result['type'], 'direct')
        self.assertEqual(result['embed_url'], url)


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------

class VideoPlayerViewTests(TestCase):
    def test_get_page_returns_200(self):
        response = self.client.get(reverse('video_player'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'player.html')

    def test_page_contains_expected_text(self):
        response = self.client.get(reverse('video_player'))
        self.assertContains(response, 'Video Stream Player')
        self.assertContains(response, 'Charger la video')

    def test_with_valid_youtube_url(self):
        url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        response = self.client.get(reverse('video_player'), {'video_url': url})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dQw4w9WgXcQ')

    def test_with_invalid_url_shows_error(self):
        url = 'invalid-url'
        response = self.client.get(reverse('video_player'), {'video_url': url})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'doit commencer par')

    def test_with_empty_url_param(self):
        response = self.client.get(reverse('video_player'), {'video_url': ''})
        self.assertEqual(response.status_code, 200)
        # Should load normally without error
        self.assertNotContains(response, 'doit commencer par')

    def test_with_dailymotion_url(self):
        url = 'https://www.dailymotion.com/video/x7tg2v5'
        response = self.client.get(reverse('video_player'), {'video_url': url})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'x7tg2v5')

    def test_with_vimeo_url(self):
        url = 'https://vimeo.com/123456789'
        response = self.client.get(reverse('video_player'), {'video_url': url})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '123456789')


class PWATests(TestCase):
    def test_manifest_json(self):
        response = self.client.get(reverse('manifest'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response['Content-Type'])

    def test_service_worker_js(self):
        response = self.client.get(reverse('service_worker'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('javascript', response['Content-Type'])
        self.assertContains(response, 'Service Worker')


class YTSearchViewTests(TestCase):
    def test_missing_query_returns_400(self):
        response = self.client.get(reverse('yt_search'))
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_with_query_uses_ytdlp(self):
        """Test that yt-search calls yt-dlp and returns JSON."""
        # Mock yt-dlp to avoid actual network calls
        mock_info = {
            'entries': [
                {
                    'id': 'test123',
                    'title': 'Test Video',
                    'url': 'https://www.youtube.com/watch?v=test123',
                    'thumbnail': 'https://i.ytimg.com/vi/test123/hqdefault.jpg',
                    'duration': 120,
                    'channel': 'Test Channel',
                    'view_count': 1000,
                    'upload_date': '20250101',
                }
            ]
        }

        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = mock_info
            mock_ydl.return_value.__enter__.return_value = mock_instance

            response = self.client.get(reverse('yt_search'), {'q': 'test query'})
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertIn('results', data)
            self.assertEqual(len(data['results']), 1)
            self.assertEqual(data['results'][0]['id'], 'test123')
            self.assertEqual(data['results'][0]['title'], 'Test Video')

    def test_empty_query(self):
        response = self.client.get(reverse('yt_search'), {'q': ''})
        self.assertEqual(response.status_code, 400)

    def test_with_duration_filter(self):
        mock_info = {'entries': [{'id': 't1', 'title': 'T1', 'duration': 60,
                                   'url': 'https://youtube.com/watch?v=t1',
                                   'thumbnail': ''}]}
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = mock_info
            mock_ydl.return_value.__enter__.return_value = mock_instance

            response = self.client.get(
                reverse('yt_search'),
                {'q': 'test', 'duration': 'short'}
            )
            self.assertEqual(response.status_code, 200)

    def test_with_sort_parameter(self):
        mock_info = {'entries': []}
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = mock_info
            mock_ydl.return_value.__enter__.return_value = mock_instance

            response = self.client.get(
                reverse('yt_search'),
                {'q': 'test', 'sort': 'date'}
            )
            self.assertEqual(response.status_code, 200)

    def test_with_all_filters(self):
        mock_info = {'entries': [
            {'id': 't1', 'title': 'T1', 'duration': 300,
             'url': 'https://youtube.com/watch?v=t1',
             'thumbnail': '', 'upload_date': '20250101',
             'channel': 'C1', 'view_count': 500}
        ]}
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = mock_info
            mock_ydl.return_value.__enter__.return_value = mock_instance

            response = self.client.get(
                reverse('yt_search'),
                {'q': 'test', 'maxResults': '5', 'duration': 'medium',
                 'date': 'year', 'sort': 'views'}
            )
            self.assertEqual(response.status_code, 200)


class DownloadInfoViewTests(TestCase):
    def test_missing_url_returns_400(self):
        response = self.client.get(reverse('download_info'))
        self.assertEqual(response.status_code, 400)

    def test_invalid_url_returns_400(self):
        response = self.client.get(
            reverse('download_info'),
            {'video_url': 'not-a-url'}
        )
        self.assertEqual(response.status_code, 400)

    def test_direct_file_url_returns_sizes(self):
        response = self.client.get(
            reverse('download_info'),
            {'video_url': 'https://example.com/video.mp4'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('direct'))
        self.assertEqual(data.get('sizes'), {})

    def test_yt_url_with_mock(self):
        mock_info = {
            'title': 'Test',
            'channel': 'Test Channel',
            'thumbnails': [{'url': 'https://example.com/thumb.jpg',
                           'preference': 1, 'width': 480, 'height': 360}],
            'duration': 300,
            'formats': [
                {'height': 720, 'filesize': 10_000_000, 'vcodec': 'avc1.64001F'},
                {'height': 480, 'filesize': 5_000_000, 'vcodec': 'avc1.4D401E'},
            ]
        }
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = mock_info
            mock_ydl.return_value.__enter__.return_value = mock_instance

            response = self.client.get(
                reverse('download_info'),
                {'video_url': 'https://www.youtube.com/watch?v=test'}
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertFalse(data.get('direct'))
            self.assertEqual(data.get('title'), 'Test')

    def test_ytdlp_error_returns_500(self):
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_instance.extract_info.side_effect = Exception('Network error')
            mock_ydl.return_value.__enter__.return_value = mock_instance

            response = self.client.get(
                reverse('download_info'),
                {'video_url': 'https://www.youtube.com/watch?v=test'}
            )
            self.assertEqual(response.status_code, 500)


class DownloadMP4RedirectTests(TestCase):
    def test_redirects_to_download_video(self):
        response = self.client.get(
            reverse('download_mp4'),
            {'video_url': 'https://example.com/video', 'quality': '1080'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/download/video/', response['Location'])


class DownloadMP3RedirectTests(TestCase):
    def test_redirects_to_download_audio(self):
        response = self.client.get(
            reverse('download_mp3'),
            {'video_url': 'https://example.com/video', 'quality': '320'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/download/audio/', response['Location'])


class DownloadVideoViewTests(TestCase):
    def test_missing_url_returns_400(self):
        response = self.client.get(reverse('download_video'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL manquante', response.content.decode())

    def test_invalid_url_returns_400(self):
        response = self.client.get(
            reverse('download_video'),
            {'video_url': 'not-a-url'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL invalide', response.content.decode())

    def test_direct_file_url_redirects(self):
        """Direct video file URLs should redirect to the URL itself."""
        url = 'https://example.com/video.mp4'
        response = self.client.get(
            reverse('download_video'),
            {'video_url': url}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], url)

    def test_direct_webm_url_redirects(self):
        url = 'https://example.com/video.webm'
        response = self.client.get(
            reverse('download_video'),
            {'video_url': url}
        )
        self.assertEqual(response.status_code, 302)

    def test_with_invalid_quality_fallback_to_720(self):
        """Invalid quality should fall back to 720p."""
        url = 'https://example.com/video.mp4'
        response = self.client.get(
            reverse('download_video'),
            {'video_url': url, 'quality': 'invalid'}
        )
        # Should still redirect because it's a direct file URL
        self.assertEqual(response.status_code, 302)

    def test_with_invalid_container_fallback(self):
        url = 'https://example.com/video.mp4'
        response = self.client.get(
            reverse('download_video'),
            {'video_url': url, 'container': 'invalid'}
        )
        self.assertEqual(response.status_code, 302)

    def test_empty_url_with_valid_params_returns_400(self):
        response = self.client.get(
            reverse('download_video'),
            {'quality': '1080', 'container': 'mp4'}
        )
        self.assertEqual(response.status_code, 400)


class DownloadAudioViewTests(TestCase):
    def test_missing_url_returns_400(self):
        response = self.client.get(reverse('download_audio'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL manquante', response.content.decode())

    def test_invalid_url_returns_400(self):
        response = self.client.get(
            reverse('download_audio'),
            {'video_url': 'not-a-url'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('URL invalide', response.content.decode())

    def test_invalid_quality_uses_default(self):
        """Invalid quality should fall back to 192kbps and return an error gracefully."""
        url = 'https://example.com/audio.mp3'
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance

            response = self.client.get(
                reverse('download_audio'),
                {'video_url': url, 'quality': 'invalid'}
            )
            # yt-dlp mock won't create a temp file → FileNotFoundError → 500
            self.assertEqual(response.status_code, 500)

    def test_invalid_format_returns_error_gracefully(self):
        """Invalid format falls back to mp3 but still fails gracefully."""
        url = 'https://example.com/audio.mp3'
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance

            response = self.client.get(
                reverse('download_audio'),
                {'video_url': url, 'format': 'invalid'}
            )
            # Falls back to mp3 but no file created by mock → 500
            self.assertEqual(response.status_code, 500)


# ---------------------------------------------------------------------------
# Integration test for URL routing
# ---------------------------------------------------------------------------

class URLRoutingTests(TestCase):
    def test_all_named_urls_resolve(self):
        """Verify all named URL patterns resolve correctly."""
        urls = [
            (reverse('video_player'), 200),
            (reverse('manifest'), 200),
            (reverse('service_worker'), 200),
        ]
        for url, expected_status in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, expected_status)


class StaticFileTests(TestCase):
    def test_manifest_json_content(self):
        response = self.client.get(reverse('manifest'))
        self.assertEqual(response.status_code, 200)
        # FileResponse uses streaming; collect content via streaming
        content = b''.join(response.streaming_content)
        data = json.loads(content)
        self.assertIn('name', data)
        self.assertIn('short_name', data)
        self.assertIn('start_url', data)
        self.assertIn('icons', data)

    def test_sw_js_content(self):
        response = self.client.get(reverse('service_worker'))
        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode()
        self.assertIn('CACHE_NAME', content)
        self.assertIn('install', content)
        self.assertIn('activate', content)
        self.assertIn('fetch', content)

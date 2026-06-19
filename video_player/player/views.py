import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import requests
import yt_dlp
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)

METADATA_COMMENT = "Telecharge avec Video Player"


def _get_ffmpeg_path():
    path = os.path.join(os.getcwd(), 'ffmpeg.exe')
    if os.path.exists(path):
        return path
    return 'ffmpeg'


def _stream_ytdlp(args, content_type, filename):
    """Lance yt-dlp en sous-processus et streame la sortie vers le client."""
    def generate():
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            for chunk in iter(lambda: proc.stdout.read(65536), b''):
                yield chunk
        finally:
            proc.wait()
            if proc.returncode != 0:
                stderr_output = proc.stderr.read().decode('utf-8', errors='replace')[:500]
                logger.error('yt-dlp failed (code %s): %s', proc.returncode, stderr_output)

    response = StreamingHttpResponse(generate(), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _stream_and_cleanup(filepath, content_type, filename):
    """Lit un fichier, le streame au client, puis le supprime."""
    def generate():
        try:
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    yield chunk
        finally:
            try:
                os.remove(filepath)
                parent = os.path.dirname(filepath)
                if os.path.isdir(parent):
                    try:
                        os.rmdir(parent)
                    except OSError:
                        pass
            except OSError:
                pass

    response = StreamingHttpResponse(generate(), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _sanitize_filename(name, max_length=200):
    """Nettoie une chaine pour usage comme nom de fichier."""
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:max_length]


# ---------------------------------------------------------------------------
# Metadonnees enrichies
# ---------------------------------------------------------------------------

def _extract_metadata(video_url):
    """Extrait les metadonnees enrichies d'une video via yt-dlp (sans telechargement)."""
    if video_url.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov', '.mp3', '.m4a', '.flac', '.wav')):
        return {}
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'no_call_home': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return _build_metadata_dict(info)
    except Exception as e:
        logger.warning('Extraction metadonnees echouee: %s', e)
        return {}


def _build_metadata_dict(info):
    """Construit un dictionnaire de metadonnees enrichi a partir des infos yt-dlp."""
    if not info:
        return {}

    title = info.get('title', '')
    uploader = info.get('uploader', '') or ''
    channel = info.get('channel', '') or uploader
    upload_date = info.get('upload_date', '')
    description = (info.get('description') or '')[:500]
    tags = info.get('tags') or []
    categories = info.get('categories') or []
    track = info.get('track') or title
    artist = info.get('artist') or uploader
    album = info.get('album') or channel
    release_year = info.get('release_year')
    playlist_index = info.get('playlist_index')
    webpage_url = info.get('webpage_url', '')

    year = ''
    if release_year:
        year = str(release_year)
    elif upload_date and len(upload_date) >= 4:
        year = upload_date[:4]

    genre = ', '.join(tags[:3]) if tags else (categories[0] if categories else 'Web')

    thumbs = info.get('thumbnails') or []
    thumbnail_url = ''
    if thumbs:
        sorted_t = sorted(
            (t for t in thumbs if t.get('url')),
            key=lambda t: (t.get('preference') or -1, t.get('width') or 0, t.get('height') or 0),
            reverse=True
        )
        if sorted_t:
            thumbnail_url = sorted_t[0].get('url', '')

    track_number = playlist_index if (playlist_index and info.get('playlist_count', 1) > 1) else None

    return {
        'title': title,
        'artist': artist,
        'channel': channel,
        'album': album,
        'year': year,
        'genre': genre,
        'description': description,
        'track': track,
        'track_number': track_number,
        'thumbnail_url': thumbnail_url,
        'webpage_url': webpage_url,
        'upload_date': upload_date,
    }


def _fetch_cover_data(thumbnail_url, max_size=1200):
    """Telecharge une image de couverture et la convertit en JPEG optimise."""
    try:
        resp = requests.get(thumbnail_url, timeout=15)
        resp.raise_for_status()

        from PIL import Image
        img = Image.open(BytesIO(resp.content))

        if img.mode != 'RGB':
            img = img.convert('RGB')

        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)

        output = BytesIO()
        img.save(output, format='JPEG', quality=92, optimize=True)
        return output.getvalue(), 'image/jpeg'
    except Exception as e:
        logger.warning('Telechargement couverture echoue: %s', e)
        return None, None


# ---------------------------------------------------------------------------
# Tags ID3 (MP3) via mutagen
# ---------------------------------------------------------------------------

def _apply_mp3_metadata(filepath, meta):
    """Applique des tags ID3v2.4 enrichis a un fichier MP3."""
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, TRCK, COMM, TPE2, APIC
    from mutagen.mp3 import MP3

    try:
        tags = ID3(filepath)
    except Exception:
        audio = MP3(filepath)
        audio.add_tags()
        tags = audio.tags

    frames = []

    if meta.get('title'):
        frames.append(TIT2(encoding=3, text=meta['title']))
    if meta.get('artist'):
        frames.append(TPE1(encoding=3, text=meta['artist']))
    if meta.get('album'):
        frames.append(TALB(encoding=3, text=meta['album']))
    if meta.get('channel'):
        frames.append(TPE2(encoding=3, text=meta['channel']))
    if meta.get('year'):
        frames.append(TDRC(encoding=3, text=meta['year']))
    if meta.get('genre'):
        frames.append(TCON(encoding=3, text=meta['genre']))
    if meta.get('track_number'):
        frames.append(TRCK(encoding=3, text=str(meta['track_number'])))

    comment_parts = [METADATA_COMMENT]
    if meta.get('webpage_url'):
        comment_parts.append(f"Source: {meta['webpage_url']}")
    frames.append(COMM(encoding=3, lang='eng', desc='Comment', text=' | '.join(comment_parts)))

    if meta.get('description'):
        frames.append(COMM(encoding=3, lang='eng', desc='Description', text=meta['description']))

    for frame in frames:
        tags.add(frame)

    if meta.get('thumbnail_url'):
        data, mime = _fetch_cover_data(meta['thumbnail_url'])
        if data:
            tags.add(APIC(encoding=3, mime=mime, type=3, desc='Cover', data=data))

    tags.save()


def _apply_m4a_metadata(filepath, meta):
    """Applique des tags iTunes enrichis a un fichier M4A."""
    from mutagen.mp4 import MP4, MP4Cover

    audio = MP4(filepath)

    if meta.get('title'):
        audio['\xa9nam'] = meta['title']
    if meta.get('artist'):
        audio['\xa9ART'] = meta['artist']
    if meta.get('album'):
        audio['\xa9alb'] = meta['album']
    if meta.get('year'):
        audio['\xa9day'] = meta['year']
    if meta.get('genre'):
        audio['\xa9gen'] = meta['genre']

    comment = METADATA_COMMENT
    if meta.get('webpage_url'):
        comment += ' | Source: ' + meta['webpage_url']
    if meta.get('description'):
        comment += ' | ' + meta['description']
    audio['\xa9cmt'] = comment

    if meta.get('track_number'):
        audio['trkn'] = [(meta['track_number'], 0)]
    if meta.get('channel'):
        audio['aART'] = meta['channel']

    if meta.get('thumbnail_url'):
        data, mime = _fetch_cover_data(meta['thumbnail_url'])
        if data:
            audio['covr'] = [MP4Cover(data, MP4Cover.FORMAT_JPEG)]

    audio.save()


def _apply_mp4_video_metadata(filepath, meta):
    """Ajoute des metadonnees iTunes a un fichier video MP4 (titre, album, commentaire, pochette)."""
    from mutagen.mp4 import MP4, MP4Cover

    video = MP4(filepath)

    if meta.get('title'):
        video['\xa9nam'] = meta['title']
    if meta.get('artist'):
        video['\xa9ART'] = meta['artist']
    if meta.get('album'):
        video['\xa9alb'] = meta['album']
    if meta.get('channel'):
        video['aART'] = meta['channel']
    if meta.get('year'):
        video['\xa9day'] = meta['year']
    if meta.get('genre'):
        video['\xa9gen'] = meta['genre']

    comment = METADATA_COMMENT
    if meta.get('webpage_url'):
        comment += ' | Source: ' + meta['webpage_url']
    if meta.get('description'):
        comment += ' | ' + meta['description']
    video['\xa9cmt'] = comment

    if meta.get('thumbnail_url'):
        data, mime = _fetch_cover_data(meta['thumbnail_url'])
        if data:
            video['covr'] = [MP4Cover(data, MP4Cover.FORMAT_JPEG)]

    video.save()


def _apply_audio_metadata(filepath, meta, audio_format):
    """Applique les metadonnees enrichies selon le format audio."""
    if not meta:
        return
    try:
        if audio_format == 'mp3':
            _apply_mp3_metadata(filepath, meta)
        elif audio_format == 'm4a':
            _apply_m4a_metadata(filepath, meta)
    except Exception as e:
        logger.warning('Metadonnees audio non appliquees: %s', e)


# ---------------------------------------------------------------------------
# Formats et options de telechargement
# ---------------------------------------------------------------------------

VIDEO_QUALITY_FORMATS = {
    '360':  'bv*[height<=360][vcodec^=avc1]+ba/b[height<=360][ext=mp4]/b[height<=360]/best',
    '480':  'bv*[height<=480][vcodec^=avc1]+ba/b[height<=480][ext=mp4]/b[height<=480]/best',
    '720':  'bv*[height<=720][vcodec^=avc1]+ba/b[height<=720][ext=mp4]/b[height<=720]/best',
    '1080': 'bv*[height<=1080][vcodec^=avc1]+ba/b[height<=1080][ext=mp4]/b[height<=1080]/best',
    '2160': 'bv*[height<=2160][vcodec^=avc1]+ba/b[height<=2160][ext=mp4]/b[height<=2160]/best',
}

AUDIO_VBR_QUALITY = {
    '128': '6',
    '192': '3',
    '256': '1',
    '320': '0',
}

VIDEO_CODEC_FILTERS = {
    'auto': '',
    'h264': '[vcodec^=avc1]',
    'hevc': '[vcodec^=hevc]',
    'vp9': '[vcodec^=vp9]',
    'av1': '[vcodec^=av01]',
}

CONTAINER_INFO = {
    'mp4': {'ext': 'mp4', 'merge': 'mp4', 'mime': 'video/mp4', 'label': 'MP4'},
    'webm': {'ext': 'webm', 'merge': 'webm', 'mime': 'video/webm', 'label': 'WebM'},
    'mkv': {'ext': 'mkv', 'merge': 'mkv', 'mime': 'video/x-matroska', 'label': 'MKV'},
}

AUDIO_FORMAT_INFO = {
    'mp3': {'ext': 'mp3', 'mime': 'audio/mpeg', 'codec': 'mp3', 'label': 'MP3'},
    'm4a': {'ext': 'm4a', 'mime': 'audio/mp4', 'codec': 'm4a', 'label': 'M4A (AAC)'},
    'opus': {'ext': 'opus', 'mime': 'audio/ogg', 'codec': 'opus', 'label': 'Opus'},
    'flac': {'ext': 'flac', 'mime': 'audio/flac', 'codec': 'flac', 'label': 'FLAC'},
}


def build_video_format(quality, video_codec, container):
    vcodec_filter = VIDEO_CODEC_FILTERS.get(video_codec, '')
    container_ext = CONTAINER_INFO.get(container, CONTAINER_INFO['mp4'])['ext']
    fmt = (
        f'bv*[height<={quality}]{vcodec_filter}+ba'
        f'/b[height<={quality}][ext={container_ext}]'
        f'/b[height<={quality}]'
        f'/best'
    )
    return fmt


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@require_GET
def download_info(request):
    """Retourne les tailles estimees pour chaque qualite via yt-dlp (sans telecharger)."""
    url = request.GET.get('video_url', '').strip()
    if not url or not url.startswith(('http://', 'https://')):
        return JsonResponse({'error': 'URL invalide'}, status=400)

    if url.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov')):
        return JsonResponse({'direct': True, 'sizes': {}})

    try:
        ydl_opts = {
            'format': 'bv*[vcodec^=avc1]+ba/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            title = info.get('title', 'Video')

        sizes = {}
        for quality_key, fmt_spec in VIDEO_QUALITY_FORMATS.items():
            height = int(quality_key)
            best_size = None
            for f in formats:
                f_height = f.get('height') or 0
                f_size = f.get('filesize') or f.get('filesize_approx') or 0
                if f_height <= height and f_size > 0:
                    if best_size is None or f_size > best_size:
                        best_size = f_size
            audio_size = 0
            duration = info.get('duration') or 0
            if duration > 0:
                audio_size = int(duration * 128 * 1000 / 8)
            if best_size:
                sizes[quality_key] = best_size + audio_size

        if not sizes:
            duration = info.get('duration') or 0
            if duration > 0:
                rates = {'360': 2000, '480': 4000, '720': 8000, '1080': 15000, '2160': 50000}
                for q, rate in rates.items():
                    sizes[q] = int(duration * rate * 1000 / 8)

        return JsonResponse({
            'direct': False,
            'title': title,
            'duration': duration,
            'sizes': sizes,
        })
    except Exception as e:
        logger.error('download_info error: %s', e)
        return JsonResponse({'error': str(e)[:200]}, status=500)


@require_GET
def download_mp4(request):
    """Ancien endpoint MP4. Redirige vers /download/video/."""
    url = request.GET.get('video_url', '').strip()
    quality = request.GET.get('quality', '720')
    return redirect(f'/download/video/?video_url={url}&quality={quality}')


@require_GET
def download_video(request):
    """Telechargement video avec metadonnees enrichies.
    Utilise un fichier temporaire pour permettre le merge
    video+audio (indispensable pour les flux DASH separees).
    """
    url = request.GET.get('video_url', '').strip()
    quality = request.GET.get('quality', '720')
    container = request.GET.get('container', 'mp4')
    video_codec = request.GET.get('vcodec', 'auto')

    if not url:
        return HttpResponse('URL manquante.', status=400)
    if not url.startswith(('http://', 'https://')):
        return HttpResponse('URL invalide.', status=400)

    valid_qualities = {'360', '480', '720', '1080', '2160'}
    if quality not in valid_qualities:
        quality = '720'
    if container not in CONTAINER_INFO:
        container = 'mp4'
    if video_codec not in VIDEO_CODEC_FILTERS:
        video_codec = 'auto'

    if url.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov')):
        return redirect(url)

    meta = _extract_metadata(url)
    title = _sanitize_filename(meta.get('title') or 'video')
    container_info = CONTAINER_INFO[container]
    ext = container_info['ext']
    fmt = build_video_format(quality, video_codec, container)
    ffmpeg_path = _get_ffmpeg_path()

    quality_label = f'{quality}p' if quality != '2160' else '4K'
    vcodec_part = f'_{video_codec}' if video_codec != 'auto' else ''
    filename = f'{title}_{quality_label}{vcodec_part}.{ext}'

    # Telechargement vers fichier temporaire pour merge fiable
    temp_dir = tempfile.mkdtemp(prefix='vid_video_')
    try:
        output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

        args = [
            sys.executable, '-m', 'yt_dlp',
            '-f', fmt,
            '--merge-output-format', container_info['merge'],
            '--embed-thumbnail',
            '--embed-metadata',
            '--parse-metadata', '%(channel)s:%(album)s',
            '-o', output_template,
            '--no-part',
            '--quiet',
            '--no-warnings',
            '--ffmpeg-location', ffmpeg_path,
            url,
        ]

        proc = subprocess.run(args, capture_output=True, text=True)
        if proc.returncode != 0:
            stderr = proc.stderr[:500] if proc.stderr else 'Unknown error'
            raise RuntimeError(stderr)

        downloaded = None
        for f in Path(temp_dir).rglob(f'*.{ext}'):
            downloaded = f
            break
        if not downloaded:
            for f in Path(temp_dir).rglob('*'):
                if f.is_file() and not f.name.startswith('.'):
                    downloaded = f
                    break
        if not downloaded:
            raise FileNotFoundError(f'Aucun fichier trouve dans {temp_dir}')

        # Metadonnees enrichies via mutagen pour MP4
        if ext == 'mp4' and meta:
            _apply_mp4_video_metadata(str(downloaded), meta)

        return _stream_and_cleanup(str(downloaded), container_info['mime'], filename)
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error('download_video error: %s', e)
        return HttpResponse(f'Erreur: {str(e)[:200]}', status=500)


@require_GET
def download_mp3(request):
    """Ancien endpoint MP3. Redirige vers /download/audio/?format=mp3."""
    url = request.GET.get('video_url', '').strip()
    quality = request.GET.get('quality', '192')
    return redirect(f'/download/audio/?video_url={url}&quality={quality}&format=mp3')


@require_GET
def download_audio(request):
    """Telechargement audio avec metadonnees enrichies (ID3 / iTunes)."""
    url = request.GET.get('video_url', '').strip()
    quality = request.GET.get('quality', '192')
    audio_format = request.GET.get('format', 'mp3')

    if not url:
        return HttpResponse('URL manquante.', status=400)
    if not url.startswith(('http://', 'https://')):
        return HttpResponse('URL invalide.', status=400)

    valid_qualities = {'128', '192', '256', '320'}
    if quality not in valid_qualities:
        quality = '192'
    if audio_format not in AUDIO_FORMAT_INFO:
        audio_format = 'mp3'

    ffmpeg_path = _get_ffmpeg_path()
    audio_info = AUDIO_FORMAT_INFO[audio_format]
    audio_codec = audio_info['codec']
    ext = audio_info['ext']

    # Pre-fetch metadata for enhanced tagging
    meta = _extract_metadata(url)
    title = _sanitize_filename(meta.get('title') or 'audio')
    quality_suffix = f'{quality}kbps' if ext != 'flac' else 'lossless'
    filename = f'{title}_{quality_suffix}.{ext}'

    # For mp3/m4a: temp download + mutagen pour tags enrichis
    if audio_format in ('mp3', 'm4a'):
        temp_dir = tempfile.mkdtemp(prefix='vid_audio_')
        try:
            output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

            audio_quality_val = AUDIO_VBR_QUALITY.get(quality, '3') if audio_format == 'mp3' else '0'

            ydl_opts = {
                'format': 'ba/b',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_codec,
                    'preferredquality': audio_quality_val,
                }],
                'embedmetadata': True,
                'ffmpeg_location': ffmpeg_path,
                'quiet': True,
                'no_warnings': True,
            }

            if audio_format == 'mp3':
                ydl_opts['postprocessor_args'] = {'ffmpeg': ['-compression_level', '0']}

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Find the downloaded file
            downloaded = None
            for f in Path(temp_dir).rglob(f'*.{ext}'):
                downloaded = f
                break

            if not downloaded:
                raise FileNotFoundError(f"Aucun fichier .{ext} genere dans {temp_dir}")

            _apply_audio_metadata(str(downloaded), meta, audio_format)
            return _stream_and_cleanup(str(downloaded), audio_info['mime'], filename)
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error('download_audio error: %s', e)
            return HttpResponse(f'Erreur: {str(e)[:200]}', status=500)

    # For opus/flac: streaming direct (metadonnees yt-dlp suffisantes)
    args = [
        sys.executable, '-m', 'yt_dlp',
        '-f', 'ba/b',
        '--extract-audio',
        '--audio-format', audio_codec,
        '--audio-quality', '0',
        '--embed-thumbnail',
        '--embed-metadata',
        '-o', '-',
        '--no-part',
        '--quiet',
        '--no-warnings',
        '--ffmpeg-location', ffmpeg_path,
        url,
    ]

    return _stream_ytdlp(args, audio_info['mime'], filename)


def detect_platform(url):
    """Detecte la plateforme video et retourne le type et l'URL embed."""
    youtube_match = re.search(
        r'(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})',
        url,
        re.IGNORECASE
    )
    if youtube_match:
        video_id = youtube_match.group(1)
        return {
            'type': 'youtube',
            'embed_url': f'https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0'
        }

    dailymotion_match = re.search(
        r'(?:dailymotion\.com/video/|dai\.ly/)([a-zA-Z0-9]+)',
        url,
        re.IGNORECASE
    )
    if dailymotion_match:
        video_id = dailymotion_match.group(1)
        return {
            'type': 'dailymotion',
            'embed_url': f'https://www.dailymotion.com/embed/video/{video_id}?autoplay=1'
        }

    vimeo_match = re.search(
        r'vimeo\.com/(\d+)',
        url,
        re.IGNORECASE
    )
    if vimeo_match:
        video_id = vimeo_match.group(1)
        return {
            'type': 'vimeo',
            'embed_url': f'https://player.vimeo.com/video/{video_id}?autoplay=1&title=0&byline=0&portrait=0'
        }

    return {
        'type': 'direct',
        'embed_url': url
    }


def video_player(request):
    video_url = request.GET.get('video_url', '')
    error_message = None
    media_type = 'direct'
    embed_url = ''

    if video_url:
        if not video_url.startswith(('http://', 'https://')):
            error_message = "L'URL doit commencer par http:// ou https://"
        else:
            info = detect_platform(video_url)
            media_type = info['type']
            embed_url = info['embed_url']

    context = {
        'video_url': video_url if not error_message else '',
        'error_message': error_message,
        'media_type': media_type if not error_message else 'direct',
        'embed_url': embed_url if not error_message else '',
    }

    return render(request, 'player.html', context)

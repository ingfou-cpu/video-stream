import json
import os
import re
import subprocess
import sys
import logging
import yt_dlp
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


def _get_ffmpeg_path():
    """Retourne le chemin vers ffmpeg.exe dans le projet."""
    path = os.path.join(os.getcwd(), 'ffmpeg.exe')
    if os.path.exists(path):
        return path
    return 'ffmpeg'  # fallback sur le PATH


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


# Formats yt-dlp par qualite video
# On utilise bv* (best video avec priorite au meilleur bitrate)
# et on essaye plusieurs codecs avant de fallback
VIDEO_QUALITY_FORMATS = {
    '360':  'bv*[height<=360][ext=mp4]+ba[ext=m4a]/b[height<=360][ext=mp4]/b[height<=360]/best',
    '480':  'bv*[height<=480][ext=mp4]+ba[ext=m4a]/b[height<=480][ext=mp4]/b[height<=480]/best',
    '720':  'bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b[height<=720]/best',
    '1080': 'bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]/b[height<=1080]/best',
    '2160': 'bv*[height<=2160][ext=mp4]+ba[ext=m4a]/b[height<=2160][ext=mp4]/b[height<=2160]/best',
}


@require_GET
def download_info(request):
    """Retourne les tailles estimees pour chaque qualite via yt-dlp (sans telecharger)."""
    url = request.GET.get('video_url', '').strip()
    if not url or not url.startswith(('http://', 'https://')):
        return JsonResponse({'error': 'URL invalide'}, status=400)

    # URLs directes : pas d.info disponible
    if url.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov')):
        return JsonResponse({'direct': True, 'sizes': {}})

    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            title = info.get('title', 'Video')

        # Trier par hauteur et trouver le meilleur format pour chaque pallier
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
            # Ajouter la taille estimee de l.audio (m4a ~8MB par minute estime)
            audio_size = 0
            duration = info.get('duration') or 0
            if duration > 0:
                audio_size = int(duration * 128 * 1000 / 8)  # ~128kbps
            if best_size:
                sizes[quality_key] = best_size + audio_size

        # Si aucune taille trouvee, estimer depuis le bitrate
        if not sizes:
            duration = info.get('duration') or 0
            if duration > 0:
                # Estimation grossiere: ~2MB/min pour 360p, ~50MB/min pour 4K
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
    url = request.GET.get('video_url', '').strip()
    quality = request.GET.get('quality', '720')

    if not url:
        return HttpResponse('URL manquante.', status=400)
    if not url.startswith(('http://', 'https://')):
        return HttpResponse('URL invalide.', status=400)

    # Valider la qualite
    if quality not in VIDEO_QUALITY_FORMATS:
        quality = '720'

    # Pour les videos directes (mp4, webm...), on redirige vers l URL source
    # pour eviter de consommer de la bande passante sur le serveur
    if url.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov')):
        return redirect(url)

    # Video de plateforme (YouTube, Dailymotion, Vimeo) via yt-dlp
    fmt = VIDEO_QUALITY_FORMATS[quality]
    ffmpeg_path = _get_ffmpeg_path()
    args = [
        sys.executable, '-m', 'yt_dlp',
        '-f', fmt,
        '--merge-output-format', 'mp4',
        '-o', '-',
        '--no-part',
        '--quiet',
        '--no-warnings',
        '--ffmpeg-location', ffmpeg_path,
        url,
    ]
    quality_label = f'{quality}p' if quality != '2160' else '4K'
    return _stream_ytdlp(args, 'video/mp4', f'video_{quality_label}.mp4')


@require_GET
def download_mp3(request):
    url = request.GET.get('video_url', '').strip()
    quality = request.GET.get('quality', '192')

    if not url:
        return HttpResponse('URL manquante.', status=400)
    if not url.startswith(('http://', 'https://')):
        return HttpResponse('URL invalide.', status=400)

    # Valider la qualite
    valid_qualities = {'128', '192', '256', '320'}
    if quality not in valid_qualities:
        quality = '192'

    ffmpeg_path = _get_ffmpeg_path()

    # Pour 320 kbps, utiliser le VBR max (0) qui donne la meilleure qualite
    # Pour les autres, utiliser le bitrate fixe selectionne
    audio_quality_val = '0' if quality == '320' else quality + 'K'

    args = [
        sys.executable, '-m', 'yt_dlp',
        '-f', 'bestaudio*/best',
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', audio_quality_val,
        '-o', '-',
        '--no-part',
        '--quiet',
        '--no-warnings',
        '--ffmpeg-location', ffmpeg_path,
        url,
    ]
    return _stream_ytdlp(args, 'audio/mpeg', f'audio_{quality}kbps.mp3')


def detect_platform(url):
    """Détecte la plateforme vidéo et retourne le type et l'URL embed."""
    # YouTube
    # youtube.com/watch?v=ID
    # youtu.be/ID
    # youtube.com/embed/ID
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

    # Dailymotion
    # dailymotion.com/video/ID
    # dai.ly/ID
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

    # Vimeo
    # vimeo.com/ID (numeric)
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

    # Aucune plateforme reconnue → vidéo directe
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

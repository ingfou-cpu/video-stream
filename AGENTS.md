# Video Stream Player — AGENTS.md

## Quick start

```powershell
python -m venv .venv && .venv\Scripts\Activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Commands

| Action | Command |
|--------|---------|
| Dev server | `python manage.py runserver` |
| Build CSS (Tailwind + daisyUI) | `npm run build:css` |
| Watch CSS | `npm run watch:css` |
| Build all | `npm run build` |
| Run all tests | `python manage.py test video_player.player` |
| Run single test class | `python manage.py test video_player.player.tests.DetectPlatformTests` |
| Collect static | `python manage.py collectstatic --noinput` |
| Shell | `python manage.py shell` |

## Django setup

- **Settings module**: `video_player.settings` (set via env or manage.py default)
- **Single app**: `video_player.player` (registered as `PlayerConfig` in `apps.py`)
- **No models** — app has no `models.py` or migrations; only views + cache
- **Database**: SQLite at `db.sqlite3` (gitignored); file-based cache at `cache/` (gitignored)
- **Static**: whitenoise, collected to `staticfiles/` (gitignored)
- **Locale**: `fr-fr`, timezone `Europe/Paris`
- **CSS**: Tailwind CSS v4 + daisyUI v5, compiled via `@tailwindcss/cli`; source in `static/player/css/tailwind.css`, output to `static/player/css/style.css`

## Required dependencies

- **ffmpeg** must be in PATH, or `ffmpeg.exe` in project root (Windows) — used by yt-dlp for merging/transcoding
- **yt-dlp** runs as a subprocess (`python -m yt_dlp ...`) with `--ffmpeg-location`; also used via Python API for info extraction

## Environment variables

| Variable | Default | Notes |
|----------|---------|-------|
| `DJANGO_SECRET_KEY` | fallback hardcoded key | Required in production |
| `DJANGO_DEBUG` | `True` | `true`/`1`/`yes` → debug on |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost,.railway.app` | Comma-separated |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Comma-separated |
| `YT_COOKIES` | — | Base64-encoded Netscape cookies file for YouTube auth |
| `PORT` | `8000` | Used by `start.sh` / gunicorn |

YouTube cookies (`YT_COOKIES`) are decoded at startup to a temp file and passed to yt-dlp. A local `cookies.txt` in the project root also works.

## Architecture

- **Entrypoints**: `video_player/wsgi.py` (gunicorn), `start.sh` (production), Python API views
- **URL structure**:
  - `/` — main player page
  - `/yt-search/` — YouTube search proxy via yt-dlp
  - `/download/info/` — returns quality/size estimates
  - `/download/video/` — download with container/codec options
  - `/download/audio/` — download with format/bitrate options
  - `/download/mp4/` and `/download/mp3/` — legacy redirects
  - `/stream/` — YouTube video proxy stream (avoids CDN blocking)
  - `/manifest.json`, `/sw.js` — PWA
  - `/admin/` — Django admin
- **Cache**: 4-hour TTL on yt-dlp extracted info (`CACHE_YT_INFO_TIMEOUT`); keyed by URL + format hash

## Deployment

- **Platform**: Railway (Docker builder)
- **Dockerfile**: `python:3.12-slim` + ffmpeg (`apt-get`) + npm build + pip install + collectstatic
- **Healthcheck**: `GET /`
- **Procfile** (Heroku-compatible): `web: python manage.py collectstatic --noinput && gunicorn video_player.wsgi`

## Code style

- No models, no migrations, no serializers, no forms
- All views are `@require_GET` function-based views (no class-based views)
- CSS uses Devoxx France theme variables: `--dvx-*` and `--devoxx-*`
- HTML templates: `base.html` (layout + sidebar) extends `player.html` (content)
- No TypeScript, no bundler, no preprocessor
- Commit messages in French
- Tests use `unittest.mock` (`MagicMock`, `patch`) for yt-dlp network calls — no external services needed

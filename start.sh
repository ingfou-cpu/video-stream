#!/bin/sh
set -e
PORT="${PORT:-8000}"
exec gunicorn video_player.wsgi --bind "0.0.0.0:${PORT}"

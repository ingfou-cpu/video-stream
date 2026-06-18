"""
URL configuration for video_player project.
"""
from django.contrib import admin
from django.urls import path
from video_player.player.views import video_player, download_info, download_mp4, download_mp3

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', video_player, name='video_player'),
    path('download/info/', download_info, name='download_info'),
    path('download/mp4/', download_mp4, name='download_mp4'),
    path('download/mp3/', download_mp3, name='download_mp3'),
]

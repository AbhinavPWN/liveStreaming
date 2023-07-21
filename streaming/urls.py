from django.conf.urls.static import static
from django.urls import path
from streaming import views
from videolive import settings

urlpatterns = [
    path('stream/<str:room_name>/', views.stream_video, name='stream_video'),
    path('create-room/', views.create_room, name='create_room'),
    path('capture-video/', views.capture_video, name='capture_video'),
    path('capture_video/start/', views.start_video_capture, name='start_video_capture'),
    path('capture_video/stop/', views.stop_video_capture, name='stop_video_capture'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

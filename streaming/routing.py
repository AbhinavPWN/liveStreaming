from django.urls import re_path,path
from streaming import consumers

websocket_urlpatterns = [
    re_path(r'ws/stream/(?P<room_name>\w+)/$', consumers.VideoConsumer.as_asgi()),
    # path('ws/stream/<str:room_name>/', consumers.VideoConsumer.as_asgi()),
]

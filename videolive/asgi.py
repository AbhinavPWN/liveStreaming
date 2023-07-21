import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

import streaming
from streaming import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'videolive.settings')


application = ProtocolTypeRouter(
    {
        'http': get_asgi_application(),
        'websocket': AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(streaming.routing.websocket_urlpatterns))
        ),
    }
)

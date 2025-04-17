from .auth import auth_routes
from .events import events_routes
from .blog import blog_routes
from .chat import chat_routes
from .notifications import notifications_routes
from .groups import groups_routes
from .challenges import challenges_routes
from .learning import learning_routes
from .forum import forum_routes
from .users import users_routes
from .achievements import achievements_routes

__all__ = [
    'auth_routes',
    'events_routes',
    'blog_routes',
    'chat_routes',
    'notifications_routes',
    'groups_routes',
    'challenges_routes',
    'learning_routes',
    'forum_routes',
    'users_routes',
    'achievements_routes',
]
from flask import Flask, send_from_directory, request, make_response, jsonify
from flask_cors import CORS
from routes.auth import auth_routes
from routes.events import events_routes
from routes.blog import blog_routes
from routes.chat import chat_routes
from routes.notifications import notifications_routes
from routes.groups import groups_routes
from routes.challenges import challenges_routes
from routes.learning import learning_routes
from routes.forum import forum_routes
from routes.users import users_routes
from routes.achievements import achievements_routes
from models.websockets import create_socketio
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logging.getLogger("engineio.server").setLevel(logging.WARNING)

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
    app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
    
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.config['DEBUG'] = debug_mode
    
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
    CORS(app, 
        resources={r"/*": {
            "origins": allowed_origins.split(','),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept"],
            "supports_credentials": True
        }},
        supports_credentials=True
    )

    socketio = create_socketio(app)
    
    app.register_blueprint(auth_routes, url_prefix='/auth')
    app.register_blueprint(events_routes, url_prefix='/events')
    app.register_blueprint(blog_routes, url_prefix='/blog')
    app.register_blueprint(chat_routes, url_prefix='/chat')
    app.register_blueprint(notifications_routes, url_prefix='/notifications')
    app.register_blueprint(groups_routes, url_prefix='/groups')
    app.register_blueprint(challenges_routes, url_prefix='/challenges')
    app.register_blueprint(learning_routes, url_prefix='/learning')
    app.register_blueprint(forum_routes, url_prefix='/forum')
    app.register_blueprint(users_routes, url_prefix='/users')
    app.register_blueprint(achievements_routes, url_prefix='/achievements')

    @app.after_request
    def after_request(response):
        response.headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept'
        })
        return response

    @app.errorhandler(404)
    def not_found_error(error):
        logger.error(f"404 error: {error}")
        return jsonify({
            'success': False,
            'message': 'Resource not found',
            'error': str(error)
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {error}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(error)
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred',
            'error': str(error)
        }), 500

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory('uploads', filename)

    @app.route('/')
    def index():
        return {'message': 'Welcome to Green Buddy API'}

    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    
    
    print("Starting server with eventlet...")
    logger.info("Binding to 127.0.0.1:5000")
    
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=False
    )


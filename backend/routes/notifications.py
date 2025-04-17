from flask import Blueprint, request, jsonify
from models.notification import Notification
from models.auth import token_required, get_current_user

notifications_routes = Blueprint('notifications', __name__)

@notifications_routes.route('/', methods=['GET'])
@token_required
def get_notifications(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        result = Notification.get_all(
            user_id=current_user['id'],
            page=page,
            limit=limit
        )
        
        # Add CORS headers
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response, 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'notifications': [],
            'page': page,
            'total': 0,
            'total_pages': 0
        }), 500

@notifications_routes.route('/', methods=['DELETE'])
@token_required
def clear_notifications():
    try:
        current_user = get_current_user()
        
        result = Notification.delete_all(user_id=current_user['id'])
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_routes.route('/unread', methods=['GET'])
@token_required
def get_unread_count(current_user):
    try:
        
        if not current_user or 'id' not in current_user:
            return jsonify({'error': 'Unauthorized', 'success': False}), 401

        result = Notification.get_unread_count(user_id=current_user['id'])
        
        if not result:
            return jsonify({'success': True, 'unread_count': 0}), 200
            
        return jsonify({'success': True, **result}), 200

    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'An unexpected error occurred',
            'success': False,
            'unread_count': 0
        }), 500

@notifications_routes.route('/<int:notification_id>/read', methods=['POST'])
@token_required
def mark_as_read(current_user, notification_id):
    try:
                
        result = Notification.mark_as_read(
            notification_id=notification_id,
            user_id=current_user['id']
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_routes.route('/read-all', methods=['POST'])
@token_required
def mark_all_as_read(current_user):
    try:
        
        if not current_user or 'id' not in current_user:
            return jsonify({'error': 'Unauthorized', 'success': False}), 401
            
        result = Notification.mark_all_as_read(user_id=current_user['id'])
        
        return jsonify({'success': True, **result}), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to mark all notifications as read',
            'success': False
        }), 500 
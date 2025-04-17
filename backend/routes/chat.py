from flask import Blueprint, request, jsonify
from models.auth import token_required, get_current_user
from models.chat import Chat, ChatMessage
from database.connection import Database

chat_routes = Blueprint('chat', __name__)

@chat_routes.route('/rooms', methods=['GET'])
@token_required
def get_chat_rooms(current_user):
    # Get all available chat rooms for the user.
    try:
        rooms = Chat.get_chat_rooms()
        return jsonify(rooms), 200
    except Exception as e:
        print(f"Error in get_chat_rooms: {str(e)}")
        return jsonify({'error': 'Failed to fetch chat rooms'}), 500

@chat_routes.route('/rooms/<int:room_id>/messages', methods=['GET'])
@token_required
def get_room_messages(current_user, room_id):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        messages = ChatMessage.get_room_messages(
            room_id=room_id,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'success': True,
            'messages': messages,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(messages), 
                'total_pages': 1 if len(messages) < per_page else page + 1  
            }
        }), 200
    except Exception as e:
        print(f"Error in get_room_messages route: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'messages': []
        }), 500

@chat_routes.route('/rooms/<int:room_id>/join', methods=['POST'])
@token_required
def join_room(current_user, room_id):
    # Join a chat room.
    try:
        success = Chat.join_room(room_id, current_user['id'])
        
        if success:
            return jsonify({
                'message': 'Successfully joined room',
                'room_id': room_id
            }), 200
        else:
            return jsonify({'error': 'Failed to join room'}), 500
    except Exception as e:
        print(f"Error in join_room: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chat_routes.route('/rooms/<int:room_id>/leave', methods=['POST'])
@token_required
def leave_room(current_user, room_id):
    try:
        success = Chat.leave_room(room_id, current_user['id'])
        
        if success:
            return jsonify({
                'message': 'Successfully left room',
                'room_id': room_id
            }), 200
        else:
            return jsonify({'error': 'Failed to leave room'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_routes.route('/rooms/<int:room_id>/participants', methods=['GET'])
@token_required
def get_room_participants(current_user, room_id):
    """Get all participants in a chat room."""
    try:
        participants = Chat.get_room_participants(room_id)
        return jsonify(participants), 200
    except Exception as e:
        print(f"Error in get_room_participants route: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@chat_routes.route('/rooms/<int:room_id>/unread', methods=['GET'])
@token_required
def get_unread_count(current_user, room_id):
    try:
        unread_count = Chat.get_unread_count(room_id=room_id, user_id=current_user['id'])
        return jsonify({'success': True, 'unread_count': unread_count}), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to get unread count',
            'success': False,
            'unread_count': 0
        }), 500

@chat_routes.route('/rooms/unread', methods=['GET'])
@token_required
def get_all_unread_counts(current_user):
    try:
        unread_counts = Chat.get_all_unread_counts(current_user['id'])
        return jsonify({'success': True, 'unread_counts': unread_counts}), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to get unread counts',
            'success': False,
            'unread_counts': {}
        }), 500

@chat_routes.route('/rooms/<int:room_id>/messages', methods=['POST'])
@token_required
def send_message(current_user, room_id):
    """Send a message to a chat room."""
    try:
        if not Chat.is_participant(room_id, current_user['id']):
            room = Chat.get_room_by_id(room_id)
            if not room or room['type'] != 'public':
                return jsonify({'error': 'Not a participant of this room'}), 403
            
            success = Chat.join_room(room_id, current_user['id'])
            if not success:
                return jsonify({'error': 'Failed to join room'}), 500
        
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Message content is required'}), 400
        
        content = data['content'].strip()
        if not content:
            return jsonify({'error': 'Message content cannot be empty'}), 400
        
        message = ChatMessage.create(
            room_id=room_id,
            sender_id=current_user['id'],
            content=content
        )
        
        if message:
            return jsonify({
                'success': True,
                'message': message
            }), 201
        else:
            return jsonify({'error': 'Failed to create message'}), 500
            
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        return jsonify({'error': str(e)}), 500


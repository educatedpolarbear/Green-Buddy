import os
from flask import request
from flask_socketio import SocketIO, join_room, leave_room, emit
import eventlet
from models.chat import Chat, ChatMessage
from models.auth import verify_token
from database.connection import Database
import jwt
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

socketio_instance = None

async_mode = 'eventlet'

def create_socketio(app):
    # Create and configure Socket.IO for the application.
    global socketio_instance
    socketio = SocketIO(app, 
                       cors_allowed_origins="*",
                       async_mode=async_mode,  
                       logger=True,
                       engineio_logger=True)
    socketio.user_data = {}  # Store user data (user_id -> {username, rooms})
    socketio_instance = socketio

    def authenticate_socket(token):
        # Authenticate user from token.
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            decoded = verify_token(token)
            if not decoded:
                return None
            
            if 'user_id' in decoded and 'id' not in decoded:
                decoded['id'] = decoded['user_id']
            
            return decoded
        except Exception as e:
            logger.error(f"Error in socket authentication: {str(e)}")
            return None

    @socketio.on('connect')
    def handle_connect():
        # Handle client connection.
        try:
            token = request.args.get('token')
            if not token:
                logger.error("No token provided for socket connection")
                return False
            
            user = authenticate_socket(token)
            if not user:
                logger.error("Invalid token for socket connection")
                return False
            
            socketio.user_data[request.sid] = {
                'user_id': user['id'],
                'username': user.get('username', 'Unknown'),
                'rooms': set()  
            }
            
            return True
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False

    @socketio.on('disconnect')
    def handle_disconnect():
        # Handle client disconnection.
        try:
            if request.sid in socketio.user_data:
                user = socketio.user_data[request.sid]
                for room_id in list(user['rooms']):  
                    leave_room(f"room_{room_id}")
                    emit('user_left', {
                        'username': user['username'],
                        'room_id': room_id
                    }, room=f"room_{room_id}")
                
                del socketio.user_data[request.sid]
        except Exception as e:
            logger.error(f"Disconnection error: {str(e)}")

    @socketio.on('join_chat')
    def handle_join_chat(data):
        # Handle user joining a chat room.
        try:
            token = data.get('token')
            room_id = data.get('room_id')
            
            if not token or not room_id:
                logger.error("Missing token or room_id in join_chat")
                emit('error', {'message': 'Missing token or room_id'})
                return
            
            user = authenticate_socket(token)
            if not user:
                logger.error("Invalid token in join_chat")
                emit('error', {'message': 'Invalid token'})
                return
            
            user_id = user.get('id') or user.get('user_id')
            if not user_id:
                logger.error("No user ID found in token payload")
                emit('error', {'message': 'Invalid user data'})
                return
            
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT r.*, 
                       CASE WHEN p.user_id IS NOT NULL THEN 1 ELSE 0 END as is_member
                FROM chat_rooms r
                LEFT JOIN chat_room_participants p 
                    ON r.id = p.room_id AND p.user_id = %s
                WHERE r.id = %s AND (r.type = 'public' OR p.user_id IS NOT NULL)
            """, (user_id, room_id))
            
            room = cursor.fetchone()
            if not room:
                logger.error(f"Room {room_id} not found or access denied for user {user_id}")
                emit('error', {'message': 'Room not found or access denied'})
                cursor.close()
                conn.close()
                return
            
            formatted_room = {
                'id': room['id'],
                'name': room['name'],
                'description': room['description'],
                'type': room['type'],
                'created_at': room['created_at'].isoformat() if room['created_at'] else None,
                'is_member': room['is_member']
            }
            
            join_room(f"room_{room_id}")
            if request.sid in socketio.user_data:
                socketio.user_data[request.sid]['rooms'].add(room_id)
            
            cursor.execute("""
                SELECT u.id, u.username, p.role, p.joined_at
                FROM chat_room_participants p
                JOIN users u ON p.user_id = u.id
                WHERE p.room_id = %s
            """, (room_id,))
            
            participants = cursor.fetchall()
            
            formatted_participants = [{
                'id': p['id'],
                'username': p['username'],
                'role': p['role'],
                'joined_at': p['joined_at'].isoformat() if p['joined_at'] else None
            } for p in participants]
            
            if not room['is_member']:
                cursor.execute("""
                    INSERT IGNORE INTO chat_room_participants 
                    (room_id, user_id, role, last_read_at)
                    VALUES (%s, %s, 'member', CURRENT_TIMESTAMP)
                """, (room_id, user_id))
                conn.commit()
            
            cursor.close()
            conn.close()
            
            emit('user_joined', {
                'username': user.get('username'),
                'room_id': room_id
            }, room=f"room_{room_id}")
            
            emit('joined_chat', {
                'success': True,
                'room': formatted_room,
                'participants': formatted_participants
            })
            
        except Exception as e:
            logger.error(f"Error joining chat: {str(e)}")
            emit('error', {'message': str(e)})

    @socketio.on('leave_chat')
    def handle_leave_chat(data):
        # Handle user leaving a chat room.
        try:
            room_id = data.get('room_id')
            if not room_id or request.sid not in socketio.user_data:
                return
            
            user = socketio.user_data[request.sid]
            if room_id in user['rooms']:
                leave_room(f"room_{room_id}")
                user['rooms'].remove(room_id)
                
                emit('user_left', {
                    'username': user['username'],
                    'room_id': room_id
                }, room=f"room_{room_id}")
                
                emit('left_chat', {'success': True})
        except Exception as e:
            logger.error(f"Error leaving chat: {str(e)}")
            emit('error', {'message': str(e)})

    @socketio.on('send_message')
    def handle_send_message(data):
        # Handle sending a chat message.
        try:
            if request.sid not in socketio.user_data:
                emit('error', {'message': 'Not authenticated'})
                return
            
            room_id = data.get('room_id')
            content = data.get('content')
            
            if not room_id or not content:
                emit('error', {'message': 'Missing room_id or content'})
                return
            
            user = socketio.user_data[request.sid]
            
            if room_id not in user['rooms']:
                emit('error', {'message': 'Not a member of this room'})
                return
            
            if not Chat.is_participant(room_id, user['user_id']):
                room = Chat.get_room_by_id(room_id)
                if not room or room['type'] != 'public':
                    emit('error', {'message': 'Cannot send messages to this room'})
                    return
                
                success = Chat.join_room(room_id, user['user_id'])
                if not success:
                    emit('error', {'message': 'Failed to join room'})
                    return
            
            message = ChatMessage.create(
                room_id=room_id,
                sender_id=user['user_id'],
                content=content
            )
            
            if not message:
                emit('error', {'message': 'Failed to create message'})
                return
            
            message['room_id'] = room_id
            
            emit('new_message', message, room=f"room_{room_id}")
            
            emit('message_sent', {'success': True})
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            emit('error', {'message': str(e)})

    return socketio

def send_achievement_notification(user_id, achievement_data):
    # Send a real-time notification to a user when they earn an achievement.

    global socketio_instance
    if not socketio_instance:
        logger.error("SocketIO instance not initialized")
        return False
    
    try:
        user_sids = [
            sid for sid, data in socketio_instance.user_data.items() 
            if data.get('user_id') == user_id
        ]
        
        if not user_sids:
            logger.info(f"User {user_id} not connected, can't send achievement notification")
            return False
        
        notification_data = {
            'type': 'achievement_earned',
            'title': 'Achievement Unlocked!',
            'message': f"You've earned the '{achievement_data['name']}' achievement and {achievement_data['exp_reward']} XP!",
            'achievement': achievement_data,
            'timestamp': datetime.now().isoformat()
        }
        
        for sid in user_sids:
            socketio_instance.emit('new_notification', notification_data, room=sid)
        
        return True
    except Exception as e:
        logger.error(f"Error sending achievement notification: {str(e)}")
        return False


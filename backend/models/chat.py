import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from database.connection import Database

logger = logging.getLogger(__name__)

class ChatMessage:
    # Model class for chat messages.
    
    @staticmethod
    def create(room_id: int, sender_id: int, content: str) -> Dict[str, Any]:
        # Create a new chat message.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                INSERT INTO chat_messages (room_id, sender_id, content, created_at)
                VALUES (%s, %s, %s, NOW())
                """,
                (room_id, sender_id, content)
            )
            
            message_id = cursor.lastrowid
            conn.commit()
            
            cursor.execute(
                """
                SELECT 
                    cm.id, 
                    cm.content, 
                    cm.created_at,
                    u.username as sender_name 
                FROM chat_messages cm
                JOIN users u ON cm.sender_id = u.id
                WHERE cm.id = %s
                """,
                (message_id,)
            )
            
            message = cursor.fetchone()
            
            if message:
                return {
                    'id': message['id'],
                    'content': message['content'],
                    'sender_name': message['sender_name'],
                    'created_at': message['created_at'].isoformat() if message['created_at'] else None
                }
            return None
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating message: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_room_messages(room_id: int, page: int = 1, per_page: int = 50) -> List[Dict[str, Any]]:
        # Get messages for a specific chat room with pagination.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            offset = (page - 1) * per_page
            
            cursor.execute(
                """
                SELECT 
                    cm.id, 
                    cm.content, 
                    cm.sender_id,
                    u.username as sender_name,
                    cm.created_at
                FROM chat_messages cm
                JOIN users u ON cm.sender_id = u.id
                WHERE cm.room_id = %s
                ORDER BY cm.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (room_id, per_page, offset)
            )
            
            messages = cursor.fetchall()
            
            # Format the messages
            formatted_messages = []
            for message in messages:
                formatted_messages.append({
                    'id': message['id'],
                    'content': message['content'],
                    'sender_id': message['sender_id'],
                    'sender_name': message['sender_name'],
                    'created_at': message['created_at'].isoformat() if message['created_at'] else None
                })
                
            return formatted_messages
            
        except Exception as e:
            logger.error(f"Error getting room messages: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()


class Chat:
    # Model class for chat rooms and chat functionality.
    
    @staticmethod
    def get_chat_rooms() -> List[Dict[str, Any]]:
        # Get all available chat rooms.
        
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT 
                    id, 
                    name, 
                    description, 
                    created_at,
                    type
                FROM chat_rooms
                ORDER BY name ASC
                """
            )
            
            rooms = cursor.fetchall()
            
            formatted_rooms = []
            for room in rooms:
                formatted_rooms.append({
                    'id': room['id'],
                    'name': room['name'],
                    'description': room['description'],
                    'type': room['type'],
                    'created_at': room['created_at'].isoformat() if room['created_at'] else None
                })
                
            return formatted_rooms
            
        except Exception as e:
            logger.error(f"Error getting chat rooms: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_room_by_id(room_id: int) -> Optional[Dict[str, Any]]:
        # Get a chat room by its ID.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT 
                    id, 
                    name, 
                    description, 
                    created_at,
                    type
                FROM chat_rooms
                WHERE id = %s
                """,
                (room_id,)
            )
            
            room = cursor.fetchone()
            
            if room:
                return {
                    'id': room['id'],
                    'name': room['name'],
                    'description': room['description'],
                    'type': room['type'],
                    'created_at': room['created_at'].isoformat() if room['created_at'] else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting chat room by ID: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def is_participant(room_id: int, user_id: int) -> bool:
        # Check if a user is a participant in a chat room.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM chat_room_participants
                WHERE room_id = %s AND user_id = %s
                """,
                (room_id, user_id)
            )
            
            result = cursor.fetchone()
            
            return result['count'] > 0
            
        except Exception as e:
            logger.error(f"Error checking if user is participant: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def join_room(room_id: int, user_id: int) -> bool:
        # Add a user to a chat room.

        try:
            room = Chat.get_room_by_id(room_id)
            if not room:
                return False
                
            if Chat.is_participant(room_id, user_id):
                return True
                
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO chat_room_participants (room_id, user_id, role, joined_at, last_read_at)
                VALUES (%s, %s, 'member', NOW(), NOW())
                """,
                (room_id, user_id)
            )
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error joining chat room: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def leave_room(room_id: int, user_id: int) -> bool:
        # Remove a user from a chat room.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                DELETE FROM chat_room_participants
                WHERE room_id = %s AND user_id = %s
                """,
                (room_id, user_id)
            )
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error leaving chat room: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_room_participants(room_id: int) -> List[Dict[str, Any]]:
        # Get all participants in a chat room.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT 
                    crp.user_id,
                    u.username,
                    crp.role,
                    crp.joined_at
                FROM chat_room_participants crp
                JOIN users u ON crp.user_id = u.id
                WHERE crp.room_id = %s
                ORDER BY crp.role, u.username
                """,
                (room_id,)
            )
            
            participants = cursor.fetchall()
            
            formatted_participants = []
            for participant in participants:
                formatted_participants.append({
                    'user_id': participant['user_id'],
                    'username': participant['username'],
                    'role': participant['role'],
                    'joined_at': participant['joined_at'].isoformat() if participant['joined_at'] else None
                })
                
            return formatted_participants
            
        except Exception as e:
            logger.error(f"Error getting room participants: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_unread_count(room_id: int, user_id: int) -> int:
        # Get the count of unread messages in a specific room for a user.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT 
                    COUNT(cm.id) as unread_count
                FROM chat_messages cm
                JOIN chat_room_participants crp ON cm.room_id = crp.room_id
                WHERE cm.room_id = %s 
                AND crp.user_id = %s
                AND (crp.last_read_at IS NULL OR cm.created_at > crp.last_read_at)
                """,
                (room_id, user_id)
            )
            
            result = cursor.fetchone()
            
            return result['unread_count'] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_all_unread_counts(user_id: int) -> Dict[int, int]:
        # Get unread message counts for all rooms the user is a participant in.
        
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT 
                    crp.room_id,
                    COUNT(cm.id) as unread_count
                FROM chat_room_participants crp
                LEFT JOIN chat_messages cm ON crp.room_id = cm.room_id 
                    AND (crp.last_read_at IS NULL OR cm.created_at > crp.last_read_at)
                WHERE crp.user_id = %s
                GROUP BY crp.room_id
                """,
                (user_id,)
            )
            
            results = cursor.fetchall()
            
            unread_counts = {}
            for result in results:
                unread_counts[result['room_id']] = result['unread_count']
                
            return unread_counts
            
        except Exception as e:
            logger.error(f"Error getting all unread counts: {str(e)}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def mark_messages_read(room_id: int, user_id: int) -> bool:
        # Mark messages as read for a user in a chat room.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE chat_room_participants
                SET last_read_at = NOW()
                WHERE room_id = %s AND user_id = %s
                """,
                (room_id, user_id)
            )
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error marking messages as read: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

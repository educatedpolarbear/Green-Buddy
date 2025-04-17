import os
import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from models.user import User
from typing import Union, Optional, Dict, Any
from database.connection import Database

logger = logging.getLogger(__name__)

def generate_token(user_data: Union[int, dict], expires_delta: timedelta = None) -> str:
    # Generate a JWT token for the user with optional expiration time.
    try:
        if os.getenv('FLASK_ENV') == 'development':
            payload = {
                'user_id': user_data['id'] if isinstance(user_data, dict) else user_data,
                'iat': datetime.utcnow()
            }
        else:
            if expires_delta is None:
                expires_delta = timedelta(days=1)
            
            payload = {
                'user_id': user_data['id'] if isinstance(user_data, dict) else user_data,
                'exp': datetime.utcnow() + expires_delta,
                'iat': datetime.utcnow()
            }
        
        token = jwt.encode(
            payload,
            os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
            algorithm='HS256'
        )
        return token
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        raise

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    # Decode and verify a JWT token.
    try:
        decoded = jwt.decode(
            token,
            os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
            algorithms=['HS256'],
            options={'verify_exp': False}
        )
        return decoded
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {str(e)}")
        return None

def get_current_user() -> Optional[Dict[str, Any]]:
    # Get the current authenticated user from the request.
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    if not auth_header.startswith('Bearer '):
        return None
    
    try:
        token = auth_header.split(' ')[1]
        
        payload = verify_token(token)
        if not payload:
            logger.debug("Token verification failed")
            return None
            
        user_id = payload.get('user_id')
        if not user_id:
            logger.debug("No user_id found in token payload")
            return None
        
        try:
            if isinstance(user_id, dict) and 'id' in user_id:
                user_id = user_id['id']
            user_id = int(user_id)
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting user_id to integer: {str(e)}")
            return None
        
        user = User.get_by_id(user_id)
        if not user:
            logger.debug(f"No user found for user_id: {user_id}")
            return None
            
        roles = [user.get('role')] if user.get('role') else ['user']
        
        is_admin = user.get('role') == 'admin'
            
        user_data = {
            'id': int(user.get('id')),
            'username': user.get('username', ''),
            'email': user.get('email', ''),
            'roles': roles,
            'is_admin': is_admin, 
            'created_at': user.get('created_at'),
            'last_login': user.get('last_login'),
            'avatar_url': user.get('avatar_url'),
            'bio': user.get('bio')
        }
        return user_data
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        return None

def token_required(f):
    # Decorator for routes that require a valid token.
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            logger.warning("Authentication required but no valid user found")
            return jsonify({'error': 'Authentication required'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def optional_auth(f):
    # Decorator to optionally include authenticated user in routes.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        return f(current_user, *args, **kwargs)
    return decorated_function

class Auth:
    @staticmethod
    def login_user(email):
        # Retrieves user information for login purposes.
        # Returns the user object if found, or None if not.
        try:
            db = Database()
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT 
                    id, 
                    username, 
                    email, 
                    password_hash, 
                    role,
                    created_at,
                    last_login,
                    exp,
                    level,
                    avatar_url,
                    bio
                FROM users 
                WHERE email = %s
                """,
                (email,)
            )
            
            user = cursor.fetchone()
            return user
        except Exception as e:
            print(f"Error retrieving user for login: {str(e)}")
            raise e
        finally:
            cursor.close()
            connection.close()
    
    @staticmethod
    def update_last_login(user_id):
        # Updates the last_login timestamp for a user.
        try:
            db = Database()
            connection = db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                (user_id,)
            )
            
            connection.commit()
            return True
        except Exception as e:
            print(f"Error updating last login: {str(e)}")
            connection.rollback()
            raise e
        finally:
            cursor.close()
            connection.close()
    
    @staticmethod
    def record_login_in_db(user_id, ip_address):
        # Records a login in the user_logins table.
        # Returns True if successful, False otherwise.
        try:
            db = Database()
            connection = db.get_connection()
            cursor = connection.cursor()
            
            cursor.execute(
                """
                INSERT INTO user_logins (user_id, login_time, ip_address)
                VALUES (%s, NOW(), %s)
                """, 
                (user_id, ip_address)
            )
            
            connection.commit()
            return True
        except Exception as e:
            print(f"Error recording login: {str(e)}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()
    
    @staticmethod
    def register_user(username, email, password_hash):
        # Registers a new user with the given username, email, and password hash.
        # Returns the user ID if successful, or raises an exception if not.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Create user with default role
            cursor.execute(
                """
                INSERT INTO users (
                    username, email, password_hash, created_at, role
                ) VALUES (%s, %s, %s, NOW(), 'user')
                """,
                (username, email, password_hash)
            )
            
            user_id = cursor.lastrowid
            conn.commit()
            
            return user_id
        except Exception as e:
            conn.rollback()
            print(f"Error registering user: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def check_email_exists(email):
        # Checks if an email already exists in the database.
        # Returns True if the email exists, False otherwise.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
            result = cursor.fetchone() is not None
            
            return result
        except Exception as e:
            print(f"Error checking email existence: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def check_username_exists(username):
        # Checks if a username already exists in the database.
        # Returns True if the username exists, False otherwise.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            result = cursor.fetchone() is not None
            
            return result
        except Exception as e:
            print(f"Error checking username existence: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_user_after_register(user_id):
        # Retrieves a user's basic information after registration.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT id, username, email, created_at, role FROM users WHERE id = %s", 
                (user_id,)
            )
            
            return cursor.fetchone()
        except Exception as e:
            print(f"Error retrieving registered user: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close() 
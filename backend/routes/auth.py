from flask import Blueprint, request, jsonify, make_response
from models.user import User
import re
from email_validator import validate_email, EmailNotValidError
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from database.connection import Database
from werkzeug.security import check_password_hash, generate_password_hash
from models.auth import generate_token, token_required, get_current_user, Auth

load_dotenv()

auth_routes = Blueprint('auth_routes', __name__)

login_attempts = {}
MAX_ATTEMPTS = 5
LOCKOUT_TIME = 15 * 60 

def is_rate_limited(email):
    # Check if the email is rate limited due to too many failed attempts.
    if email in login_attempts:
        attempts, timestamp = login_attempts[email]
        if attempts >= MAX_ATTEMPTS:
            if datetime.now().timestamp() - timestamp < LOCKOUT_TIME:
                return True
            login_attempts[email] = (0, datetime.now().timestamp())
    return False

def record_login_attempt(email, success):
    # Record a login attempt for rate limiting purposes.
    current_time = datetime.now().timestamp()
    if email in login_attempts:
        attempts, _ = login_attempts[email]
        if success:
            login_attempts[email] = (0, current_time)
        else:
            login_attempts[email] = (attempts + 1, current_time)
    else:
        login_attempts[email] = (1 if not success else 0, current_time)

def validate_password(password):
    # Validate password strength
    # - At least 8 characters long
    # - Contains at least one uppercase letter
    # - Contains at least one lowercase letter
    # - Contains at least one number
    # - Contains at least one special character
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, ""

@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            'success': False,
            'message': 'Email and password are required',
            'field': 'email' if 'email' not in data else 'password'
        }), 400

    try:
        validate_email(data['email'])
    except EmailNotValidError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'field': 'email'
        }), 400

    if is_rate_limited(data['email']):
        remaining_time = LOCKOUT_TIME - (datetime.now().timestamp() - login_attempts[data['email']][1])
        return jsonify({
            'success': False,
            'message': f'Too many failed attempts. Please try again in {int(remaining_time / 60)} minutes.',
            'field': 'email'
        }), 429

    try:
        user = Auth.login_user(data['email'])

        if not user or not check_password_hash(user['password_hash'], data['password']):
            record_login_attempt(data['email'], False)
            attempts = login_attempts[data['email']][0]
            remaining_attempts = MAX_ATTEMPTS - attempts
            
            message = 'Invalid email or password'
            if remaining_attempts > 0:
                message += f'. {remaining_attempts} attempts remaining'
            
            return jsonify({
                'success': False,
                'message': message,
                'field': 'password',
                'remaining_attempts': remaining_attempts
            }), 401

        record_login_attempt(data['email'], True)

        Auth.update_last_login(user['id'])
        
        try:
            Auth.record_login_in_db(user['id'], request.remote_addr)
            
            from models.user_stats import UserStats
            
            UserStats.update_stat_and_achievements(
                user['id'],
                'login_count',
                {
                    'login_time': datetime.now()
                }
            )

            UserStats.update_stat_and_achievements(
                user['id'],
                'login_streak',
                {
                    'login_time': datetime.now()
                }
            )
            
        except Exception as e:
            print(f"Error recording login stats: {str(e)}")

        roles = [user['role']] if user['role'] else ['user']

        token = generate_token(user['id'])

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'roles': roles,
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'last_login': user['last_login'].isoformat() if user['last_login'] else None,
                'avatar_url': user['avatar_url'],
                'bio': user['bio']
            }
        }), 200
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Login failed. Please try again later.'
        }), 500

@auth_routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'success': False,
                'message': f'{field.capitalize()} is required',
                'field': field
            }), 400
    
    try:
        valid_email = validate_email(data['email'])
        normalized_email = valid_email.email
    except EmailNotValidError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'field': 'email'
        }), 400
        
    password_valid, password_error = validate_password(data['password'])
    if not password_valid:
        return jsonify({
            'success': False,
            'message': password_error,
            'field': 'password'
        }), 400
    
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', data['username']):
        return jsonify({
            'success': False,
            'message': 'Username must be 3-20 characters and can only contain letters, numbers, and underscores',
            'field': 'username'
        }), 400
    
    try:
        if Auth.check_email_exists(normalized_email):
            return jsonify({
                'success': False,
                'message': 'Email already registered',
                'field': 'email'
            }), 400
            
        if Auth.check_username_exists(data['username']):
            return jsonify({
                'success': False,
                'message': 'Username already taken',
                'field': 'username'
            }), 400
            
        password_hash = generate_password_hash(data['password'])
        
        user_id = Auth.register_user(data['username'], normalized_email, password_hash)
        
        user = Auth.get_user_after_register(user_id)
        
        roles = [user['role']] if user['role'] else ['user']
        
        token = generate_token(user_id)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'roles': roles,
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'last_login': None
            }
        }), 201
    except Exception as e:
        print(f"Error in register: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Registration failed. Please try again later.'
        }), 500

@auth_routes.route('/verify-token', methods=['POST'])
def verify_token_route():
    try:
        current_user = get_current_user()
        if not current_user or not isinstance(current_user, dict):
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401
        
        return jsonify({
            'success': True,
            'user': {
                'id': current_user['id'],
                'username': current_user['username'],
                'email': current_user['email'],
                'roles': current_user.get('roles', []),
                'created_at': current_user.get('created_at'),
                'last_login': current_user.get('last_login')
            }
        })
    except Exception as e:
        print(f"Error in verify_token_route: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to process user data'
        }), 500

@auth_routes.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    # Get the current user's complete profile information.
    try:
        profile_data = User.get_profile(current_user['id'])
        if not profile_data.get('success'):
            return jsonify({'success': False, 'error': 'Failed to fetch profile'}), 404

        return jsonify(profile_data), 200
        
    except Exception as e:
        print(f"Error in get_current_user: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_routes.route('/protected', methods=['GET'])
@token_required
def protected(current_user):
    return jsonify({'message': f'Hello {current_user["username"]}!'}), 200

@auth_routes.route('/user/achievements', methods=['GET', 'OPTIONS'])
@token_required
def get_user_achievements(current_user):
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response

    try:
        user_model = User()
        achievements = user_model.get_achievements(current_user['id'])
        return jsonify(achievements), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_routes.route('/user/available-achievements', methods=['GET'])
@token_required
def get_available_achievements(current_user):
    try:
        user_model = User()
        achievements = user_model.get_available_achievements(current_user['id'])
        return jsonify(achievements), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

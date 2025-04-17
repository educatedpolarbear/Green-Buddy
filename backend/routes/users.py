from flask import Blueprint, request, jsonify
from models.user import User
from models.group import Group
from models.chat import Chat
from models.auth import token_required, optional_auth
import re
from database.connection import Database
from models.achievement import UserActivity
from models.user_stats import UserStats

users_routes = Blueprint('users_routes', __name__)

@users_routes.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    # Get the current user's profile information.
    try:
        profile_data = User.get_profile(current_user['id'])
        if not profile_data.get('success'):
            return jsonify({'success': False, 'error': 'Failed to fetch profile'}), 404

        try:
            chat_groups = Chat.get_user_groups(current_user['id'])
            profile_data['chatGroups'] = chat_groups
        except Exception as e:
            print(f"Error fetching chat groups: {str(e)}")
            profile_data['chatGroups'] = []

        return jsonify(profile_data), 200
        
    except Exception as e:
        print(f"Error in get_profile: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@users_routes.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    # Update the current user's profile.
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        User.update_profile(current_user['id'], data)
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error updating profile: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@users_routes.route('/<int:user_id>/follow', methods=['POST'])
@token_required
def follow_user(current_user, user_id):
    # Follow a user.
    try:
        if current_user['id'] == user_id:
            return jsonify({'error': 'Cannot follow yourself'}), 400
            
        follower_id = current_user['id']
        result = User.follow_user(follower_id, user_id)
        return jsonify({'success': True, 'message': 'User followed successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_routes.route('/<int:user_id>/follow', methods=['DELETE'])
@token_required
def unfollow_user(current_user, user_id):
    # Unfollow a user.
    try:
        if current_user['id'] == user_id:
            return jsonify({'error': 'Cannot unfollow yourself'}), 400
            
        follower_id = current_user['id']
        result = User.unfollow_user(follower_id, user_id)
        return jsonify({'success': True, 'message': 'User unfollowed successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_routes.route('/<int:user_id>/profile', methods=['GET'])
@optional_auth
def get_user_profile(current_user, user_id):
    # Get a specific user's profile information.
    try:
        if current_user and current_user['id'] == user_id:
            return get_profile(current_user)

        profile_data = User.get_profile(user_id)
        if not profile_data.get('success'):
            return jsonify({'success': False, 'error': 'Failed to fetch profile'}), 404
        
        try:
            chat_groups = Chat.get_user_groups(user_id)
            profile_data['chatGroups'] = chat_groups
        except Exception as e:
            print(f"Error fetching chat groups: {str(e)}")
            profile_data['chatGroups'] = []

        if current_user:
            try:
                profile_data['is_following'] = User.is_following(current_user['id'], user_id)
            except Exception as e:
                print(f"Error checking following status: {str(e)}")
                profile_data['is_following'] = False
        else:
            profile_data['is_following'] = False

        if 'user' in profile_data:
            profile_data['user'].pop('email', None)
            profile_data['user'].pop('roles', None)

        return jsonify(profile_data), 200
        
    except Exception as e:
        print(f"Error in get_user_profile: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@users_routes.route('/<int:user_id>/activities', methods=['GET'])
@token_required
def get_user_activities(current_user, user_id):
    # Get activities for a specific user with pagination.
    try:
        
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        activities = UserActivity.get_user_activities(
            user_id, 
            limit=min(limit, 50),  
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'activities': activities
        })
    except Exception as e:
        print(f"Error in get_user_activities: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500 
        
@users_routes.route('/<int:user_id>/stats', methods=['GET'])
@token_required
def get_user_stats(current_user, user_id):
    # Get stats for a specific user.
    try:
        stats = UserStats.get_user_stats(user_id)
        return jsonify({'success': True, 'stats': stats}), 200
    except Exception as e:
        print(f"Error in get_user_stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@users_routes.route('/following', methods=['GET'])
@token_required
def get_following(current_user):
    # Get list of users that the current user is following.
    try:
        user_id = current_user['id']
        result = User.get_following(user_id)
        
        if not result.get('success'):
            return jsonify({'success': False, 'error': 'Failed to get following list'}), 500
            
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in get_following: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


from flask import Blueprint, jsonify, request, g
from models.achievement import achievements, UserActivity
from routes.auth import token_required
from models.user import User
from database.connection import Database
from models.user_stats import UserStats

achievements_routes = Blueprint('achievements', __name__)

@achievements_routes.route('/user/<int:user_id>', methods=['GET'])
@token_required
def get_user_achievements(current_user, user_id):
    # Get achievements earned by a specific user
    try:

        earned_achievements = achievements.get_user_achievements(user_id)
        
        progress = achievements.get_user_progress(user_id)
        
        return jsonify({
            'success': True,
            'earned_achievements': earned_achievements,
            'progress': progress
        })
    except Exception as e:
        print(f"Error in get_user_achievements: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@achievements_routes.route('/', methods=['GET'])
@token_required
def get_achievements(current_user):
    # Get all achievements and user's progress.
    try:
        
        try:
            all_achievements = achievements.get_all()
        except Exception as e:
            print(f"GET /achievements - Error getting all achievements: {str(e)}")
            raise
        
        try:
            user_achievements = achievements.get_user_achievements(current_user['id'])
        except Exception as e:
            print(f"GET /achievements - Error getting user achievements: {str(e)}")
            raise
        
        earned_map = {ach['id']: ach['earned_at'] for ach in user_achievements}
        
        achievements_list = []
        
        for ach in all_achievements:
            try:
                achievement = {
                    'id': ach['id'],
                    'name': ach['name'],
                    'description': ach['description'],
                    'icon_name': ach.get('icon_name'),
                    'exp_reward': ach['exp_reward'],
                    'criteria': ach['criteria'],
                    'category': ach['category'],
                    'earned': ach['id'] in earned_map,
                    'earned_at': earned_map.get(ach['id'])
                }
                
                achievements_list.append(achievement)
            except Exception as e:
                print(f"GET /achievements - Error processing achievement {ach.get('id', 'unknown')}: {str(e)}")
        
        return jsonify({
            'success': True,
            'achievements': achievements_list
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"GET /achievements - Unhandled error: {str(e)}")
        print(f"GET /achievements - Traceback: {error_traceback}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__
        }), 500

@achievements_routes.route('/auto-check', methods=['POST'])
@token_required
def auto_check_achievements():
    # Check and award any completed achievements.
    try:
        unearned_with_progress = achievements.check_achievement_progress(g.user['id'])
        
        earned_achievements = achievements.get_user_achievements(g.user['id'])
        
        return jsonify({
            'success': True,
            'earned_count': len(earned_achievements),
            'progress': unearned_with_progress
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@achievements_routes.route('/activities', methods=['GET'])
@token_required
def get_activities():
    # Get user's activity feed.
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        activities = UserActivity.get_user_activities(
            g.user['id'], 
            limit=min(limit, 50),  
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'activities': activities
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@achievements_routes.route('/activities/stats', methods=['GET'])
@token_required
def get_activity_stats():
    # Get user's activity statistics.
    try:
        stats = UserActivity.get_user_stats(g.user['id'])
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@achievements_routes.route('/activities', methods=['POST'])
@token_required
def add_activity():
    # Add a new activity.
    try:
        data = request.get_json()
        if not data or 'activity_type' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        activity_type = data['activity_type']
        activity_data = data.get('activity_data', {})
        
        activity = UserActivity.add_activity(g.user['id'], activity_type, activity_data)
        
        unearned_with_progress = achievements.check_achievement_progress(g.user['id'])
        
        earned_achievements = achievements.get_user_achievements(g.user['id'])
        
        return jsonify({
            'success': True,
            'activity': activity,
            'earned_count': len(earned_achievements),
            'progress': unearned_with_progress
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@achievements_routes.route('/check', methods=['POST'])
@token_required
def manually_check_achievements(current_user):
    # Manually check achievements for the current user.
    try:
        user_id = current_user['id']
        
        from models.achievement import achievements
        unearned_with_progress = achievements.check_achievement_progress(user_id)
        
        from models.achievement import Achievements
        earned_achievements = Achievements.get_user_achievements(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Achievement progress checked successfully',
            'earned_count': len(earned_achievements),
            'unearned_count': len(unearned_with_progress),
            'progress': unearned_with_progress 
        }), 200
    except Exception as e:
        print(f"Error checking achievements: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error checking achievements: {str(e)}'
        }), 500

@achievements_routes.route('/refresh-stats', methods=['POST'])
@token_required
def refresh_user_stats(current_user):
    # Refresh all stats for the current user.
    try:
        user_id = current_user['id']
        
        updated_stats = UserStats.refresh_user_stats(user_id)

        from models.achievement import achievements
        unearned_with_progress = achievements.check_achievement_progress(user_id)
        
        from models.achievement import Achievements
        earned_achievements = Achievements.get_user_achievements(user_id)
        
        return jsonify({
            'success': True,
            'message': 'User stats refreshed successfully',
            'stats': updated_stats,
            'earned_count': len(earned_achievements),
            'progress': unearned_with_progress
        })
    except Exception as e:
        print(f"Error refreshing user stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

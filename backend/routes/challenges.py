from flask import Blueprint, request, jsonify
from models.challenge import Challenge, ChallengeCategory, ChallengeDifficulty
from models.auth import token_required, get_current_user
from database.connection import Database
import json

challenges_routes = Blueprint('challenges', __name__)

@challenges_routes.route('/', methods=['GET'])
def get_challenges():
    try:
        category = request.args.get('category')
        if category:
            try:
                category = ChallengeCategory(category)
            except ValueError:
                return jsonify({'error': f'Invalid category: {category}'}), 400
        
        challenges = Challenge.get_all(category=category)
        return jsonify(challenges), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@challenges_routes.route('/<int:challenge_id>', methods=['GET'])
def get_challenge(challenge_id):
    try:
        challenge = Challenge.get_by_id(challenge_id)
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404
        return jsonify(challenge), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@challenges_routes.route('/<int:challenge_id>/start', methods=['POST'])
@token_required
def start_challenge(current_user, challenge_id):
    try:
        result = Challenge.start(
            challenge_id=challenge_id,
            user_id=current_user['id']
        )
        
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        print(f"Error in start_challenge: {str(e)}")
        return jsonify({
            'error': str(e),
            'message': 'An unexpected error occurred',
            'success': False
        }), 500

@challenges_routes.route('/<int:challenge_id>/progress', methods=['POST'])
@token_required
def update_progress(current_user, challenge_id):
    try:
        data = request.get_json()
        
        if 'progress' not in data:
            return jsonify({'error': 'Missing required field: progress'}), 400
        
        result = Challenge.update_progress(
            challenge_id=challenge_id,
            user_id=current_user['id'],
            progress=data['progress']
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@challenges_routes.route('/<int:challenge_id>/complete', methods=['POST'])
@token_required
def complete_challenge(current_user, challenge_id):
    try:
        result = Challenge.complete(
            challenge_id=challenge_id,
            user_id=current_user['id']
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@challenges_routes.route('/<int:challenge_id>/submit', methods=['POST'])
@token_required
def submit_challenge(current_user, challenge_id):
    try:
        data = request.get_json()
        
        if 'submission' not in data:
            return jsonify({'error': 'Missing required field: submission'}), 400
        
        result = Challenge.submit(
            challenge_id=challenge_id,
            user_id=current_user['id'],
            submission=data['submission']
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@challenges_routes.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = Challenge.get_categories()
        return jsonify(categories), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@challenges_routes.route('/user', methods=['GET'])
@token_required
def get_user_challenges(current_user):
    try:        
        response_data = Challenge.get_user_challenges(current_user['id'])
        
        return jsonify(response_data), 200
    except Exception as e:
        print(f"Error in get_user_challenges: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@challenges_routes.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        leaderboard = Challenge.get_leaderboard()
        return jsonify(leaderboard), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@challenges_routes.route('/admin/submissions', methods=['GET'])
@token_required
def get_pending_submissions(current_user):
    # Get pending challenge submissions (admin/moderator only)
    try:
        
        if not current_user.get('roles') or not any(role in ['admin', 'moderator'] for role in current_user['roles']):
            return jsonify({'error': 'Unauthorized. Admin or moderator access required.'}), 403
            
        submissions = Challenge.get_pending_submissions()
        return jsonify(submissions), 200
    except Exception as e:
        print(f"Error getting pending submissions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@challenges_routes.route('/submissions/<int:submission_id>/review', methods=['POST'])
@token_required
def review_submission(current_user, submission_id):
    try:
        data = request.get_json()
        
        if 'approved' not in data:
            return jsonify({'error': 'Missing required field: approved'}), 400
        
        result = Challenge.review_submission(
            submission_id=submission_id,
            is_approved=data['approved'],
            feedback=data.get('feedback')
        )
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in review_submission: {str(e)}")
        return jsonify({'error': str(e)}), 500 
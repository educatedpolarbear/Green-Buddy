from flask import Blueprint, request, jsonify
from models.forum import Forum
from models.auth import token_required, get_current_user

forum_routes = Blueprint('forum', __name__)

@forum_routes.route('/', methods=['GET'])
def get_discussions():
    try:
        page = request.args.get('page', 1, type=int)
        category = request.args.get('category')
        
        discussions = Forum.get_discussions(page=page, category=category)
        return jsonify(discussions), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>', methods=['GET'])
def get_discussion(discussion_id):
    try:
        discussion = Forum.get_discussion_by_id(discussion_id)
        if not discussion:
            return jsonify({'error': 'Discussion not found'}), 404
        return jsonify(discussion), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/', methods=['POST'])
@token_required
def create_discussion(current_user):
    try:
        data = request.get_json()
        required_fields = ['title', 'content', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        discussion = Forum.create_discussion(
            author_id=current_user['id'],
            title=data['title'],
            content=data['content'],
            category=data['category'],
            excerpt=data['excerpt']
        )
        
        return jsonify(discussion), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>', methods=['PUT'])
@token_required
def update_discussion(current_user, discussion_id):
    try:
        data = request.get_json()
        
        discussion = Forum.update_discussion(
            discussion_id=discussion_id,
            author_id=current_user['id'],
            title=data.get('title'),
            content=data.get('content'),
            category=data.get('category')
        )
        
        if not discussion:
            return jsonify({'error': 'Discussion not found or unauthorized'}), 404
        return jsonify(discussion), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>', methods=['DELETE'])
@token_required
def delete_discussion(current_user, discussion_id):
    try:
        success = Forum.delete_discussion(discussion_id=discussion_id, user_id=current_user['id'])
        if not success:
            return jsonify({'error': 'Discussion not found or unauthorized'}), 404
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>/replies', methods=['GET'])
def get_replies(discussion_id):
    try:
        replies = Forum.get_replies(discussion_id)
        return jsonify(replies), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>/replies', methods=['POST'])
@token_required
def create_reply(current_user, discussion_id):
    try:
        data = request.get_json()
        if 'content' not in data:
            return jsonify({'error': 'Missing required field: content'}), 400
        
        reply = Forum.create_reply(
            discussion_id=discussion_id,
            author_id=current_user['id'],
            content=data['content']
        )
        
        return jsonify(reply), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>/solution/<int:reply_id>', methods=['POST'])
@token_required
def mark_solution(current_user, discussion_id, reply_id):
    try:
        success = Forum.mark_solution(
            reply_id=reply_id,
            discussion_id=discussion_id,
            user_id=current_user['id']
        )
        if not success:
            return jsonify({'error': 'Reply not found or unauthorized'}), 404
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>/like', methods=['POST'])
@token_required
def like_discussion(current_user, discussion_id):
    try:
        success = Forum.like_discussion(discussion_id=discussion_id, user_id=current_user['id'])
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>/like', methods=['DELETE'])
@token_required
def unlike_discussion(current_user, discussion_id):
    try:
        success = Forum.unlike_discussion(discussion_id=discussion_id, user_id=current_user['id'])
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>/replies/<int:reply_id>/like', methods=['POST'])
@token_required
def like_reply(current_user, discussion_id, reply_id):
    try:
        success = Forum.like_reply(reply_id=reply_id, user_id=current_user['id'])
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>/replies/<int:reply_id>/like', methods=['DELETE'])
@token_required
def unlike_reply(current_user, discussion_id, reply_id):
    try:
        success = Forum.unlike_reply(reply_id=reply_id, user_id=current_user['id'])
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = Forum.get_categories()
        return jsonify(categories), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/top-contributors', methods=['GET'])
def get_top_contributors():
    try:
        limit = request.args.get('limit', 10, type=int)
        contributors = Forum.get_top_contributors(limit=limit)
        return jsonify({'contributors': contributors}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/categories/<int:category_id>/experts', methods=['GET'])
def get_category_experts(category_id):
    try:
        limit = request.args.get('limit', 5, type=int)
        experts = Forum.get_category_experts(category_id, limit=limit)
        return jsonify({'experts': experts}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@forum_routes.route('/discussions/<int:discussion_id>/related', methods=['GET'])
def get_related_discussions(discussion_id):
    # Get discussions related to the specified discussion by category and popularity.
    try:
        limit = request.args.get('limit', 5, type=int)
        
        result = Forum.get_related_discussions(discussion_id, limit)
        
        if not result["success"]:
            return jsonify(result), 404
            
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@forum_routes.route('/discussions/<int:discussion_id>/view', methods=['POST'])
def track_discussion_view(discussion_id):
    # Track a view for a discussion.
    try:
        result = Forum.increment_discussion_view(discussion_id)
        
        if not result["success"]:
            return jsonify(result), 404
            
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500 
    
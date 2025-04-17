from flask import Blueprint, request, jsonify
from models.group import Group
from models.auth import token_required, get_current_user
from database.connection import Database
import models.websockets as websockets

groups_routes = Blueprint('groups', __name__)

@groups_routes.route('/', methods=['GET'])
def get_groups():
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search')
        
        groups = Group.get_all(
            page=page,
            search=search
        )
        
        return jsonify(groups), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/', methods=['POST'])
@token_required
def create_group(current_user):
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'description' not in data:
            return jsonify({
                'error': 'Missing required fields: name and description'
            }), 400
            
        group = Group.create(
            creator_id=current_user['id'],
            name=data['name'],
            description=data['description'],
            is_private=data.get('is_private', False)
        )
        
        if not group:
            return jsonify({
                'error': 'Failed to create group'
            }), 500
            
        return jsonify(group.to_dict()), 201
        
    except Exception as e:
        print(f"Error in create_group: {str(e)}")
        return jsonify({
            'error': 'Internal server error'
        }), 500

@groups_routes.route('/<int:group_id>', methods=['GET'])
def get_group(group_id):
    try:
        current_user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                current_user = get_current_user()
            except:
                pass 
        
        group = Group.get_by_id(group_id)
        if not group:
            return jsonify({'error': 'Group not found'}), 404
            
        group_dict = group.to_dict()
        
        if current_user:
            membership = Group.get_user_membership(group_id, current_user['id'])
            group_dict.update(membership)
        else:
            group_dict['is_member'] = False
            group_dict['role'] = None
            
        return jsonify(group_dict), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>', methods=['PUT'])
@token_required
def update_group(group_id):
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        group = Group.get_by_id(group_id)
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        if not Group.is_admin(group_id, current_user['id']):
            return jsonify({'error': 'Unauthorized to update this group'}), 403
        
        updated_group = Group.update(
            group_id=group_id,
            name=data.get('name'),
            description=data.get('description'),
            privacy=data.get('privacy'),
            category=data.get('category'),
            rules=data.get('rules')
        )
        
        return jsonify(updated_group), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>', methods=['DELETE'])
@token_required
def delete_group(group_id):
    try:
        current_user = get_current_user()
        
        group = Group.get_by_id(group_id)
        if not group:
            return jsonify({'error': 'Group not found'}), 404
        if not Group.is_admin(group_id, current_user['id']):
            return jsonify({'error': 'Unauthorized to delete this group'}), 403
        
        Group.delete(group_id)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>/join', methods=['POST'])
@token_required
def join_group(current_user, group_id):
    try:
        result = Group.join_group(current_user['id'], group_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>/leave', methods=['POST'])
@token_required
def leave_group(current_user, group_id):
    try:
        result = Group.remove_member(group_id, current_user['id'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>/members', methods=['GET'])
def get_members(group_id):
    try:
        group = Group.get_by_id(group_id)
        if not group:
            print(f"[Group Members] Group {group_id} not found")
            return jsonify({'error': 'Group not found'}), 404
            
        members = Group.get_members(group_id)
        return jsonify(members), 200
    except Exception as e:
        print(f"[Group Members] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>/posts', methods=['GET'])
def get_group_posts(group_id):
    try:
        group = Group.get_by_id(group_id)
        if not group:
            return jsonify({'error': 'Group not found'}), 404

        posts = Group.get_group_posts(group_id)
        return jsonify(posts), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>/posts', methods=['POST'])
@token_required
def create_group_post(current_user, group_id):
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'Content is required'}), 400

        if not Group.is_group_member(group_id, current_user['id']):
            return jsonify({'error': 'Must be a group member to post'}), 403

        post = Group.create_group_post(
            group_id=group_id,
            author_id=current_user['id'],
            content=data['content'],
            image_url=data.get('image_url')
        )

        return jsonify(post), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>/posts/<int:post_id>', methods=['DELETE'])
@token_required
def delete_group_post(current_user, group_id, post_id):
    try:
        try:
            Group.delete_group_post(post_id, group_id, current_user['id'])
            return jsonify({'success': True}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>/posts/<int:post_id>', methods=['PUT'])
@token_required
def update_group_post(current_user, group_id, post_id):
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'Content is required'}), 400

        try:
            post = Group.update_group_post(
                post_id=post_id,
                group_id=group_id,
                author_id=current_user['id'],
                content=data['content'],
                image_url=data.get('image_url')
            )
            return jsonify(post), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(group_id, post_id):
    try:
        comments = Group.get_post_comments(post_id)
        return jsonify(comments), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>/posts/<int:post_id>/comments', methods=['POST'])
@token_required
def create_post_comment(current_user, group_id, post_id):
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'Content is required'}), 400

        if not Group.is_group_member(group_id, current_user['id']):
            return jsonify({'error': 'Must be a group member to comment'}), 403

        comment = Group.create_post_comment(
            post_id=post_id,
            author_id=current_user['id'],
            content=data['content']
        )

        return jsonify(comment), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:group_id>/posts/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_post_comment(current_user, group_id, post_id, comment_id):
    try:
        try:
            Group.delete_post_comment(comment_id, post_id, group_id, current_user['id'])
            return jsonify({'success': True}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:id>/chat/messages', methods=['GET'])
@token_required
def get_chat_messages(current_user, id):
    try:
        
        group = Group.get_by_id(id)
        if not group:
            print(f"[Group Chat] Group {id} not found")
            return jsonify({'error': 'Group not found'}), 404

        if not Group.is_group_member(id, current_user['id']):
            print(f"[Group Chat] User {current_user['id']} is not a member of group {id}")
            return jsonify({'error': 'Must be a group member to view chat'}), 403

        messages = Group.get_chat_messages(id)
        
        return jsonify(messages), 200
    except Exception as e:
        print(f"[Group Chat] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:id>/chat/messages', methods=['POST'])
@token_required
def send_chat_message(current_user, id):
        
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'Message content is required'}), 400

        if not Group.is_group_member(id, current_user['id']):
            return jsonify({'error': 'Must be a group member to send messages'}), 403

        message = Group.create_chat_message(
            group_id=id,
            author_id=current_user['id'],
            content=data['content']
        )

        if websockets.socketio_instance:
            socket_message = {
                'id': message['id'],
                'content': message['content'],
                'group_id': id,
                'author_id': message['author_id'],
                'author_name': message['author_name'],
                'created_at': message['created_at'].isoformat() if message['created_at'] else None
            }
            websockets.socketio_instance.emit('group_chat_message', socket_message)

        return jsonify(message), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/<int:id>/chat/messages/<int:message_id>', methods=['DELETE'])
@token_required
def delete_chat_message(current_user, id, message_id):
    try:
        try:
            Group.delete_chat_message(message_id, id, current_user['id'])
            
            if websockets.socketio_instance:
                websockets.socketio_instance.emit('group_chat_message_deleted', {
                    'message_id': message_id,
                    'group_id': id
                })
                
            return jsonify({'success': True}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@groups_routes.route('/memberships', methods=['GET'])
@token_required
def get_user_group_memberships(current_user):
    # Get all groups the current user is a member of
    try:
        user_id = current_user['id']
        groups = Group.get_user_memberships(user_id)
        
        return jsonify(groups), 200
    except Exception as e:
        print(f"Error in get_user_group_memberships: {str(e)}")
        return jsonify({'error': str(e)}), 500 
from flask import Blueprint, request, jsonify
from models.learning import LearningResource, LearningComment
from models.auth import token_required, get_current_user
from database.connection import Database
from sqlalchemy import desc, func
import re
from bs4 import BeautifulSoup

learning_routes = Blueprint('learning', __name__, url_prefix='/learning')

@learning_routes.route('/', methods=['GET'])
def get_materials():
    try:
        category = request.args.get('category')
        type = request.args.get('type')
        search = request.args.get('search')
        
        result = LearningResource.get_all(
            category=category,
            type=type,
            search=search
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result['data']), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@learning_routes.route('/<int:material_id>', methods=['GET'])
def get_material(material_id):
    try:
        result = LearningResource.get_by_id(material_id)
        if not result['success']:
            return jsonify({'error': result['error']}), 404 if result['error'] == 'Material not found' else 500
        
        return jsonify(result['data']['material']), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@learning_routes.route('/categories', methods=['GET'])
def get_categories():
    try:
        content_type = request.args.get('content_type')
        result = LearningResource.get_categories(content_type=content_type)
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        return jsonify(result['data']), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@learning_routes.route('/<int:material_id>/view', methods=['POST'])
@token_required
def record_view(current_user, material_id):
    # Record that a user viewed a learning material.
    try:
        result = LearningResource.record_view(user_id=current_user['id'], material_id=material_id)
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        return jsonify(result), 200
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"Exception in record_view route: {error_type} - {error_msg}")
        return jsonify({"success": False, "error": f"{error_type}: {error_msg}"}), 500


@learning_routes.route('/<int:material_id>/complete', methods=['POST'])
@token_required
def record_completion(current_user, material_id):
    # Record that a user completed reading a learning material (scrolled to bottom).
    db = Database()
    conn = db.get_connection()
    
    try:        
        result = LearningResource.record_completion(user_id=current_user['id'], material_id=material_id)
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        return jsonify(result), 200
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        return jsonify({"success": False, "error": f"{error_type}: {error_msg}"}), 500
    finally:
        conn.close()

@learning_routes.route('/<int:material_id>/like', methods=['POST'])
@token_required
def toggle_like(current_user, material_id):
    # Toggle like status for a learning material.
    result = LearningResource.toggle_like(material_id, current_user['id'])
    
    if not result['success']:
        return jsonify({'error': result['error']}), 404 if result['error'] == 'Material not found' else 500
        
    return jsonify(result['data']), 200

@learning_routes.route('/<int:material_id>/comments', methods=['GET'])
def get_comments(material_id):
    # Get paginated comments for a learning material.
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        result = LearningComment.get_comments(material_id, page, per_page)
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        return jsonify(result['data']), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@learning_routes.route('/<int:material_id>/comments', methods=['POST'])
@token_required
def create_comment(current_user, material_id):
    # Create a new comment.
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Content is required'}), 400
        
        result = LearningComment.create_comment(
            material_id=material_id,
            user_id=current_user['id'],
            content=data['content'],
            parent_id=data.get('parent_id')
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400 if result['error'] == 'Invalid parent comment' else 500
            
        return jsonify(result['data']), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@learning_routes.route('/comments/<int:comment_id>/like', methods=['POST'])
@token_required
def toggle_comment_like(current_user, comment_id):
    # Toggle like status for a comment.
    try:
        result = LearningComment.toggle_comment_like(comment_id, current_user['id'])
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        return jsonify(result['data']), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@learning_routes.route('/<int:id>/related', methods=['GET'])
def get_related_materials(id):
    # Get related articles based on category.
    same_type_param = request.args.get('sameType', 'false')
    limit_param = request.args.get('limit', '3')
    
    same_type = same_type_param.lower() in ('true', '1', 't', 'y', 'yes')
    try:
        limit = int(limit_param)
    except ValueError:
        limit = 3 
    
    result = LearningResource.get_related_materials(id, limit, same_type)
    
    if not result['success']:
        return jsonify({'error': result['error']}), 404 if result['error'] == 'Material not found' else 500
        
    return jsonify(result['data']), 200

@learning_routes.route('/articles/author/<int:author_id>', methods=['GET'])
def get_author_articles(author_id):
    # Get articles by the same author.
    current_article_id = request.args.get('exclude_id', type=int)
    result = LearningResource.get_author_articles(author_id, exclude_id=current_article_id)
    
    if not result['success']:
        return jsonify({'error': result['error']}), 500
        
    return jsonify(result['data']), 200

@learning_routes.route('/<int:id>/increment-view', methods=['POST'])
@token_required
def increment_post_view(current_user, id):
    try:
        result = LearningResource.increment_views(id)
        if not result['success']:
            return jsonify({'error': result['error']}), 500
        return jsonify(result['data']), 200
    except Exception as e:
        print(f"Error incrementing view count: {str(e)}")
        return jsonify({'error': str(e)}), 500

@learning_routes.route('/featured', methods=['GET'])
def get_featured_content():
    # Get featured content based on views, likes, and comments.
    result = LearningResource.get_featured_content()
    
    if not result['success']:
        return jsonify({'error': result['error']}), 500
        
    return jsonify(result['data']), 200

@learning_routes.route('/community', methods=['POST'])
@token_required
def create_community_content(current_user):
    # Create a new community learning material (for regular users).
    try:
        data = request.get_json()
        
        required_fields = ['title', 'content', 'category_id', 'excerpt']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        data['type'] = 'community'
        
        result = LearningResource.create_material(
            user_id=current_user['id'],
            title=data['title'],
            content=data['content'],
            category_id=data['category_id'],
            type=data['type'],
            excerpt=data['excerpt'],
            thumbnail_url=data.get('thumbnail_url'),
            duration=data.get('duration'),
            tags=data.get('tags', [])
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result['data']), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@learning_routes.route('/admin/materials', methods=['POST'])
@token_required
def create_admin_content(current_user):
    # Create any type of learning material (admin only).
    try:
        if 'roles' not in current_user or 'admin' not in current_user['roles']:
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        data = request.get_json()
        
        required_fields = ['title', 'content', 'category_id', 'type', 'excerpt']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        valid_types = ['video', 'article', 'wiki', 'community']
        if data['type'] not in valid_types:
            return jsonify({'error': f'Invalid type. Must be one of: {", ".join(valid_types)}'}), 400
        
        if data['type'] == 'article':
            if len(data['content']) < 100:
                return jsonify({'error': 'Article content is too short. Minimum 100 characters required.'}), 400
            
            soup = BeautifulSoup(data['content'], 'html.parser')
            
            for tag in soup.find_all():
                if tag.name not in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre', 'strong', 'em', 'span', 'div']:
                    tag.decompose()
                else:
                    attrs = dict(tag.attrs)
                    for attr in attrs:
                        if attr not in ['href', 'src', 'alt', 'class']:
                            del tag[attr]
                    
                    if tag.name == 'a' and 'href' in tag.attrs:
                        href = tag['href']
                        if not href.startswith(('http://', 'https://', '/')):
                            tag['href'] = '#'
                    
                    if tag.name == 'img' and 'src' in tag.attrs:
                        src = tag['src']
                        if not src.startswith(('http://', 'https://', '/')):
                            tag['src'] = '/placeholder.svg'
            
            data['content'] = str(soup)
            
            if not data.get('duration'):
                word_count = len(soup.get_text().split())
                reading_minutes = max(1, round(word_count / 200)) 
                data['duration'] = f'{reading_minutes} min read'
            
            if not data.get('excerpt') or len(data['excerpt']) < 10:
                plain_text = soup.get_text()
                data['excerpt'] = plain_text[:150] + ('...' if len(plain_text) > 150 else '')
        
        elif data['type'] == 'video':
            if not data.get('content') or len(data['content']) < 5:
                return jsonify({'error': 'Video ID is required'}), 400
            
            youtube_id_pattern = r'^[a-zA-Z0-9_-]{11}$'
            if not re.match(youtube_id_pattern, data['content']):
                youtube_url_pattern = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
                match = re.search(youtube_url_pattern, data['content'])
                if match:
                    data['content'] = match.group(1)
                else:
                    return jsonify({'error': 'Invalid YouTube video ID or URL'}), 400
            
            if not data.get('thumbnail_url'):
                data['thumbnail_url'] = f'https://img.youtube.com/vi/{data["content"]}/maxresdefault.jpg'
            
        elif data['type'] == 'wiki':
            if len(data['content']) < 200:
                return jsonify({'error': 'Wiki content is too short. Minimum 200 characters required.'}), 400
            
            soup = BeautifulSoup(data['content'], 'html.parser')
            
            if not data.get('duration'):
                data['duration'] = None
                
        result = LearningResource.create_material(
            user_id=current_user['id'],
            title=data['title'],
            content=data['content'],
            category_id=data['category_id'],
            type=data['type'],
            excerpt=data['excerpt'],
            thumbnail_url=data.get('thumbnail_url'),
            duration=data.get('duration'),
            tags=data.get('tags', [])
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result['data']), 201
    except Exception as e:
        print(f"Error in create_admin_content: {str(e)}")
        return jsonify({'error': str(e)}), 500

@learning_routes.route('/<int:material_id>', methods=['DELETE'])
@token_required
def delete_material(current_user, material_id):
    # Delete a learning material (admin or material author only).
    try:
        result = LearningResource.delete_material(material_id, current_user['id'])
        
        if not result['success']:
            status_code = 404 if result['error'] == 'Material not found' else 403 if 'Unauthorized' in result['error'] else 500
            return jsonify({'error': result['error']}), status_code
        
        return '', 204  # No content success response
    except Exception as e:
        print(f"Error in delete_material route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@learning_routes.route('/<int:material_id>', methods=['PUT'])
@token_required
def update_material(current_user, material_id):
    # Update a learning material (admin or material author only).
    try:
        material = LearningResource.get_by_id(material_id)
        if not material['success']:
            return jsonify({'error': material['error']}), 404
        
        material_data = material['data']['material']
        is_admin = 'roles' in current_user and 'admin' in current_user['roles']
        is_author = material_data['author_id'] == current_user['id']
        
        if material_data['type'] == 'community':
            if not is_author:
                return jsonify({'error': 'Unauthorized. Only the author can edit community content.'}), 403
        else:
            if not (is_admin or is_author):
                return jsonify({'error': 'Unauthorized. You must be an admin or the author to update this content.'}), 403
        
        data = request.get_json()
        
        required_fields = ['title', 'content', 'category_id', 'type', 'excerpt']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        original_type = material_data['type']
        if data['type'] != original_type:
            return jsonify({'error': 'Changing the content type is not allowed'}), 400
        
        if data['type'] == 'article':
            if len(data['content']) < 100:
                return jsonify({'error': 'Article content is too short. Minimum 100 characters required.'}), 400
            
            soup = BeautifulSoup(data['content'], 'html.parser')
            
            for tag in soup.find_all():
                if tag.name not in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre', 'strong', 'em', 'span', 'div']:
                    tag.decompose()
                else:
                    attrs = dict(tag.attrs)
                    for attr in attrs:
                        if attr not in ['href', 'src', 'alt', 'class']:
                            del tag[attr]
                    
                    if tag.name == 'a' and 'href' in tag.attrs:
                        href = tag['href']
                        if not href.startswith(('http://', 'https://', '/')):
                            tag['href'] = '#'
                    
                    if tag.name == 'img' and 'src' in tag.attrs:
                        src = tag['src']
                        if not src.startswith(('http://', 'https://', '/')):
                            tag['src'] = '/placeholder.svg'
            
            data['content'] = str(soup)
            
            if not data.get('duration'):
                word_count = len(soup.get_text().split())
                reading_minutes = max(1, round(word_count / 200)) 
                data['duration'] = f'{reading_minutes} min read'
            
            if not data.get('excerpt') or len(data['excerpt']) < 10:
                plain_text = soup.get_text()
                data['excerpt'] = plain_text[:150] + ('...' if len(plain_text) > 150 else '')
        
        elif data['type'] == 'video':
            if not data.get('content') or len(data['content']) < 5:
                return jsonify({'error': 'Video ID is required'}), 400
            
            youtube_id_pattern = r'^[a-zA-Z0-9_-]{11}$'
            if not re.match(youtube_id_pattern, data['content']):
                youtube_url_pattern = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
                match = re.search(youtube_url_pattern, data['content'])
                if match:
                    data['content'] = match.group(1)
                else:
                    return jsonify({'error': 'Invalid YouTube video ID or URL'}), 400
            
            if not data.get('thumbnail_url'):
                data['thumbnail_url'] = f'https://img.youtube.com/vi/{data["content"]}/maxresdefault.jpg'
            
        elif data['type'] == 'wiki':
            if len(data['content']) < 200:
                return jsonify({'error': 'Wiki content is too short. Minimum 200 characters required.'}), 400
            
        elif data['type'] == 'community':
            if len(data['content']) < 50:
                return jsonify({'error': 'Community content is too short. Minimum 50 characters required.'}), 400
            
        
        result = LearningResource.update_material(
            material_id=material_id,
            user_id=current_user['id'],
            title=data['title'],
            content=data['content'],
            category_id=data['category_id'],
            type=data['type'],
            excerpt=data['excerpt'],
            thumbnail_url=data.get('thumbnail_url'),
            duration=data.get('duration'),
            tags=data.get('tags', [])
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
            
        return jsonify({'material': result['data']}), 200
    except Exception as e:
        print(f"Error in update_material route: {str(e)}")
        return jsonify({'error': str(e)}), 500

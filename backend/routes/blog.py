from flask import Blueprint, request, jsonify
from models.blog import BlogPost
from models.auth import token_required, get_current_user, verify_token

blog_routes = Blueprint('blog', __name__)

@blog_routes.route('/', methods=['GET'])
def get_posts():
    try:
        category = request.args.get('category')
        search = request.args.get('search')
        author_id = request.args.get('author_id')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        tag = request.args.get('tag')  
        
        current_user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            if payload and 'user_id' in payload:
                current_user_id = payload['user_id']
        
        
        result = BlogPost.get_all(
            category=category,
            search=search,
            author_id=author_id,
            tag=tag,
            page=page,
            per_page=per_page,
            current_user_id=current_user_id
        )
        
        
        if not isinstance(result, dict) or 'posts' not in result:
            raise ValueError("Invalid result format from database")
            
        response = {
            'success': True,
            'posts': result['posts'],
            'total': result['total'],
            'total_pages': result['total_pages'],
            'current_page': page
        }
                
        return jsonify(response), 200
    except Exception as e:
        print(f"Error fetching posts: {str(e)}", exc_info=True)
        print(f"Error type: {type(e)}")
        print(f"Error details: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': str(type(e)),
            'posts': []
        }), 500

@blog_routes.route('/', methods=['POST'])
@token_required
def create_post(current_user):
    try:
        data = request.get_json()
        
        required_fields = ['title', 'content', 'tags']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        post = BlogPost.create(
            author_id=current_user['id'],
            title=data['title'],
            content=data['content'],
            excerpt=data['excerpt'],
            featured_image_url=data['featured_image_url'],
            tags=data.get('tags', [])
        )
                
        return jsonify(post), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        current_user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            if payload and 'user_id' in payload:
                current_user_id = payload['user_id']
        
        post = BlogPost.get_by_id(post_id, current_user_id)
        if not post:
            return jsonify({'error': 'Blog post not found'}), 404
        return jsonify(post), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/<int:post_id>', methods=['PUT'])
@token_required
def update_post(post_id):
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        post = BlogPost.get_by_id(post_id)
        if not post:
            return jsonify({'error': 'Blog post not found'}), 404
        if post['author_id'] != current_user['id']:
            return jsonify({'error': 'Unauthorized to update this post'}), 403
        
        updated_post = BlogPost.update(
            post_id=post_id,
            title=data.get('title'),
            content=data.get('content'),
            category=data.get('category'),
            tags=data.get('tags')
        )
        
        return jsonify(updated_post), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user, post_id):
    try:
        
        post = BlogPost.get_by_id(post_id)
        if not post:
            return jsonify({'error': 'Blog post not found'}), 404
        if post['author_id'] != current_user['id']:
            return jsonify({'error': 'Unauthorized to delete this post'}), 403
        
        BlogPost.delete(post_id)
        return jsonify({'message': 'Blog post deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/<int:post_id>/like', methods=['POST'])
@token_required
def like_post(current_user, post_id):
    try:
        result = BlogPost.add_like(post_id, current_user['id'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/<int:post_id>/like', methods=['DELETE'])
def unlike_post(post_id):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False, 
                'message': 'No token provided'
            }), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if not payload or 'user_id' not in payload:
            return jsonify({
                'success': False, 
                'message': 'Invalid token'
            }), 401
        
        user_id = payload['user_id']
        
        result = BlogPost.remove_like(post_id, user_id)
        
        return jsonify({
            'success': True,
            'message': 'Post unliked successfully'
        }), 200
    except Exception as e:
        print(f"Error unliking post: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@blog_routes.route('/<int:post_id>/related', methods=['GET'])
def get_related_posts(post_id):
    try:
        limit = request.args.get('limit', 3, type=int)
        
        current_user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            if payload and 'user_id' in payload:
                current_user_id = payload['user_id']
        
        related_posts = BlogPost.get_related(post_id, limit, current_user_id)
        
        return jsonify({
            'success': True,
            'posts': related_posts
        }), 200
    except Exception as e:
        print(f"Error fetching related posts: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'posts': []
        }), 500

@blog_routes.route('/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    try:
        comments = BlogPost.get_comments(post_id)
        return jsonify(comments), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/<int:post_id>/comments', methods=['POST'])
@token_required
def add_comment(current_user, post_id):
    try:
        data = request.get_json()
        
        if 'content' not in data:
            return jsonify({'error': 'Missing required field: content'}), 400
        
        comment = BlogPost.add_comment(
            post_id=post_id,
            user_id=current_user['id'],
            content=data['content']
        )
        
        return jsonify(comment), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = BlogPost.get_categories()
        return jsonify(categories), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/featured', methods=['GET'])
def get_featured_posts():
    try:
        limit = request.args.get('limit', 3, type=int)
        
        posts = BlogPost.get_featured(limit=limit)
        response = {
            'success': True,
            'posts': posts
        }
        return jsonify(response), 200
    except Exception as e:
        print(f"Error fetching featured posts: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e),
            'posts': []
        }), 500

@blog_routes.route('/<int:post_id>/increment-view', methods=['POST'])
def increment_post_view(post_id):
    try:
        BlogPost.increment_views(post_id)
        return jsonify({'message': 'View count incremented successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/tags', methods=['GET'])
def get_tags():
    try:
        tags = BlogPost.get_tags()
        response = {
            'success': True,
            'tags': tags
        }
        return jsonify(response), 200
    except Exception as e:
        print(f"Error fetching tags: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e),
            'tags': []
        }), 500

@blog_routes.route('/comments/<int:comment_id>/like', methods=['POST'])
@token_required
def like_comment(current_user, comment_id):
    try:
        result = BlogPost.add_comment_like(comment_id, current_user['id'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/comments/<int:comment_id>/unlike', methods=['POST'])
@token_required
def unlike_comment(current_user, comment_id):
    try:
        result = BlogPost.remove_comment_like(comment_id, current_user['id'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_routes.route('/tags/trending', methods=['GET'])
def get_trending_tags():
    try:
        tags = BlogPost.get_trending_tags()
        response = {
            'success': True,
            'tags': tags
        }
        return jsonify(response), 200
    except Exception as e:
        print(f"Error fetching trending tags: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e),
            'tags': []
        }), 500

@blog_routes.route('/authors/top', methods=['GET'])
def get_top_authors():
    try:
        limit = request.args.get('limit', 5, type=int)
        
        authors = BlogPost.get_top_authors(limit=limit)
        response = {
            'success': True,
            'authors': authors
        }
        return jsonify(response), 200
    except Exception as e:
        print(f"Error fetching top authors: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': str(e),
            'authors': []
        }), 500 
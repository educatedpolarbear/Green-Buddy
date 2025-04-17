from flask import Blueprint, request, jsonify
from models.event import Event
from models.auth import token_required, get_current_user, verify_token
from datetime import datetime
import logging

events_routes = Blueprint('events', __name__)

logger = logging.getLogger(__name__)

@events_routes.route('/', methods=['GET'])
def get_events():
    try:
        category = request.args.get('category')
        status = request.args.get('status')
        search = request.args.get('search')
        location = request.args.get('location')
        start_date = request.args.get('start_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        auth_header = request.headers.get('Authorization')
        user_id = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = verify_token(token)
                if payload and 'user_id' in payload:
                    user_id = payload.get('user_id')
            except Exception as e:
                logger.error(f"Error decoding token: {str(e)}")
        
        result = Event.get_all(
            category=category,
            status=status,
            search=search,
            location=location,
            start_date=start_date,
            user_id=user_id
        )
        
        return jsonify({
            'events': result['events'],
            'page': result['page'],
            'total': result['total'],
            'total_pages': result['total_pages']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'events': []}), 500

@events_routes.route('/', methods=['POST'])
@token_required
def create_event():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        required_fields = ['title', 'description', 'start_date', 'end_date', 'location', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%dT%H:%M:%S')
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

        if end_date <= start_date:
            return jsonify({'error': 'End date must be after start date'}), 400
        
        event = Event.create(
            organizer_id=current_user['id'],
            title=data['title'],
            description=data['description'],
            start_date=start_date,
            end_date=end_date,
            location=data['location'],
            category=data['category'],
            max_participants=data.get('max_participants'),
            status=data.get('status', 'draft'),
            requirements=data.get('requirements'),
            schedule=data.get('schedule'),
            organizer_name=data.get('organizer_name'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            image_url=data.get('image_url')
        )
        
        return jsonify(event), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_routes.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    try:
        auth_header = request.headers.get('Authorization')
        user_id = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = verify_token(token)
                if payload and 'user_id' in payload:
                    user_id = payload.get('user_id')
            except Exception as e:
                print(f"Error decoding token: {str(e)}")
        
        event = Event.get_by_id(event_id, user_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        return jsonify(event), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_routes.route('/<int:event_id>', methods=['PUT'])
@token_required
def update_event(event_id):
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        event = Event.get_by_id(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        if event['organizer_id'] != current_user['id']:
            return jsonify({'error': 'Unauthorized to update this event'}), 403
        
        # Parse dates if provided
        start_date = None
        end_date = None
        if data.get('start_date'):
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                return jsonify({'error': 'Invalid start date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
                
        if data.get('end_date'):
            try:
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                return jsonify({'error': 'Invalid end date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
        
        if start_date and end_date and end_date <= start_date:
            return jsonify({'error': 'End date must be after start date'}), 400
        
        updated_event = Event.update(
            event_id=event_id,
            title=data.get('title'),
            description=data.get('description'),
            start_date=start_date,
            end_date=end_date,
            location=data.get('location'),
            category=data.get('category'),
            max_participants=data.get('max_participants'),
            status=data.get('status'),
            requirements=data.get('requirements'),
            schedule=data.get('schedule'),
            organizer_name=data.get('organizer_name'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            image_url=data.get('image_url')
        )
        
        return jsonify(updated_event), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_routes.route('/<int:event_id>', methods=['DELETE'])
@token_required
def delete_event(event_id):
    try:
        current_user = get_current_user()
        
        event = Event.get_by_id(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        if event['organizer_id'] != current_user['id']:
            return jsonify({'error': 'Unauthorized to delete this event'}), 403
        
        Event.delete(event_id)
        return jsonify({'message': 'Event deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_routes.route('/<int:event_id>/register', methods=['POST'])
@token_required
def register_for_event(current_user, event_id):
    try:
        result = Event.register_participant(event_id, current_user['id'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_routes.route('/<int:event_id>/unregister', methods=['POST'])
@token_required
def unregister_from_event(current_user, event_id):
    # Unregister a user from an event.
    try:
        if not current_user or 'id' not in current_user:
            logger.error("Invalid user data in token")
            return jsonify({'error': 'Invalid user data'}), 401
            
        if not isinstance(event_id, int) or event_id <= 0:
            logger.error(f"Invalid event_id: {event_id}")
            return jsonify({'error': 'Invalid event ID'}), 400
            
        result = Event.unregister_participant(event_id, current_user['id'])
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error unregistering from event: {str(e)}")
        return jsonify({'error': 'Failed to unregister from event'}), 500

@events_routes.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = Event.get_categories()
        return jsonify(categories), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_routes.route('/<int:event_id>/vote', methods=['GET'])
@token_required
def get_user_vote(current_user, event_id):
    try:
        vote_type = Event.get_user_vote(event_id, current_user['id'])
        return jsonify({'vote_type': vote_type}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_routes.route('/<int:event_id>/vote', methods=['POST'])
@token_required
def vote_for_event(current_user, event_id):
    try:
        data = request.get_json()
        if not data or 'vote_type' not in data:
            return jsonify({'error': 'Vote type is required'}), 400
            
        vote_type = data['vote_type']
        if vote_type not in ['upvote', 'downvote']:
            return jsonify({'error': 'Invalid vote type'}), 400
            
        result = Event.vote(event_id, current_user['id'], vote_type)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_routes.route('/<int:event_id>/comments', methods=['GET'])
def get_event_comments(event_id):
    try:
        comments = Event.get_comments(event_id)
        return jsonify(comments), 200
    except Exception as e:
        print(f"Error getting comments: {str(e)}")
        return jsonify({'error': 'Failed to fetch comments', 'details': str(e)}), 500

@events_routes.route('/<int:event_id>/comments', methods=['POST'])
@token_required
def add_event_comment(current_user, event_id):
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Comment content is required'}), 400
        
        if not data['content'].strip():
            return jsonify({'error': 'Comment content cannot be empty'}), 400
            
        comment = Event.add_comment(event_id, current_user['id'], data['content'])
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error adding comment: {str(e)}")
        return jsonify({'error': 'Failed to add comment', 'details': str(e)}), 500

@events_routes.route('/<int:event_id>/user-registration', methods=['GET'])
@token_required
def check_user_registration(current_user, event_id):
    """Check if the current user is registered for an event."""
    try:
        event = Event.get_by_id(event_id, current_user['id'])
        if not event:
            return jsonify({'error': 'Event not found'}), 404
            
        return jsonify({
            'is_registered': event.get('is_registered', False)
        }), 200
    except Exception as e:
        print(f"Error checking registration status: {str(e)}")
        return jsonify({'error': str(e)}), 500 
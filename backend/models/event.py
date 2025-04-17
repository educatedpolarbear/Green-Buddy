from database.connection import Database
from models.user_stats import UserStats
from models.achievement import UserActivity, achievements

class Event:
    @staticmethod
    def get_all(page=1, category=None, status=None, search=None, location=None, start_date=None, user_id=None):
        # Get all events with calculated fields.
        try:
            db = Database()
            conn = db.get_connection()
            if not conn:
                raise Exception("Database connection failed")
            
            cursor = conn.cursor(dictionary=True)
            
            base_query = """
                SELECT 
                    e.*,
                    c.name as category_name,
                    u.username as organizer_username,
                    COUNT(DISTINCT ep.user_id) as participant_count,
                    COUNT(DISTINCT CASE WHEN ev.vote_type = 'upvote' THEN ev.id END) as upvotes,
                    COUNT(DISTINCT CASE WHEN ev.vote_type = 'downvote' THEN ev.id END) as downvotes,
                    CASE WHEN ep_current.user_id IS NOT NULL THEN TRUE ELSE FALSE END as is_registered
                FROM events e
                LEFT JOIN event_categories c ON e.category_id = c.id
                LEFT JOIN users u ON e.organizer_id = u.id
                LEFT JOIN event_participants ep ON e.id = ep.event_id
                LEFT JOIN event_votes ev ON e.id = ev.event_id
                LEFT JOIN event_participants ep_current ON e.id = ep_current.event_id 
                    AND ep_current.user_id = %s
            """
            
            where_conditions = []
            params = [user_id if user_id else None] 
            
            if category:
                where_conditions.append("c.id = %s")
                params.append(category)
            
            if status:
                where_conditions.append("e.status = %s")
                params.append(status)
            
            if search:
                where_conditions.append("(e.title LIKE %s OR e.description LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            if location:
                where_conditions.append("e.location LIKE %s")
                params.append(f"%{location}%")
            
            if start_date:
                where_conditions.append("DATE(e.start_date) = DATE(%s)")
                params.append(start_date)
            
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            count_query = f"""
                SELECT COUNT(DISTINCT e.id) as total
                FROM events e
                LEFT JOIN event_categories c ON e.category_id = c.id
                {where_clause}
            """
            
            count_params = params[1:] if len(params) > 1 else []
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['total']
            
            per_page = 10
            offset = (page - 1) * per_page
            
            query = base_query + where_clause + """
                GROUP BY e.id
                ORDER BY e.start_date ASC
                LIMIT %s OFFSET %s
            """
            
            params.extend([per_page, offset])
            cursor.execute(query, params)
            events = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'events': events,
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        except Exception as e:
            print(f"Error getting events: {e}")
            return {
                'events': [],
                'page': page,
                'per_page': 10,
                'total': 0,
                'total_pages': 0
            }

    @staticmethod
    def get_by_id(event_id, user_id=None):
        # Get event by ID with all calculated fields.
        try:
            db = Database()
            conn = db.get_connection()
            if not conn:
                raise Exception("Database connection failed")
            
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT COUNT(*) as raw_count
                FROM event_participants
                WHERE event_id = %s
            """, (event_id,))
            raw_count = cursor.fetchone()['raw_count']
            
            query = """
                SELECT 
                    e.*,
                    c.name as category_name,
                    u.username as organizer_username,
                    u.id as organizer_id,
                    u.avatar_url as organizer_avatar_url,
                    u.bio as organizer_bio,
                    u.email as organizer_email,
                    COUNT(DISTINCT ep.user_id) as participant_count,
                    COUNT(DISTINCT CASE WHEN ev.vote_type = 'upvote' THEN ev.id END) as upvotes,
                    COUNT(DISTINCT CASE WHEN ev.vote_type = 'downvote' THEN ev.id END) as downvotes,
                    CASE WHEN ep_current.user_id IS NOT NULL THEN TRUE ELSE FALSE END as is_registered
                FROM events e
                LEFT JOIN event_categories c ON e.category_id = c.id
                LEFT JOIN users u ON e.organizer_id = u.id
                LEFT JOIN event_participants ep ON e.id = ep.event_id
                LEFT JOIN event_votes ev ON e.id = ev.event_id
                LEFT JOIN event_participants ep_current ON e.id = ep_current.event_id 
                    AND ep_current.user_id = %s
                WHERE e.id = %s
                GROUP BY e.id, c.name, u.username, u.id, u.avatar_url, u.bio, u.email, ep_current.user_id
            """
            
            cursor.execute(query, (user_id if user_id else None, event_id))
            event = cursor.fetchone()
            
            if event:
                if event['participant_count'] != raw_count:
                    print(f"WARNING: Participant count mismatch! Raw: {raw_count}, Calculated: {event['participant_count']}")
                    event['participant_count'] = raw_count
                
                event['organizer'] = {
                    'id': event.pop('organizer_id', None),
                    'name': event.pop('organizer_name', None) or event['organizer_username'],
                    'username': event.pop('organizer_username', None),
                    'avatar_url': event.pop('organizer_avatar_url', None),
                    'description': event.pop('organizer_bio', None),
                    'email': event.pop('organizer_email', None),
                    'phone': event.get('contact_phone', None)
                }
                
                cursor.execute("""
                    SELECT 
                        u.username as name,
                        u.avatar_url
                    FROM event_participants ep
                    JOIN users u ON ep.user_id = u.id
                    WHERE ep.event_id = %s
                    LIMIT 10
                """, (event_id,))
                
                event['attendees'] = cursor.fetchall()
                
                cursor.execute("""
                    SELECT 
                        e.id,
                        e.title,
                        e.start_date
                    FROM events e
                    WHERE e.category_id = %s
                      AND e.id != %s
                      AND e.status = 'published'
                    ORDER BY e.start_date ASC
                    LIMIT 3
                """, (event['category_id'], event_id))
                
                event['similar_events'] = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return event
        except Exception as e:
            print(f"Error getting event: {e}")
            return None

    @staticmethod
    def create(organizer_id, title, description, start_date, end_date, location, category, 
               max_participants=None, status='draft', requirements=None, schedule=None,
               organizer_name=None, contact_email=None, contact_phone=None, image_url=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT id FROM event_categories WHERE name = %s", (category,))
            category_result = cursor.fetchone()
            if not category_result:
                raise ValueError(f"Category '{category}' not found")
            
            valid_statuses = ['draft', 'published', 'cancelled', 'completed']
            if status not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
            
            query = """
                INSERT INTO events (
                    organizer_id, title, description, start_date, end_date,
                    location, category_id, max_participants, status, created_at,
                    requirements, schedule, organizer_name, contact_email,
                    contact_phone, image_url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                organizer_id, title, description, start_date, end_date,
                location, category_result['id'], max_participants, status,
                requirements, schedule, organizer_name, contact_email,
                contact_phone, image_url
            ))
            
            conn.commit()
            event_id = cursor.lastrowid
            
            return Event.get_by_id(event_id)
        except Exception as e:
            conn.rollback()
            print(f"Error in create: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update(event_id, title=None, description=None, start_date=None, end_date=None, 
              location=None, category=None, max_participants=None, status=None,
              requirements=None, schedule=None, organizer_name=None,
              contact_email=None, contact_phone=None, image_url=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            updates = []
            params = []
            
            field_updates = {
                'title': title,
                'description': description,
                'start_date': start_date,
                'end_date': end_date,
                'location': location,
                'max_participants': max_participants,
                'requirements': requirements,
                'schedule': schedule,
                'organizer_name': organizer_name,
                'contact_email': contact_email,
                'contact_phone': contact_phone,
                'image_url': image_url
            }
            
            for field, value in field_updates.items():
                if value is not None:
                    updates.append(f"{field} = %s")
                    params.append(value)
            
            if category is not None:
                cursor.execute("SELECT id FROM event_categories WHERE name = %s", (category,))
                category_result = cursor.fetchone()
                if not category_result:
                    raise ValueError(f"Category '{category}' not found")
                updates.append("category_id = %s")
                params.append(category_result['id'])
            
            if status is not None:
                valid_statuses = ['draft', 'published', 'cancelled', 'completed']
                if status not in valid_statuses:
                    raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
                updates.append("status = %s")
                params.append(status)
            
            if updates:
                query = f"UPDATE events SET {', '.join(updates)} WHERE id = %s"
                params.append(event_id)
                
                cursor.execute(query, params)
                conn.commit()
            
            return Event.get_by_id(event_id)
        except Exception as e:
            conn.rollback()
            print(f"Error in update: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(event_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM event_participants WHERE event_id = %s", (event_id,))
            
            cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error in delete: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def register_participant(event_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            if isinstance(user_id, dict) and 'id' in user_id:
                user_id = user_id['id']
            elif not isinstance(user_id, int):
                try:
                    user_id = int(user_id)
                except (ValueError, TypeError):
                    raise ValueError("Invalid user ID")
            
            cursor.execute("""
                SELECT 
                    e.*,
                    COUNT(p.user_id) as current_participants
                FROM events e
                LEFT JOIN event_participants p ON e.id = p.event_id
                WHERE e.id = %s
                GROUP BY e.id
            """, (event_id,))
            
            event = cursor.fetchone()
            if not event:
                raise ValueError("Event not found")
            
            cursor.execute(
                "SELECT 1 FROM event_participants WHERE event_id = %s AND user_id = %s",
                (event_id, user_id)
            )
            if cursor.fetchone():
                cursor.execute(
                    "DELETE FROM event_participants WHERE event_id = %s AND user_id = %s",
                    (event_id, user_id)
                )
                conn.commit()
                
                
                return {"message": "Successfully unregistered from event"}
            
            if event['max_participants'] and event['current_participants'] >= event['max_participants']:
                raise ValueError("Event is full")
            
            cursor.execute(
                "INSERT INTO event_participants (event_id, user_id, registered_at) VALUES (%s, %s, NOW())",
                (event_id, user_id)
            )
            
            conn.commit()

            try:
                from models.user_stats import UserStats
                UserStats.update_stat_and_achievements(
                    user_id,
                    'events_joined',
                    {
                        'event_id': event_id,
                        'event_title': event.get('title', 'Unknown Event')
                    }
                )
            except Exception as e:
                print(f"Error updating stats: {str(e)}")
                        
            return {"message": "Successfully registered for event"}
        except Exception as e:
            conn.rollback()
            print(f"Error in register_participant: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def unregister_participant(event_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            if isinstance(user_id, dict) and 'id' in user_id:
                user_id = user_id['id']
            elif not isinstance(user_id, int):
                try:
                    user_id = int(user_id)
                except (ValueError, TypeError):
                    raise ValueError("Invalid user ID")
            
            cursor.execute(
                "SELECT e.* FROM events e WHERE e.id = %s",
                (event_id,)
            )
            event = cursor.fetchone()
            
            cursor.execute(
                "DELETE FROM event_participants WHERE event_id = %s AND user_id = %s",
                (event_id, user_id)
            )
            
            if cursor.rowcount > 0:
                conn.commit()

                try:
                    from models.user_stats import UserStats
                    UserStats.update_stat_and_achievements(
                        user_id, 
                        'events_unregistered',
                        {
                            'event_id': event_id,
                            'event_title': event.get('title', 'Unknown Event')
                        }
                    )
                except Exception as e:
                    print(f"Error updating stats: {str(e)}")
                
                return {"message": "Successfully unregistered from event"}
            else:
                return {"message": "User was not registered for this event"}
        except Exception as e:
            conn.rollback()
            print(f"Error in unregister_participant: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_categories():
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            try:
                cursor.execute("""
                    SELECT c.*, COUNT(e.id) as event_count
                    FROM event_categories c
                    LEFT JOIN events e ON c.id = e.category_id
                    GROUP BY c.id
                    ORDER BY c.name
                """)
                               
                return cursor.fetchall()
            except Exception as e:
                if "Table 'green_buddy.event_categories' doesn't exist" in str(e):
                    return [{
                        'id': 1,
                        'name': 'General',
                        'description': 'Default category for all events',
                        'event_count': 0
                    }]
                raise e
            
        except Exception as e:
            print(f"Error in get_categories: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_vote(event_id, user_id):
        # Get a user's vote for an event.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            if isinstance(user_id, dict) and 'id' in user_id:
                user_id = user_id['id']
            elif not isinstance(user_id, int):
                try:
                    user_id = int(user_id)
                except (ValueError, TypeError):
                    raise ValueError("Invalid user ID")
            
            cursor.execute(
                "SELECT vote_type FROM event_votes WHERE event_id = %s AND user_id = %s",
                (event_id, user_id)
            )
            result = cursor.fetchone()
            return result['vote_type'] if result else None
        except Exception as e:
            print(f"Error in get_user_vote: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def vote(event_id, user_id, vote_type):
        # Add or update a user's vote for an event.
        try:
            if vote_type not in ['upvote', 'downvote']:
                raise ValueError("Invalid vote type. Must be 'upvote' or 'downvote'")

            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if isinstance(user_id, dict) and 'id' in user_id:
                user_id = user_id['id']
            elif not isinstance(user_id, int):
                try:
                    user_id = int(user_id)
                except (ValueError, TypeError):
                    raise ValueError("Invalid user ID")
            
            cursor.execute(
                "SELECT vote_type FROM event_votes WHERE event_id = %s AND user_id = %s",
                (event_id, user_id)
            )
            existing_vote = cursor.fetchone()
            
            if existing_vote:
                if existing_vote[0] == vote_type:
                    cursor.execute(
                        "DELETE FROM event_votes WHERE event_id = %s AND user_id = %s",
                        (event_id, user_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE event_votes SET vote_type = %s WHERE event_id = %s AND user_id = %s",
                        (vote_type, event_id, user_id)
                    )
            else:
                cursor.execute(
                    "INSERT INTO event_votes (event_id, user_id, vote_type) VALUES (%s, %s, %s)",
                    (event_id, user_id, vote_type)
                )
            
            conn.commit()
            
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN vote_type = 'upvote' THEN 1 ELSE 0 END) as upvotes,
                    SUM(CASE WHEN vote_type = 'downvote' THEN 1 ELSE 0 END) as downvotes
                FROM event_votes 
                WHERE event_id = %s
            """, (event_id,))
            
            vote_counts = cursor.fetchone()
            return {
                "message": "Vote recorded successfully",
                "upvotes": vote_counts[0] or 0,
                "downvotes": vote_counts[1] or 0
            }
        except Exception as e:
            conn.rollback()
            print(f"Error in vote: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_comments(event_id):
        # Get all comments for an event.
        db = Database()
        conn = db.get_connection()
        if not conn:
            raise Exception("Could not connect to database")
            
        cursor = conn.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute("""
                SELECT 
                    c.*,
                    u.username as author_name
                FROM event_comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.event_id = %s
                ORDER BY c.created_at DESC
            """, (event_id,))
            
            return {"comments": cursor.fetchall()}
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add_comment(event_id, user_id, content):
        # Add a new comment to an event.
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        if isinstance(user_id, dict) and 'id' in user_id:
            user_id = user_id['id']
        elif not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                raise ValueError("Invalid user ID")

        db = Database()
        conn = db.get_connection()
        if not conn:
            raise Exception("Could not connect to database")
            
        cursor = conn.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(
                """
                INSERT INTO event_comments (event_id, user_id, content, created_at) 
                VALUES (%s, %s, %s, NOW())
                """,
                (event_id, user_id, content.strip())
            )
            
            comment_id = cursor.lastrowid
            
            cursor.execute("""
                SELECT 
                    c.*,
                    u.username as author_name
                FROM event_comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.id = %s
            """, (comment_id,))
            
            comment = cursor.fetchone()
            conn.commit()
            return comment
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close() 
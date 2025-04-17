from flask import json
from requests import request
from models.user_stats import UserStats
from database.connection import Database
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User:
    @staticmethod
    def get_by_id(user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT *
                FROM users
                WHERE id = %s
            """, (user_id,))
            
            return cursor.fetchone()
        except Exception as e:
            print(f"Error in get_by_id: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_email(email):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, username, email, password_hash, exp, created_at
                FROM users
                WHERE email = %s
            """, (email,))
            
            return cursor.fetchone()
        except Exception as e:
            print(f"Error in get_by_email: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def create(username, email, password):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                raise ValueError("Email already registered")
            
            cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                raise ValueError("Username already taken")
            
            password_hash = generate_password_hash(password)
            
            query = """
                INSERT INTO users (
                    username, email, password_hash, exp, created_at
                ) VALUES (%s, %s, %s, 0, NOW())
            """
            
            cursor.execute(query, (username, email, password_hash))
            conn.commit()
            
            return User.get_by_id(cursor.lastrowid)
        except Exception as e:
            conn.rollback()
            print(f"Error in create: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update(user_id, username=None, email=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            updates = []
            params = []
            
            if username is not None:
                cursor.execute("SELECT 1 FROM users WHERE username = %s AND id != %s", (username, user_id))
                if cursor.fetchone():
                    raise ValueError("Username already taken")
                updates.append("username = %s")
                params.append(username)
            
            if email is not None:
                cursor.execute("SELECT 1 FROM users WHERE email = %s AND id != %s", (email, user_id))
                if cursor.fetchone():
                    raise ValueError("Email already registered")
                updates.append("email = %s")
                params.append(email)
            
            if updates:
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
                params.append(user_id)
                
                cursor.execute(query, params)
                conn.commit()
            
            return User.get_by_id(user_id)
        except Exception as e:
            conn.rollback()
            print(f"Error in update: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_password(user_id, current_password, new_password):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user or not check_password_hash(user['password_hash'], current_password):
                raise ValueError("Current password is incorrect")
            
            password_hash = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (password_hash, user_id)
            )
            
            conn.commit()
            return {"message": "Password updated successfully"}
        except Exception as e:
            conn.rollback()
            print(f"Error in update_password: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def verify_password(user, password):
        return check_password_hash(user['password_hash'], password)

    @staticmethod
    def add_exp(user_id, points):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE users SET exp = exp + %s WHERE id = %s",
                (points, user_id)
            )
            
            conn.commit()
            return {"message": f"Added {points} experience points"}
        except Exception as e:
            conn.rollback()
            print(f"Error in add_exp: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_leaderboard(limit=10):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, username, exp, level
                FROM users
                ORDER BY exp DESC
                LIMIT %s
            """, (limit,))
            
            return cursor.fetchall()
        except Exception as e:
            print(f"Error in get_leaderboard: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_profile(user_id):
        """Get user profile information."""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            user_query = """
                SELECT 
                    u.id, 
                    u.username, 
                    u.email, 
                    u.exp, 
                    u.level, 
                    u.created_at,
                    u.last_login,
                    u.role,
                    u.avatar_url,
                    u.bio,
                    (SELECT COUNT(*) FROM user_followers WHERE followed_id = u.id) as followers_count,
                    (SELECT COUNT(*) FROM user_followers WHERE follower_id = u.id) as following_count,
                    (
                        SELECT COUNT(*) 
                        FROM event_participants
                        WHERE user_id = u.id
                    ) as events_joined,
                    (
                        SELECT COUNT(*)
                        FROM events
                        WHERE organizer_id = u.id
                    ) as events_created,
                    (
                        SELECT COUNT(*)
                        FROM user_achievements
                        WHERE user_id = u.id
                    ) as achievements_earned,
                    (
                        SELECT COUNT(*)
                        FROM forum_replies
                        WHERE author_id = u.id
                    ) as forum_posts

                FROM users u
                WHERE u.id = %s
            """
            
            cursor.execute(user_query, (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return {'success': False, 'error': 'User not found'}
            
            group_query = """
                SELECT 
                    g.id, 
                    g.name, 
                    g.image_url, 
                    gm.role,
                    (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
                FROM groups g
                JOIN group_members gm ON g.id = gm.group_id
                WHERE gm.user_id = %s
                LIMIT 1
            """
            
            cursor.execute(group_query, (user_id,))
            group_data = cursor.fetchone()

            
            roles = [user_data.get('role')] if user_data.get('role') else ['user']
            
            return {
                'success': True,
                'user': {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'email': user_data['email'],
                    'exp': user_data['exp'] or 0,
                    'level': user_data['level'] or 1,
                    'created_at': user_data['created_at'].isoformat() if user_data['created_at'] else None,
                    'last_login': user_data['last_login'].isoformat() if user_data['last_login'] else None,
                    'roles': roles,
                    'avatar_url': user_data['avatar_url'],
                    'bio': user_data['bio']
                },
                'stats': {
                    'followers_count': user_data['followers_count'],
                    'following_count': user_data['following_count'],
                    'events_joined': user_data['events_joined'],
                    'events_created': user_data['events_created'],
                    'achievements_earned': user_data['achievements_earned'],
                    'forum_posts': user_data['forum_posts'],
                },
                'group': {
                    'id': group_data['id'],
                    'name': group_data['name'],
                    'image_url': group_data['image_url'],
                    'role': group_data['role'],
                    'member_count': group_data['member_count']
                } if group_data else None,
            }
            
        except Exception as e:
            print(f"Error in get_profile: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_profile(user_id, update_fields):
        # Update user profile fields
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            allowed_fields = {'username'}
            valid_updates = {k: v for k, v in update_fields.items() if k in allowed_fields}
            
            if not valid_updates:
                raise ValueError("No valid fields to update")
            
            # Check username uniqueness if being updated
            if 'username' in valid_updates:
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s AND id != %s",
                    (valid_updates['username'], user_id)
                )
                if cursor.fetchone():
                    raise ValueError("Username is already taken")
            
            # Build and execute update query
            set_clauses = [f"{field} = %s" for field in valid_updates.keys()]
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s"
            values = list(valid_updates.values()) + [user_id]
            
            cursor.execute(query, values)
            conn.commit()
            
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error in update_profile: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def is_following(follower_id: int, followed_id: int) -> bool:
        # Check if one user is following another.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 1 
                FROM user_followers 
                WHERE follower_id = %s AND followed_id = %s
            """, (follower_id, followed_id))
            
            return bool(cursor.fetchone())
            
        except Exception as e:
            print(f"Error in is_following: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def follow_user(follower_id: int, followed_id: int) -> bool:
        # Follow a user.

        if follower_id == followed_id:
            raise ValueError("Cannot follow yourself")
            
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 1 FROM user_followers
                WHERE follower_id = %s AND followed_id = %s
            """, (follower_id, followed_id))
            
            if cursor.fetchone():
                raise ValueError("Already following this user")
                
            cursor.execute("""
                INSERT INTO user_followers (follower_id, followed_id, created_at)
                VALUES (%s, %s, NOW())
            """, (follower_id, followed_id))
            
            try:
                UserStats.update_stat_and_achievements(
                    follower_id,
                    'followers_count',
                    {
                        'name': 'First Following'
                    }
                )
            except Exception as e:
                print(f"Error updating stats and achievements: {str(e)}")
                
            conn.commit()
            return True
            
        except ValueError as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            print(f"Error in follow_user: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()
            
    @staticmethod
    def unfollow_user(follower_id: int, followed_id: int) -> bool:
        # Unfollow a user.

        if follower_id == followed_id:
            raise ValueError("Cannot unfollow yourself")
            
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM user_followers
                WHERE follower_id = %s AND followed_id = %s
            """, (follower_id, followed_id))
            
            if cursor.rowcount == 0:
                raise ValueError("Not following this user")
                
            conn.commit()
            return True
            
        except ValueError as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            print(f"Error in unfollow_user: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_following(user_id: int):
        # Get the list of users that a user is following.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    f.followed_id,
                    u.username,
                    u.avatar_url,
                    f.created_at
                FROM user_followers f
                JOIN users u ON f.followed_id = u.id
                WHERE f.follower_id = %s
                ORDER BY f.created_at DESC
            """, (user_id,))
            
            following = []
            for row in cursor.fetchall():
                following.append({
                    'followed_id': row['followed_id'],
                    'username': row['username'],
                    'avatar_url': row['avatar_url'],
                    'followed_since': row['created_at'].isoformat() if row['created_at'] else None
                })
            
            return {
                'success': True,
                'following': following
            }
            
        except Exception as e:
            print(f"Error in get_following: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def record_login(user_id):
        # Record a user login and update their login stats and achievements.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            ip_address = request.remote_addr if 'request' in globals() else '127.0.0.1'
            
            cursor.execute("""
                INSERT INTO user_logins (user_id, login_time, ip_address)
                VALUES (%s, NOW(), %s)
            """, (user_id, ip_address))
            
            conn.commit()
            
            try:
                from models.user_stats import UserStats
                
                UserStats.update_stat_and_achievements(
                    user_id,
                    'login_count',
                    {
                        'login_time': datetime.now()
                    }
                )
                
                UserStats.update_stat_and_achievements(
                    user_id,
                    'login_streak',
                    {
                        'login_time': datetime.now()
                    }
                )
                
                print(f"Successfully updated login stats for user {user_id}")
            except Exception as e:
                print(f"Error updating login stats: {str(e)}")
            
            return True
        except Exception as e:
            print(f"Error recording login: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close() 
from typing import Optional, Dict, Any
from database.connection import Database
from models.user_stats import UserStats

class Group:
    def __init__(self, id: int = None, name: str = None, description: str = None,
                 creator_id: int = None, image_url: str = None, member_count: int = 0,
                 is_private: bool = False, creator_name: str = None):
        self.id = id
        self.name = name
        self.description = description
        self.creator_id = creator_id
        self.image_url = image_url
        self.member_count = member_count
        self.is_private = is_private
        self.creator_name = creator_name

    @classmethod
    def get_all(cls, page=1, search=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    g.*,
                    u.username as creator_name,
                    COUNT(DISTINCT m.user_id) as member_count
                FROM groups g
                LEFT JOIN users u ON g.creator_id = u.id
                LEFT JOIN group_members m ON g.id = m.group_id
                WHERE 1=1
            """
            params = []
            
            if search:
                query += " AND (g.name LIKE %s OR g.description LIKE %s)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            query += " GROUP BY g.id ORDER BY g.created_at DESC"
            
            limit = 10
            offset = (page - 1) * limit
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            groups = cursor.fetchall()
            
            count_query = """
                SELECT COUNT(DISTINCT g.id) as total
                FROM groups g
                WHERE 1=1
            """
            if search:
                count_query += " AND (g.name LIKE %s OR g.description LIKE %s)"
            
            cursor.execute(count_query, params[:-2] if search else [])  # Exclude LIMIT and OFFSET params
            total = cursor.fetchone()['total']
            
            return {
                'groups': groups,
                'page': page,
                'total': total,
                'total_pages': (total + limit - 1) // limit
            }
        except Exception as e:
            print(f"Error in get_all: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def get_by_id(cls, group_id: int) -> Optional['Group']:
        # Retrieve a group by its ID.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    g.id,
                    g.name,
                    g.description,
                    g.creator_id,
                    g.image_url,
                    g.is_private,
                    u.username as creator_name,
                    COUNT(DISTINCT m.user_id) as member_count
                FROM groups g
                LEFT JOIN users u ON g.creator_id = u.id
                LEFT JOIN group_members m ON g.id = m.group_id
                WHERE g.id = %s
                GROUP BY g.id, g.name, g.description, g.creator_id, g.image_url, g.is_private, u.username
            """, (group_id,))
            
            group_data = cursor.fetchone()
            
            if group_data:
                return cls(**group_data)
            return None
            
        except Exception as e:
            print(f"Error retrieving group: {str(e)}")
            return None
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    @classmethod
    def create(cls, *, creator_id: int, name: str, description: str, is_private: bool = False) -> Optional['Group']:
        # Create a new group in the database.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                INSERT INTO groups (creator_id, name, description, is_private)
                VALUES (%s, %s, %s, %s)
            """, (creator_id, name, description, is_private))
            
            group_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO group_members (group_id, user_id, role)
                VALUES (%s, %s, 'admin')
            """, (group_id, creator_id))
            
            conn.commit()
            
            try:
                UserStats.update_stat_and_achievements(
                    creator_id,
                'group_created',
                {
                    'name': name
                    }
                )
            except Exception as e:
                print(f"Error updating stats and achievements: {str(e)}")
            
            return cls(
                id=group_id,
                name=name,
                description=description,
                creator_id=creator_id,
                is_private=is_private
            )
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            print(f"Error creating group: {str(e)}")
            return None
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def update(group_id, name=None, description=None, is_private=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = %s")
                params.append(name)
            
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            
            if is_private is not None:
                updates.append("is_private = %s")
                params.append(is_private)
            
            if updates:
                query = f"UPDATE groups SET {', '.join(updates)} WHERE id = %s"
                params.append(group_id)
                
                cursor.execute(query, params)
                conn.commit()
            
            return Group.get_by_id(group_id)
        except Exception as e:
            conn.rollback()
            print(f"Error in update: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(group_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM group_members WHERE group_id = %s", (group_id,))
            
            cursor.execute("DELETE FROM groups WHERE id = %s", (group_id,))
            
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
    def get_members(group_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    u.id,
                    u.username,
                    m.role,
                    m.joined_at
                FROM group_members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = %s
                ORDER BY 
                    CASE m.role 
                        WHEN 'admin' THEN 1 
                        WHEN 'moderator' THEN 2 
                        ELSE 3 
                    END,
                    m.joined_at ASC
            """
            
            cursor.execute(query, (group_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error in get_members: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add_member(group_id, user_id, role='member'):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT 1 FROM group_members WHERE group_id = %s AND user_id = %s",
                (group_id, user_id)
            )
            if cursor.fetchone():
                raise ValueError("User is already a member of this group")
            
            cursor.execute("SELECT creator_id, name FROM groups WHERE id = %s", (group_id,))
            group_data = cursor.fetchone()
            if not group_data:
                raise ValueError("Group not found")
                
            creator_id = group_data['creator_id']
            
            cursor.execute(
                """
                INSERT INTO group_members (
                    group_id, user_id, role, joined_at
                ) VALUES (%s, %s, %s, NOW())
                """,
                (group_id, user_id, role)
            )
            
            conn.commit()
            
            UserStats.update_stat_and_achievements(
                user_id,
                'group_member_added',
                {
                    'name': group_data['name']
                }
            )
            return {"message": "Successfully joined group"}
        except Exception as e:
            conn.rollback()
            print(f"Error in add_member: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def remove_member(group_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT creator_id FROM groups WHERE id = %s", (group_id,))
            group_data = cursor.fetchone()
            if not group_data:
                raise ValueError("Group not found")
                
            creator_id = group_data['creator_id']
            
            cursor.execute(
                "DELETE FROM group_members WHERE group_id = %s AND user_id = %s",
                (group_id, user_id)
            )
            
            conn.commit()
            
            UserStats.update_stat_and_achievements(
                creator_id,
                'group_member_removed',
                {
                    'name': group_data['name']
                }
            )
            return {"message": "Successfully left group"}
        except Exception as e:
            conn.rollback()
            print(f"Error in remove_member: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_member_role(group_id, user_id, new_role):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE group_members 
                SET role = %s
                WHERE group_id = %s AND user_id = %s
                """,
                (new_role, group_id, user_id)
            )
            
            conn.commit()
            return {"message": f"Successfully updated member role to {new_role}"}
        except Exception as e:
            conn.rollback()
            print(f"Error in update_member_role: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_user_id(user_id: int) -> Optional[Dict[str, Any]]:
        # Get a user's group information.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    g.*,
                    u.username as creator_name,
                    COUNT(DISTINCT m.user_id) as member_count
                FROM groups g
                LEFT JOIN users u ON g.creator_id = u.id
                LEFT JOIN group_members m ON g.id = m.group_id
                WHERE g.id = (SELECT group_id FROM users WHERE id = %s)
                GROUP BY g.id
            """, (user_id,))
            
            return cursor.fetchone()
            
        except Exception as e:
            print(f"Error in get_by_user_id: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def is_admin(group_id, user_id):
        # Check if a user is an admin of a group.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 1 
                FROM group_members 
                WHERE group_id = %s AND user_id = %s AND role = 'admin'
            """, (group_id, user_id))
            
            result = cursor.fetchone()
            return bool(result)
        except Exception as e:
            print(f"Error in is_admin: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    def to_dict(self) -> Dict[str, Any]:
        # Convert the group object to a dictionary.

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'creator_id': self.creator_id,
            'creator_name': self.creator_name,
            'image_url': self.image_url,
            'member_count': self.member_count,
            'is_private': self.is_private
        }
        
    @staticmethod
    def join_group(user_id, group_id):
        # Add a user to a group if they're not already a member of any group.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT g.name 
                FROM group_members gm
                JOIN groups g ON g.id = gm.group_id
                WHERE gm.user_id = %s
            """, (user_id,))
            
            existing_group = cursor.fetchone()
            if existing_group:
                raise ValueError(f'You are already a member of the group: {existing_group[0]}. You can only be a member of one group at a time.')

            cursor.execute("""
                INSERT INTO group_members (group_id, user_id, role)
                VALUES (%s, %s, 'member')
            """, (group_id, user_id))
            
            conn.commit()
            return {'success': True, 'message': 'Successfully joined group'}
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def get_user_membership(group_id, user_id):
        # Check if a user is a member of a group and get their role.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT role FROM group_members WHERE group_id = %s AND user_id = %s",
                (group_id, user_id)
            )
            
            member = cursor.fetchone()
            return {
                'is_member': bool(member),
                'role': member[0] if member else None
            }
            
        except Exception as e:
            print(f"Error checking user membership: {str(e)}")
            return {'is_member': False, 'role': None}
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def get_group_posts(group_id):
        # Get all posts for a group.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    p.*,
                    u.username as author_name,
                    COUNT(DISTINCT c.id) as comments_count
                FROM group_posts p
                LEFT JOIN users u ON p.author_id = u.id
                LEFT JOIN group_comments c ON p.id = c.group_post_id
                WHERE p.group_id = %s
                GROUP BY p.id
                ORDER BY p.created_at DESC
            """, (group_id,))

            posts = cursor.fetchall()
            return posts
            
        except Exception as e:
            print(f"Error getting group posts: {str(e)}")
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def create_group_post(group_id, author_id, content, image_url=None):
        # Create a new post in a group.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                INSERT INTO group_posts (
                    group_id, author_id, content, image_url
                ) VALUES (%s, %s, %s, %s)
            """, (
                group_id,
                author_id,
                content,
                image_url
            ))

            post_id = cursor.lastrowid
            conn.commit()

            cursor.execute("""
                SELECT 
                    p.*,
                    u.username as author_name,
                    0 as comments_count
                FROM group_posts p
                LEFT JOIN users u ON p.author_id = u.id
                WHERE p.id = %s
            """, (post_id,))

            post = cursor.fetchone()
            return post
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            print(f"Error creating group post: {str(e)}")
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def update_group_post(post_id, group_id, author_id, content, image_url=None):
        # Update an existing group post.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 1 FROM group_posts p
                WHERE p.id = %s AND p.group_id = %s AND p.author_id = %s
            """, (post_id, group_id, author_id))

            if not cursor.fetchone():
                raise ValueError("Unauthorized to edit this post")

            cursor.execute("""
                UPDATE group_posts 
                SET content = %s, image_url = %s
                WHERE id = %s
            """, (content, image_url, post_id))

            conn.commit()

            cursor.execute("""
                SELECT 
                    p.*,
                    u.username as author_name,
                    COUNT(DISTINCT c.id) as comments_count
                FROM group_posts p
                LEFT JOIN users u ON p.author_id = u.id
                LEFT JOIN group_comments c ON p.id = c.group_post_id
                WHERE p.id = %s
                GROUP BY p.id
            """, (post_id,))

            post = cursor.fetchone()
            return post
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            print(f"Error updating group post: {str(e)}")
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def delete_group_post(post_id, group_id, user_id):
        # Delete a group post if the user is the author or a group admin.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 1 FROM group_posts p
                WHERE p.id = %s AND p.group_id = %s AND (
                    p.author_id = %s OR 
                    EXISTS (
                        SELECT 1 FROM group_members 
                        WHERE group_id = %s AND user_id = %s AND role = 'admin'
                    )
                )
            """, (post_id, group_id, user_id, group_id, user_id))

            if not cursor.fetchone():
                raise ValueError("Unauthorized to delete this post")

            cursor.execute("DELETE FROM group_posts WHERE id = %s", (post_id,))
            conn.commit()
            
            return True
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            print(f"Error deleting group post: {str(e)}")
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def is_group_member(group_id, user_id):
        # Check if a user is a member of a group.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 FROM group_members WHERE group_id = %s AND user_id = %s",
                (group_id, user_id)
            )
            
            is_member = cursor.fetchone() is not None
            return is_member
            
        except Exception as e:
            print(f"Error checking group membership: {str(e)}")
            return False
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def get_post_comments(post_id):
        # Get all comments for a group post.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    c.*,
                    u.username as author_name
                FROM group_comments c
                LEFT JOIN users u ON c.author_id = u.id
                WHERE c.group_post_id = %s
                ORDER BY c.created_at DESC
            """, (post_id,))

            comments = cursor.fetchall()
            return comments
            
        except Exception as e:
            print(f"Error getting post comments: {str(e)}")
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def create_post_comment(post_id, author_id, content):
        # Create a new comment on a group post.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            # Create comment
            cursor.execute("""
                INSERT INTO group_comments (
                    group_post_id, author_id, content
                ) VALUES (%s, %s, %s)
            """, (post_id, author_id, content))

            comment_id = cursor.lastrowid
            conn.commit()

            # Get the created comment
            cursor.execute("""
                SELECT 
                    c.*,
                    u.username as author_name
                FROM group_comments c
                LEFT JOIN users u ON c.author_id = u.id
                WHERE c.id = %s
            """, (comment_id,))

            comment = cursor.fetchone()
            return comment
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            print(f"Error creating post comment: {str(e)}")
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def delete_post_comment(comment_id, post_id, group_id, user_id):
        # Delete a comment if the user is the author or a group admin.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 1 FROM group_comments c
                WHERE c.id = %s AND c.group_post_id = %s AND (
                    c.author_id = %s OR 
                    EXISTS (
                        SELECT 1 FROM group_members 
                        WHERE group_id = %s AND user_id = %s AND role = 'admin'
                    )
                )
            """, (comment_id, post_id, user_id, group_id, user_id))

            if not cursor.fetchone():
                raise ValueError("Unauthorized to delete this comment")

            cursor.execute("DELETE FROM group_comments WHERE id = %s", (comment_id,))
            conn.commit()
            
            return True
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            print(f"Error deleting post comment: {str(e)}")
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def get_chat_messages(group_id):
        # Get chat messages for a group.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    m.*,
                    u.username as author_name
                FROM group_chat_messages m
                LEFT JOIN users u ON m.author_id = u.id
                WHERE m.group_id = %s
                ORDER BY m.created_at DESC
                LIMIT 50
            """, (group_id,))

            messages = cursor.fetchall()
            return messages
            
        except Exception as e:
            print(f"Error getting chat messages: {str(e)}")
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def create_chat_message(group_id, author_id, content):
        # Create a new chat message in a group.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                INSERT INTO group_chat_messages (
                    group_id, author_id, content
                ) VALUES (%s, %s, %s)
            """, (group_id, author_id, content))

            message_id = cursor.lastrowid
            conn.commit()

            cursor.execute("""
                SELECT 
                    m.*,
                    u.username as author_name
                FROM group_chat_messages m
                LEFT JOIN users u ON m.author_id = u.id
                WHERE m.id = %s
            """, (message_id,))

            message = cursor.fetchone()
            return message
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            print(f"Error creating chat message: {str(e)}")
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    @staticmethod
    def delete_chat_message(message_id, group_id, user_id):
        # Delete a chat message if the user is the author or a group admin.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 1 FROM group_chat_messages m
                WHERE m.id = %s AND m.group_id = %s AND (
                    m.author_id = %s OR 
                    EXISTS (
                        SELECT 1 FROM group_members 
                        WHERE group_id = %s AND user_id = %s AND role = 'admin'
                    )
                )
            """, (message_id, group_id, user_id, group_id, user_id))

            if not cursor.fetchone():
                raise ValueError("Unauthorized to delete this message")

            cursor.execute("DELETE FROM group_chat_messages WHERE id = %s", (message_id,))
            conn.commit()
            
            return True
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            print(f"Error deleting chat message: {str(e)}")
            raise e
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def get_user_memberships(user_id):
        # Get all groups that a user is a member of.

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    g.*,
                    u.username as creator_name,
                    gm.role,
                    COUNT(DISTINCT m.user_id) as member_count
                FROM groups g
                JOIN group_members gm ON g.id = gm.group_id AND gm.user_id = %s
                LEFT JOIN users u ON g.creator_id = u.id
                LEFT JOIN group_members m ON g.id = m.group_id
                GROUP BY g.id, gm.role
                ORDER BY g.name
            """, (user_id,))

            groups = cursor.fetchall()
            return groups
            
        except Exception as e:
            print(f"Error getting user group memberships: {str(e)}")
            return []
            
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close() 
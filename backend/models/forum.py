from database.connection import Database
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

class Forum:
    def __init__(self):
        self.db = Database()

    def create_discussion(self, title: str, content: str, author_id: int, 
                        category_id: int, excerpt: Optional[str] = None) -> Tuple[bool, str]:
        connection = self.db.get_connection()
        if not connection:
            return False, "Database connection error"

        try:
            cursor = connection.cursor()
            
            if not excerpt:
                excerpt = content[:200] + "..." if len(content) > 200 else content

            cursor.execute("""
                INSERT INTO forum_discussions 
                (title, content, excerpt, author_id, category_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, content, excerpt, author_id, category_id))
            
            connection.commit()
            
            try:
                from models.user_stats import UserStats
                UserStats.update_stat_and_achievements(
                    author_id,
                    'forum_discussions',
                    {
                        'discussion_title': title
                    }
                )
            except Exception as e:
                print(f"Error updating stats: {str(e)}")
            
            return True, str(cursor.lastrowid)
        except Exception as e:
            return False, str(e)
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_discussions(page=1, category=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    d.*,
                    c.name as category_name,
                    u.username as author_name,
                    COUNT(DISTINCT l.user_id) as likes_count,
                    COUNT(DISTINCT r.id) as replies_count,
                    EXISTS(SELECT 1 FROM forum_replies r2 WHERE r2.discussion_id = d.id AND r2.is_solution = TRUE) as has_solution
                FROM forum_discussions d
                LEFT JOIN forum_categories c ON d.category_id = c.id
                LEFT JOIN users u ON d.author_id = u.id
                LEFT JOIN forum_likes l ON d.id = l.discussion_id
                LEFT JOIN forum_replies r ON d.id = r.discussion_id
                WHERE 1=1
            """
            params = []
            
            if category and category != 'all':
                query += " AND c.name = %s"
                params.append(category)
            
            query += " GROUP BY d.id ORDER BY d.created_at DESC"
            
            limit = 10
            offset = (page - 1) * limit
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            discussions = cursor.fetchall()
            
            count_query = """
                SELECT COUNT(DISTINCT d.id) as total
                FROM forum_discussions d
                LEFT JOIN forum_categories c ON d.category_id = c.id
                WHERE 1=1
            """
            if category and category != 'all':
                count_query += " AND c.name = %s"
            
            cursor.execute(count_query, params[:-2] if category and category != 'all' else [])
            total = cursor.fetchone()['total']
            
            return {
                'discussions': discussions,
                'page': page,
                'total': total,
                'total_pages': (total + limit - 1) // limit
            }
        except Exception as e:
            print(f"Error in get_discussions: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_discussion_by_id(discussion_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    d.*,
                    c.name as category_name,
                    u.username as author_name, 
                    u.avatar_url as author_avatar_url,
                    COUNT(DISTINCT l.user_id) as likes_count,
                    COUNT(DISTINCT r.id) as replies_count,
                    EXISTS(SELECT 1 FROM forum_replies r2 WHERE r2.discussion_id = d.id AND r2.is_solution = TRUE) as has_solution
                FROM forum_discussions d
                LEFT JOIN forum_categories c ON d.category_id = c.id
                LEFT JOIN users u ON d.author_id = u.id
                LEFT JOIN forum_likes l ON d.id = l.discussion_id
                LEFT JOIN forum_replies r ON d.id = r.discussion_id
                WHERE d.id = %s
                GROUP BY d.id, d.category_id, c.name, u.username
            """
            
            cursor.execute(query, (discussion_id,))
            discussion = cursor.fetchone()
            
            return discussion
        except Exception as e:
            print(f"Error in get_discussion_by_id: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def increment_discussion_view(discussion_id):
        # Increment the view count for a discussion

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT id FROM forum_discussions WHERE id = %s",
                (discussion_id,)
            )
            
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": "Discussion not found"
                }
            
            cursor.execute(
                "UPDATE forum_discussions SET views_count = views_count + 1 WHERE id = %s",
                (discussion_id,)
            )
            conn.commit()
            
            cursor.execute(
                "SELECT views_count FROM forum_discussions WHERE id = %s",
                (discussion_id,)
            )
            result = cursor.fetchone()
            
            return {
                "success": True,
                "views_count": result['views_count']
            }
        except Exception as e:
            print(f"Error incrementing discussion view: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def create_discussion(author_id, title, content, category, excerpt):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT id FROM forum_categories WHERE name = %s", (category,))
            category_result = cursor.fetchone()
            if not category_result:
                raise ValueError(f"Category '{category}' not found")
            
            query = """
                INSERT INTO forum_discussions (
                    author_id, category_id, title, content, excerpt,
                    views_count, created_at
                ) VALUES (%s, %s, %s, %s, %s, 0, NOW())
            """
            
            cursor.execute(query, (
                author_id, category_result['id'], title, content, excerpt
            ))
            
            conn.commit()
            discussion_id = cursor.lastrowid
            
            try:
                from models.user_stats import UserStats
                UserStats.update_stat_and_achievements(
                    author_id,
                    'forum_discussions',
                    {
                        'discussion_id': discussion_id,
                        'discussion_title': title
                    }
                )
            except Exception as e:
                print(f"Error updating stats: {str(e)}")
            
            return Forum.get_discussion_by_id(discussion_id)
        except Exception as e:
            conn.rollback()
            print(f"Error in create_discussion: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_discussion(discussion_id, author_id, title=None, content=None, category=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT author_id FROM forum_discussions WHERE id = %s",
                (discussion_id,)
            )
            discussion = cursor.fetchone()
            if not discussion or discussion['author_id'] != author_id:
                raise ValueError("Unauthorized to update this discussion")
            
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            
            if content is not None:
                updates.append("content = %s")
                excerpt = content[:200] + '...' if len(content) > 200 else content
                updates.append("excerpt = %s")
                params.extend([content, excerpt])
            
            if category is not None:
                cursor.execute("SELECT id FROM forum_categories WHERE name = %s", (category,))
                category_result = cursor.fetchone()
                if not category_result:
                    raise ValueError(f"Category '{category}' not found")
                updates.append("category_id = %s")
                params.append(category_result['id'])
            
            if updates:
                query = f"UPDATE forum_discussions SET {', '.join(updates)} WHERE id = %s"
                params.append(discussion_id)
                
                cursor.execute(query, params)
                conn.commit()
            
            return Forum.get_discussion_by_id(discussion_id)
        except Exception as e:
            conn.rollback()
            print(f"Error in update_discussion: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete_discussion(discussion_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT author_id FROM forum_discussions WHERE id = %s",
                (discussion_id,)
            )
            discussion = cursor.fetchone()
            if not discussion or discussion['author_id'] != user_id:
                raise ValueError("Unauthorized to delete this discussion")
            
            cursor.execute("DELETE FROM forum_likes WHERE discussion_id = %s", (discussion_id,))
            cursor.execute("DELETE FROM forum_replies WHERE discussion_id = %s", (discussion_id,))
            
            cursor.execute("DELETE FROM forum_discussions WHERE id = %s", (discussion_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error in delete_discussion: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_replies(discussion_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    r.*,
                    u.username as author_name,
                    u.avatar_url as author_avatar_url,
                    COUNT(DISTINCT l.user_id) as likes_count
                FROM forum_replies r
                LEFT JOIN users u ON r.author_id = u.id
                LEFT JOIN forum_likes l ON r.id = l.reply_id
                WHERE r.discussion_id = %s
                GROUP BY r.id
                ORDER BY r.is_solution DESC, r.created_at ASC
            """
            
            cursor.execute(query, (discussion_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error in get_replies: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def create_reply(discussion_id, author_id, content):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT title FROM forum_discussions
                WHERE id = %s
            """, (discussion_id,))
            
            discussion = cursor.fetchone()
            if not discussion:
                raise ValueError(f"Discussion with ID {discussion_id} not found")
            
            query = """
                INSERT INTO forum_replies (
                    discussion_id, author_id, content, created_at
                ) VALUES (%s, %s, %s, NOW())
            """
            
            cursor.execute(query, (
                discussion_id, author_id, content
            ))
            
            conn.commit()
            reply_id = cursor.lastrowid
            
            cursor.execute("""
                UPDATE forum_discussions
                SET replies_count = replies_count + 1
                WHERE id = %s
            """, (discussion_id,))
            
            conn.commit()
            
            try:
                from models.user_stats import UserStats
                UserStats.update_stat_and_achievements(
                    author_id,
                    'forum_replies',
                    {
                        'discussion_title': discussion['title']
                    }
                )
            except Exception as e:
                print(f"Error updating stats: {str(e)}")
            
            cursor.execute("""
                SELECT r.*, u.username as author_name
                FROM forum_replies r
                JOIN users u ON r.author_id = u.id
                WHERE r.id = %s
            """, (reply_id,))
            
            return cursor.fetchone()
        except Exception as e:
            conn.rollback()
            print(f"Error in create_reply: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def mark_solution(reply_id, discussion_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT author_id, title FROM forum_discussions WHERE id = %s",
                (discussion_id,)
            )
            discussion = cursor.fetchone()
            if not discussion or discussion['author_id'] != user_id:
                raise ValueError("Only the discussion author can mark a solution")
            
            cursor.execute(
                "SELECT author_id FROM forum_replies WHERE id = %s",
                (reply_id,)
            )
            reply = cursor.fetchone()
            if not reply:
                raise ValueError(f"Reply with ID {reply_id} not found")
            
            cursor.execute(
                "UPDATE forum_replies SET is_solution = TRUE WHERE id = %s AND discussion_id = %s",
                (reply_id, discussion_id)
            )
            
            cursor.execute(
                "UPDATE forum_discussions SET has_solution = TRUE WHERE id = %s",
                (discussion_id,)
            )
                        
            try:
                from models.user_stats import UserStats
                if reply['author_id'] != user_id:  
                    UserStats.update_stat_and_achievements(
                        reply['author_id'],
                        'forum_solutions',
                        {
                            'discussion_title': discussion['title']
                        }
                    )
            except Exception as e:
                print(f"Error updating stats: {str(e)}")
            
            return {"message": "Reply marked as solution"}
        except Exception as e:
            conn.rollback()
            print(f"Error in mark_solution: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def like_discussion(discussion_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT title, author_id FROM forum_discussions
                WHERE id = %s
            """, (discussion_id,))
            
            discussion = cursor.fetchone()
            if not discussion:
                raise ValueError(f"Discussion with ID {discussion_id} not found")
            
            cursor.execute(
                """
                INSERT INTO forum_likes (discussion_id, user_id, created_at)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE created_at = NOW()
                """,
                (discussion_id, user_id)
            )
            
            conn.commit()
            
            try:
                from models.user_stats import UserStats
                if discussion['author_id'] != user_id:  
                    UserStats.update_stat_and_achievements(
                        user_id,
                        'forum_likes',
                        {
                            'discussion_title': discussion['title']
                        }
                    )
            except Exception as e:
                print(f"Error updating stats: {str(e)}")
            
            return {"message": "Discussion liked successfully"}
        except Exception as e:
            conn.rollback()
            print(f"Error in like_discussion: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def unlike_discussion(discussion_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM forum_likes WHERE discussion_id = %s AND user_id = %s",
                (discussion_id, user_id)
            )
            
            conn.commit()
            return {"message": "Discussion unliked successfully"}
        except Exception as e:
            conn.rollback()
            print(f"Error in unlike_discussion: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def like_reply(reply_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT r.author_id, r.discussion_id, d.title
                FROM forum_replies r
                JOIN forum_discussions d ON r.discussion_id = d.id
                WHERE r.id = %s
            """, (reply_id,))
            
            reply = cursor.fetchone()
            if not reply:
                raise ValueError(f"Reply with ID {reply_id} not found")
            
            cursor.execute(
                """
                INSERT INTO forum_likes (reply_id, user_id, created_at)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE created_at = NOW()
                """,
                (reply_id, user_id)
            )
            
            conn.commit()
            
            try:
                from models.user_stats import UserStats
                if reply['author_id'] != user_id:  
                    UserStats.update_stat_and_achievements(
                        user_id,
                        'forum_likes',
                        {
                            'reply_id': reply_id,
                        }
                    )
            except Exception as e:
                print(f"Error updating stats: {str(e)}")
                # Don't fail if stats update fails
            
            return {"message": "Reply liked successfully"}
        except Exception as e:
            conn.rollback()
            print(f"Error in like_reply: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def unlike_reply(reply_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM forum_likes WHERE reply_id = %s AND user_id = %s",
                (reply_id, user_id)
            )
            
            conn.commit()
            return {"message": "Reply unliked successfully"}
        except Exception as e:
            conn.rollback()
            print(f"Error in unlike_reply: {str(e)}")
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
            
            cursor.execute("""
                SELECT * FROM forum_categories
                ORDER BY name
            """)
            
            categories = cursor.fetchall()
            return categories
        except Exception as e:
            print(f"Error in get_categories: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_top_contributors(limit=10):
        """
        Get top contributors based on likes received on their replies.
        
        Args:
            limit (int): Maximum number of contributors to return
            
        Returns:
            List of top contributors with their like counts
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    u.id,
                    u.username,
                    u.avatar_url as avatar,
                    COUNT(fl.id) as likes_count
                FROM 
                    users u
                JOIN 
                    forum_replies fr ON u.id = fr.author_id
                JOIN 
                    forum_likes fl ON fr.id = fl.reply_id
                GROUP BY 
                    u.id, u.username
                ORDER BY 
                    likes_count DESC
                LIMIT %s
            """, (limit,))
            
            contributors = cursor.fetchall()
            print("cac ", contributors)
            return contributors
        except Exception as e:
            print(f"Error in get_top_contributors: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_category_experts(category_id, limit=5):
        # Get top experts in a category based on the number of likes they received on their replies
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    r.author_id,
                    u.username as author_name,
                    u.avatar_url as author_avatar_url,
                    COUNT(DISTINCT l.id) as likes_count
                FROM 
                    forum_replies r
                JOIN 
                    forum_discussions d ON r.discussion_id = d.id
                JOIN 
                    users u ON r.author_id = u.id
                LEFT JOIN 
                    forum_likes l ON l.reply_id = r.id
                WHERE 
                    d.category_id = %s
                GROUP BY 
                    r.author_id, u.username
                ORDER BY 
                    likes_count DESC
                LIMIT %s
            """
            
            cursor.execute(query, (category_id, limit))
            experts = cursor.fetchall()
            
            return experts
        except Exception as e:
            print(f"Error getting category experts: {e}")
            return []
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    @staticmethod
    def get_related_discussions(discussion_id, limit=5):
    
        # Get discussions related to the specified discussion based on category and popularity.

        
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT title, category_id FROM forum_discussions WHERE id = %s",
                (discussion_id,)
            )
            source = cursor.fetchone()
            
            if not source:
                return {
                    "success": False,
                    "error": "Source discussion not found"
                }
            
            category_related_query = """
                SELECT 
                    d.id,
                    d.title,
                    d.excerpt,
                    d.created_at,
                    d.views_count as view_count,
                    u.username,
                    c.name as category_name,
                    COUNT(DISTINCT l.id) as like_count,
                    COUNT(DISTINCT r.id) as reply_count,
                    'same_category' as relation_type
                FROM forum_discussions d
                LEFT JOIN forum_categories c ON d.category_id = c.id
                LEFT JOIN users u ON d.author_id = u.id
                LEFT JOIN forum_likes l ON d.id = l.discussion_id AND l.reply_id IS NULL
                LEFT JOIN forum_replies r ON d.id = r.discussion_id
                WHERE d.id != %s AND d.category_id = %s
                GROUP BY d.id, d.title, d.excerpt, d.created_at, d.views_count, u.username, c.name
                ORDER BY d.created_at DESC
                LIMIT %s
            """
            
            cursor.execute(category_related_query, (discussion_id, source['category_id'], limit))
            category_related = cursor.fetchall()
            
            remaining = limit - len(category_related)
            
            if remaining > 0:
                exclude_ids = [discussion_id] + [d['id'] for d in category_related]
                placeholder = ', '.join(['%s'] * len(exclude_ids))
                
                popular_query = f"""
                    SELECT 
                        d.id,
                        d.title,
                        d.excerpt,
                        d.created_at,
                        d.views_count as view_count,
                        u.username,
                        c.name as category_name,
                        COUNT(DISTINCT l.id) as like_count,
                        COUNT(DISTINCT r.id) as reply_count,
                        'popular' as relation_type
                    FROM forum_discussions d
                    LEFT JOIN forum_categories c ON d.category_id = c.id
                    LEFT JOIN users u ON d.author_id = u.id
                    LEFT JOIN forum_likes l ON d.id = l.discussion_id AND l.reply_id IS NULL
                    LEFT JOIN forum_replies r ON d.id = r.discussion_id
                    WHERE d.id NOT IN ({placeholder})
                    GROUP BY d.id, d.title, d.excerpt, d.created_at, d.views_count, u.username, c.name
                    ORDER BY (d.likes_count + d.views_count) DESC, d.created_at DESC
                    LIMIT %s
                """
                
                cursor.execute(popular_query, exclude_ids + [remaining])
                popular_related = cursor.fetchall()
                
                related_discussions = category_related + popular_related
            else:
                related_discussions = category_related
            
            return {
                "success": True,
                "discussions": related_discussions
            }
            
        except Exception as e:
            print(f"Error in get_related_discussions: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
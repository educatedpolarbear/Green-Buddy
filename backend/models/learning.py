from datetime import datetime
from database.connection import Database
from models.auth import get_current_user
from flask import abort
from mysql.connector import Error as MySQLError

class LearningResource:
    @staticmethod
    def get_all(category=None, type=None, search=None):
        # Get all learning resources with optional filters.

        db = Database()
        conn = db.get_connection()
        if not conn:
            print("Failed to establish database connection")
            return {
                "success": False,
                "error": "Failed to establish database connection"
            }
            
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT lm.*, u.username as author_name, u.avatar_url as author_avatar_url, u.bio as author_bio, lc.title as category_title,
                    (SELECT COUNT(*) FROM learning_material_likes WHERE material_id = lm.id) as likes_count
                FROM learning_materials lm
                LEFT JOIN users u ON lm.author_id = u.id
                LEFT JOIN learning_categories lc ON lm.category_id = lc.id
                WHERE 1=1
            """
            params = []
            
            if category:
                query += " AND lm.category_id = %s"
                params.append(category)
            if type:
                query += " AND lm.type = %s"
                params.append(type)
            if search:
                query += " AND (lm.title LIKE %s OR lm.content LIKE %s OR lm.excerpt LIKE %s)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
            
            cursor.execute(query, params)
            resources = cursor.fetchall() or []
            
            current_user = get_current_user()
            if current_user:
                for resource in resources:
                    try:
                        cursor.execute(
                            "SELECT 1 FROM learning_material_likes WHERE material_id = %s AND user_id = %s",
                            (resource['id'], current_user['id'])
                        )
                        resource['is_liked'] = bool(cursor.fetchone())
                    except MySQLError as e:
                        print(f"Error fetching user data: {e}")
                        resource['is_liked'] = False
                        
            
            materials = []
            for resource in resources:
                material = {
                    'id': resource['id'],
                    'title': resource['title'],
                    'excerpt': resource['excerpt'] or '',
                    'category_title': resource.get('category_title', ''),
                    'type': resource['type'],
                    'duration': resource.get('duration', ''),
                    'thumbnail_url': resource.get('thumbnail_url'),
                    'views_count': resource.get('views_count', 0),
                    'likes_count': resource.get('likes_count', 0),
                    'author_id': resource['author_id'],
                    'author_name': resource.get('author_name', ''),
                    'author_avatar_url': resource.get('author_avatar_url', ''),
                    'status': resource.get('status', 'published'),
                    'is_liked': resource.get('is_liked', False),
                    'author_bio': resource.get('author_bio', '')
                }
                materials.append(material)
                
            return {
                "success": True,
                "data": {
                    "materials": materials
                }
            }
            
        except MySQLError as e:
            print(f"Database error in get_all: {e}")
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
    def get_by_id(resource_id):
        # Get a learning material by ID.

        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        try:
            cursor.execute("""
                SELECT lm.*, u.username as author_name, u.avatar_url as author_avatar_url, u.bio as author_bio, lc.title as category_title,
                    (SELECT COUNT(*) FROM learning_material_likes WHERE material_id = lm.id) as likes_count,
                    (SELECT COUNT(*) FROM learning_material_comments WHERE material_id = lm.id) as comments_count
                FROM learning_materials lm
                LEFT JOIN users u ON lm.author_id = u.id
                LEFT JOIN learning_categories lc ON lm.category_id = lc.id
                WHERE lm.id = %s
            """, (resource_id,))
            
            resource = cursor.fetchone()
            
            if not resource:
                return {
                    "success": False,
                    "error": "Material not found"
                }
                
            current_user = get_current_user()
            if current_user:
                cursor.execute(
                    "SELECT 1 FROM learning_material_likes WHERE material_id = %s AND user_id = %s",
                    (resource_id, current_user['id'])
                )
                
                resource['is_liked'] = bool(cursor.fetchone())
                        
            material = {
                'id': resource['id'],
                'title': resource['title'],
                'content': resource['content'],
                'excerpt': resource['excerpt'] or '',
                'category_id': resource['category_id'],
                'category_title': resource.get('category_title', ''),
                'type': resource['type'],
                'duration': resource.get('duration', ''),
                'thumbnail_url': resource.get('thumbnail_url'),
                'views_count': resource.get('views_count', 0),
                'likes_count': resource.get('likes_count', 0),
                'author_id': resource['author_id'],
                'author_name': resource.get('author_name', ''),
                'author_avatar_url': resource.get('author_avatar_url', ''),
                'status': resource.get('status', 'published'),
                'is_liked': resource.get('is_liked', False),
                'created_at': resource.get('created_at'),
                'updated_at': resource.get('updated_at'),
                'author_bio': resource.get('author_bio', ''),
                'comments_count': resource.get('comments_count', 0)
            }     
            
            return {
                "success": True,
                "data": {
                    "material": material
                }
            }
               
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_completed_count(user_id: int) -> dict:
        # Get the count of learning materials viewed by a user.

        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM learning_material_progress
                WHERE user_id = %s AND completion_type = 'completion'
            """, (user_id,))
            
            result = cursor.fetchone()
            return {
                "success": True,
                "data": {
                    "count": result['count'] if result else 0
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def record_view(user_id: int, material_id: int) -> dict:
        # Record that a user viewed a learning material.
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            
            cursor.execute("""
                INSERT INTO learning_material_progress (user_id, material_id, completion_type, completed_at)
                VALUES (%s, %s, 'view', CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE completed_at = CURRENT_TIMESTAMP
            """, (user_id, material_id))
            
            conn.commit()
            
            cursor.execute("""
                SELECT title FROM learning_materials WHERE id = %s
            """, (material_id,))
            
            material_title = cursor.fetchone()['title']
                
            try:
                from models.user_stats import UserStats
                UserStats.update_stat_and_achievements(
                    user_id, 
                    'materials_read',
                    {
                        'material_title': material_title
                    }
                )
            except Exception as e:
                print(f"Error updating stats: {str(e)}")
                
            return {"success": True, "message": "View recorded successfully"}
            
        except Exception as e:
            conn.rollback()
            print(f"Error recording view: {e}")
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"Error type: {error_type}, Message: {error_msg}")
            return {"success": False, "error": f"{error_type}: {error_msg}"}
        finally:
            if cursor:
                cursor.close()
                conn.close()


    @staticmethod
    def record_completion(user_id: int, material_id: int) -> dict:
        # Record that a user completed reading a learning material (scrolled to bottom).

        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            
            cursor.execute("""
                INSERT INTO learning_material_progress (user_id, material_id, completion_type, completed_at)
                VALUES (%s, %s, 'completion', CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE completed_at = CURRENT_TIMESTAMP
            """, (user_id, material_id))
        
            conn.commit()
            
            cursor.execute("""
                SELECT title FROM learning_materials WHERE id = %s
            """, (material_id,))
            
            material_title = cursor.fetchone()['title']
            
            try:
                from models.user_stats import UserStats
                UserStats.update_stat_and_achievements(
                    user_id, 
                    'learning_completed',
                    {
                        'material_title': material_title
                    }
                )
            except Exception as e:
                print(f"Error updating stats: {str(e)}")
                
            return {"success": True, "message": "Completion recorded successfully"}
        
        
            
        except Exception as e:
            
            conn.rollback()
            
            print(f"Error recording completion: {e}")
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"Error type: {error_type}, Message: {error_msg}")
            return {"success": False, "error": f"{error_type}: {error_msg}"}
        finally:
            if cursor:
                cursor.close()
                conn.close()
                
    @staticmethod
    def increment_views(post_id):
        # Increment the views count for a learning material.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE learning_materials SET views_count = COALESCE(views_count, 0) + 1 WHERE id = %s",
                (post_id,)
            )
            
            conn.commit()
            return {
                "success": True,
                "data": {
                    "message": "Views count incremented successfully"
                }
            }
        except Exception as e:
            print(f"Error incrementing views: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()
            
    @staticmethod
    def toggle_like(material_id: int, user_id: int) -> dict:
        # Toggle like status for a learning material and return updated status.
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            material_result = LearningResource.get_by_id(material_id)
            if not material_result['success']:
                return material_result
            
            cursor.execute("""
                SELECT id FROM learning_material_likes
                WHERE material_id = %s AND user_id = %s
            """, (material_id, user_id))
            
            existing_like = cursor.fetchone()
            
            if existing_like:
                cursor.execute("""
                    DELETE FROM learning_material_likes
                    WHERE material_id = %s AND user_id = %s
                """, (material_id, user_id))
                liked = False
            else:
                cursor.execute("""
                    INSERT INTO learning_material_likes
                    (material_id, user_id, created_at)
                    VALUES (%s, %s, NOW())
                """, (material_id, user_id))
                liked = True
            
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM learning_material_likes
                WHERE material_id = %s
            """, (material_id,))
            
            likes_count = cursor.fetchone()['count']
            
            conn.commit()
            return {
                "success": True,
                "data": {
                    "liked": liked,
                    "likes_count": likes_count
                }
            }
            
        except Exception as e:
            conn.rollback()
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()
            
    @staticmethod
    def get_related_materials(material_id: int, limit: int = 3, same_type_only: bool = False) -> dict:
        # Get related materials based on category and optionally type.

        
        mappings = {
            'article': 'articles',
            'video': 'videos',
            'wiki': 'wiki',
            'community': 'community'
        }
                
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
                
        try:
            material_result = LearningResource.get_by_id(material_id)
            if not material_result['success']:
                return material_result
            
            material = material_result['data']['material']
            
            query = """
                SELECT DISTINCT lm.*, u.username as author_name,
                    (SELECT COUNT(*) FROM learning_material_likes WHERE material_id = lm.id) as likes_count
                FROM learning_materials lm
                LEFT JOIN users u ON lm.author_id = u.id
                WHERE lm.id != %s 
                AND lm.category_id = %s
                AND lm.status = 'published'
            """
            params = [material_id, material['category_id']]
            
            if same_type_only:
                query += " AND lm.type = %s"
                params.append(material['type'])
                
            query += """
                ORDER BY 
                    lm.views_count DESC,
                    likes_count DESC,
                    lm.created_at DESC
                LIMIT %s
            """
            params.append(limit)
            
            cursor.execute(query, params)
            related_materials = cursor.fetchall()
                        
            if len(related_materials) < limit:
                remaining_count = limit - len(related_materials)
                existing_ids = [material_id] + [material['id'] for material in related_materials]
                
                placeholders = ','.join(['%s'] * len(existing_ids))
                
                query = f"""
                    SELECT DISTINCT lm.*, u.username as author_name,
                        (SELECT COUNT(*) FROM learning_material_likes WHERE material_id = lm.id) as likes_count
                    FROM learning_materials lm
                    LEFT JOIN users u ON lm.author_id = u.id
                    WHERE lm.id NOT IN ({placeholders})
                    AND lm.status = 'published'
                """
                params = existing_ids[:]
                
                if same_type_only:
                    query += " AND lm.type = %s"
                    params.append(material['type'])
                    
                query += """
                    ORDER BY 
                        lm.views_count DESC,
                        likes_count DESC,
                        RAND()
                    LIMIT %s
                """
                params.append(remaining_count)
                
                cursor.execute(query, params)
                additional_materials = cursor.fetchall()
                
                existing_ids_set = set(existing_ids)
                filtered_additional_materials = []
                for material in additional_materials:
                    if material['id'] not in existing_ids_set:
                        filtered_additional_materials.append(material)
                        existing_ids_set.add(material['id'])
                
                related_materials.extend(filtered_additional_materials)
            
            formatted_materials = []
            for resource in related_materials:
                formatted_material = {
                    'id': resource['id'],
                    'title': resource['title'],
                    'excerpt': resource.get('excerpt', ''),
                    'type': resource['type'],
                    'duration': resource.get('duration', ''),
                    'thumbnail_url': resource.get('thumbnail_url'),
                    'views_count': resource.get('views_count', 0),
                    'likes_count': resource.get('likes_count', 0),
                    'author_id': resource['author_id'],
                    'author_name': resource.get('author_name', ''),
                    'created_at': resource.get('created_at'),
                    'updated_at': resource.get('updated_at'),
                    'category_path': mappings[resource['type']]
                }
                formatted_materials.append(formatted_material)
            
            return {
                "success": True,
                "data": {
                    "materials": formatted_materials
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_author_articles(author_id: int, exclude_id: int = None, limit: int = 3) -> dict:
        """Get articles by the same author."""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            query = """
                SELECT lm.*, u.username as author_name,
                    (SELECT COUNT(*) FROM learning_material_likes WHERE material_id = lm.id) as likes_count
                FROM learning_materials lm
                LEFT JOIN users u ON lm.author_id = u.id
                WHERE lm.author_id = %s AND lm.type = 'article'
            """
            params = [author_id]
            
            if exclude_id:
                query += " AND lm.id != %s"
                params.append(exclude_id)
            
            query += " ORDER BY lm.created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            articles = cursor.fetchall()
            
            return {
                "success": True,
                "data": {
                    "articles": articles
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_featured_content() -> dict:
        # Get featured content based on views, likes, and comments.
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT 
                    m.*,
                    u.username as author_name,
                    u.avatar_url as author_avatar_url,
                    (SELECT COUNT(*) FROM learning_material_likes l WHERE l.material_id = m.id) as likes_count,
                    (SELECT COUNT(*) FROM learning_material_comments c WHERE c.material_id = m.id) as comments_count
                FROM learning_materials m
                LEFT JOIN users u ON m.author_id = u.id
                WHERE m.status = 'published'
                ORDER BY m.views_count DESC
                LIMIT 3
            """)
            by_views = cursor.fetchall()

            cursor.execute("""
                SELECT 
                    m.*,
                    u.username as author_name,
                    u.avatar_url as author_avatar_url,
                    (SELECT COUNT(*) FROM learning_material_likes l WHERE l.material_id = m.id) as likes_count,
                    (SELECT COUNT(*) FROM learning_material_comments c WHERE c.material_id = m.id) as comments_count
                FROM learning_materials m
                LEFT JOIN users u ON m.author_id = u.id
                WHERE m.status = 'published'
                ORDER BY (
                    SELECT COUNT(*) 
                    FROM learning_material_likes l 
                    WHERE l.material_id = m.id
                ) DESC
                LIMIT 3
            """)
            by_likes = cursor.fetchall()

            cursor.execute("""
                SELECT 
                    m.*,
                    u.username as author_name,
                    u.avatar_url as author_avatar_url,
                    (SELECT COUNT(*) FROM learning_material_likes l WHERE l.material_id = m.id) as likes_count,
                    (SELECT COUNT(*) FROM learning_material_comments c WHERE c.material_id = m.id) as comments_count
                FROM learning_materials m
                LEFT JOIN users u ON m.author_id = u.id
                WHERE m.status = 'published'
                ORDER BY (
                    SELECT COUNT(*) 
                    FROM learning_material_comments c 
                    WHERE c.material_id = m.id
                ) DESC
                LIMIT 3
            """)
            by_comments = cursor.fetchall()

            featured = []
            used_ids = set()

            if by_views:
                featured.append({
                    'content': by_views[0],
                    'featured_for': 'Most Viewed'
                })
                used_ids.add(by_views[0]['id'])

            for content in by_likes:
                if content['id'] not in used_ids:
                    featured.append({
                        'content': content,
                        'featured_for': 'Most Liked'
                    })
                    used_ids.add(content['id'])
                    break

            for content in by_comments:
                if content['id'] not in used_ids:
                    featured.append({
                        'content': content,
                        'featured_for': 'Most Discussed'
                    })
                    used_ids.add(content['id'])
                    break

            return {
                'success': True,
                'data': featured
            }
            
        except Exception as e:
            print(f"Error getting featured content: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            cursor.close()
            conn.close()
            
    @staticmethod
    def get_categories(content_type=None):
        # Get categories with optional content type filter.
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            if content_type and content_type != 'all':
                query = """
                    SELECT c.id, c.title, c.slug, c.description, c.icon_name, c.content_type, COUNT(lm.id) as material_count
                    FROM learning_categories c
                    LEFT JOIN learning_materials lm ON c.id = lm.category_id
                    WHERE c.content_type IN ('general', %s)
                    GROUP BY c.id, c.title, c.slug, c.description, c.icon_name, c.content_type
                    ORDER BY c.title ASC
                """
                cursor.execute(query, (content_type,))
            else:
                query = """
                    SELECT c.id, c.title, c.slug, c.description, c.icon_name, c.content_type, COUNT(lm.id) as material_count
                    FROM learning_categories c
                    LEFT JOIN learning_materials lm ON c.id = lm.category_id
                    GROUP BY c.id, c.title, c.slug, c.description, c.icon_name, c.content_type
                    ORDER BY c.title ASC
                """
                cursor.execute(query)
            
            categories = cursor.fetchall()
            return {
                "success": True,
                "data": {
                    "categories": categories
                }
            }
            
        except Exception as e:
            print(f"Error getting categories: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def create_material(user_id, title, content, category_id, type, excerpt=None, thumbnail_url=None, duration=None, tags=None):
        # Create a new learning material.
        
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT id FROM learning_categories WHERE id = %s", (category_id,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": "Invalid category"
                }
            
            cursor.execute("""
                INSERT INTO learning_materials
                (title, content, excerpt, category_id, type, thumbnail_url, author_id, status, 
                 views_count, likes_count, duration, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                title, 
                content, 
                excerpt, 
                category_id, 
                type,
                thumbnail_url,
                user_id,
                'published', 
                0,  
                0,  
                duration
            ))
            
            material_id = cursor.lastrowid
            
            if tags and isinstance(tags, list) and len(tags) > 0:
                for tag_id in tags:
                    try:
                        cursor.execute("""
                            INSERT INTO learning_material_tags (material_id, tag_id)
                            VALUES (%s, %s)
                        """, (material_id, tag_id))
                    except Exception as tag_error:
                        print(f"Error associating tag {tag_id}: {str(tag_error)}")
            
            cursor.execute("""
                SELECT lm.*, u.username as author_name, lc.title as category_title
                FROM learning_materials lm
                LEFT JOIN users u ON lm.author_id = u.id
                LEFT JOIN learning_categories lc ON lm.category_id = lc.id
                WHERE lm.id = %s
            """, (material_id,))
            
            material = cursor.fetchone()
            
            transformed_material = {
                'id': material['id'],
                'title': material['title'],
                'content': material['content'],
                'excerpt': material['excerpt'] or '',
                'category_id': material['category_id'],
                'category_title': material.get('category_title', ''),
                'type': material['type'],
                'duration': material.get('duration', ''),
                'thumbnail_url': material.get('thumbnail_url'),
                'views_count': material.get('views_count', 0),
                'likes_count': material.get('likes_count', 0),
                'author_id': material['author_id'],
                'author_name': material.get('author_name', ''),
                'status': material.get('status', 'published'),
                'is_liked': False,
                'created_at': material.get('created_at'),
                'updated_at': material.get('updated_at')
            }
            
            conn.commit()
            return {
                "success": True,
                "data": {
                    "material": transformed_material
                }
            }
            
        except Exception as e:
            conn.rollback()
            print(f"Error in create_material: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete_material(material_id, user_id):
        # Delete a learning material.

        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT author_id 
                FROM learning_materials 
                WHERE id = %s
            """, (material_id,))
            
            material = cursor.fetchone()
            if not material:
                return {
                    "success": False,
                    "error": "Material not found"
                }
            
            cursor.execute("""
                SELECT role FROM users WHERE id = %s
            """, (user_id,))
            
            user_result = cursor.fetchone()
            if not user_result:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            is_admin = user_result['role'] == 'admin'
            is_author = material['author_id'] == user_id
            
            if not (is_admin or is_author):
                return {
                    "success": False,
                    "error": "Unauthorized. You must be the author or an admin to delete this material"
                }
  
            cursor.execute("""
                DELETE FROM learning_materials 
                WHERE id = %s
            """, (material_id,))
            
            if cursor.rowcount == 0:
                conn.rollback()
                return {
                    "success": False,
                    "error": "Failed to delete material"
                }
            
            conn.commit()
            return {
                "success": True,
                "message": "Material deleted successfully"
            }
            
        except Exception as e:
            conn.rollback()
            print(f"Error in delete_material: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_material(material_id: int, user_id: int, title: str, content: str, 
                      category_id: int, type: str, excerpt: str = None, 
                      thumbnail_url: str = None, duration: str = None, tags: list = None) -> dict:
        # Update an existing learning material.

        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT author_id FROM learning_materials
                WHERE id = %s
            """, (material_id,))
            
            material = cursor.fetchone()
            if not material:
                return {
                    "success": False,
                    "error": "Material not found"
                }

            cursor.execute("""
                UPDATE learning_materials
                SET title = %s, content = %s, category_id = %s, type = %s,
                    excerpt = %s, thumbnail_url = %s, duration = %s, updated_at = NOW()
                WHERE id = %s
            """, (
                title, content, category_id, type,
                excerpt, thumbnail_url, duration, material_id
            ))
            
            if tags and isinstance(tags, list):
                cursor.execute("DELETE FROM learning_material_tags WHERE material_id = %s", (material_id,))
                
                for tag in tags:
                    cursor.execute("""
                        INSERT INTO learning_material_tags (material_id, tag)
                        VALUES (%s, %s)
                    """, (material_id, tag))
            
            conn.commit()
            
            updated_material = LearningResource.get_by_id(material_id)
            if not updated_material['success']:
                return updated_material
                
            return {
                "success": True,
                "data": updated_material['data']['material']
            }
        except Exception as e:
            conn.rollback()
            print(f"Error updating material: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()

class LearningComment:
    @staticmethod
    def get_comments(material_id, page=1, per_page=10):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Helper function to get replies recursively for any comment
        def get_comment_replies(comment_id):
            cursor.execute("""
                SELECT c.*, u.username
                FROM learning_material_comments c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.parent_id = %s
                ORDER BY c.created_at ASC
            """, (comment_id,))
            
            replies = cursor.fetchall()
            
            for reply in replies:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM learning_material_comment_likes
                    WHERE comment_id = %s
                """, (reply['id'],))
                reply['likes_count'] = cursor.fetchone()['count']
                
                nested_replies = get_comment_replies(reply['id'])
                reply['replies'] = nested_replies
            
            return replies
        
        try:
            offset = (page - 1) * per_page
            
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM learning_material_comments
                WHERE material_id = %s AND parent_id IS NULL
            """, (material_id,))
            total = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT c.*, u.username, u.avatar_url as user_avatar
                FROM learning_material_comments c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.material_id = %s AND c.parent_id IS NULL
                ORDER BY c.created_at DESC
                LIMIT %s OFFSET %s
            """, (material_id, per_page, offset))
            
            comments = cursor.fetchall()
            
            for comment in comments:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM learning_material_comment_likes
                    WHERE comment_id = %s
                """, (comment['id'],))
                comment['likes_count'] = cursor.fetchone()['count']
                
                comment['replies'] = get_comment_replies(comment['id'])
            
            return {
                "success": True,
                "data": {
                    "items": comments,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page,
                    "current_page": page
                }
            }
            
        except Exception as e:
            print(f"Error in get_comments: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def create_comment(material_id, user_id, content, parent_id=None):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            if parent_id:
                cursor.execute("""
                    SELECT material_id FROM learning_material_comments
                    WHERE id = %s
                """, (parent_id,))
                parent = cursor.fetchone()
                if not parent or parent['material_id'] != material_id:
                    return {
                        "success": False,
                        "error": "Invalid parent comment"
                    }
            
            cursor.execute("""
                INSERT INTO learning_material_comments
                (material_id, user_id, parent_id, content, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
            """, (material_id, user_id, parent_id, content))
            
            comment_id = cursor.lastrowid
            
            cursor.execute("""
                SELECT c.*, u.username
                FROM learning_material_comments c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.id = %s
            """, (comment_id,))
            
            comment = cursor.fetchone()
            comment['replies'] = []
            comment['likes_count'] = 0
            
            conn.commit()
            return {
                "success": True,
                "data": {
                    "comment": comment
                }
            }
            
        except Exception as e:
            conn.rollback()
            print(f"Error in create_comment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def toggle_comment_like(comment_id, user_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT id FROM learning_material_comment_likes
                WHERE comment_id = %s AND user_id = %s
            """, (comment_id, user_id))
            
            existing_like = cursor.fetchone()
            
            if existing_like:
                cursor.execute("""
                    DELETE FROM learning_material_comment_likes
                    WHERE comment_id = %s AND user_id = %s
                """, (comment_id, user_id))
                liked = False
            else:
                cursor.execute("""
                    INSERT INTO learning_material_comment_likes
                    (comment_id, user_id, type, created_at)
                    VALUES (%s, %s, 'like', NOW())
                """, (comment_id, user_id))
                liked = True
            
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM learning_material_comment_likes
                WHERE comment_id = %s
            """, (comment_id,))
            
            likes_count = cursor.fetchone()['count']
            
            conn.commit()
            return {
                "success": True,
                "data": {
                    "liked": liked,
                    "likes_count": likes_count
                }
            }
            
        except Exception as e:
            conn.rollback()
            print(f"Error in toggle_comment_like: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            cursor.close()
            conn.close() 
            

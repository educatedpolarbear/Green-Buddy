from models.user_stats import UserStats
from database.connection import Database

class BlogPost:
    @staticmethod
    def get_all(category=None, search=None, author_id=None, tag=None, page=1, per_page=10, current_user_id=None):
        # Get all blog posts with optional filters and pagination.
        db = Database()
        conn = db.get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            trending_post_ids = BlogPost.get_trending_post_ids()
            
            query = """
                SELECT DISTINCT 
                    bp.*,
                    u.username as author_name,
                    u.avatar_url as author_avatar_url,
                    COALESCE(bp.views_count, 0) as views_count,
                    (SELECT COUNT(*) FROM blog_likes WHERE post_id = bp.id) as likes_count,
                    (SELECT COUNT(*) FROM blog_comments WHERE post_id = bp.id) as comments_count,
                    GROUP_CONCAT(DISTINCT t.id) as tag_ids,
                    GROUP_CONCAT(DISTINCT t.name) as tag_names,
                    CASE 
                        WHEN %s IS NOT NULL THEN EXISTS(
                            SELECT 1 FROM blog_likes 
                            WHERE post_id = bp.id AND user_id = %s
                        )
                        ELSE FALSE
                    END as is_liked
                FROM blog_posts bp
                LEFT JOIN users u ON bp.author_id = u.id
                LEFT JOIN blog_post_tags pt ON bp.id = pt.post_id
                LEFT JOIN blog_tags t ON pt.tag_id = t.id
                WHERE 1=1
            """
            params = [current_user_id, current_user_id] 
            
            if category:
                query += " AND bp.category = %s"
                params.append(category)
            if search:
                query += " AND (bp.title LIKE %s OR bp.content LIKE %s OR bp.excerpt LIKE %s)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])
            if author_id:
                query += " AND bp.author_id = %s"
                params.append(author_id)
            if tag:
                query += " AND EXISTS (SELECT 1 FROM blog_post_tags pt2 WHERE pt2.post_id = bp.id AND pt2.tag_id = %s)"
                params.append(tag)
            
            query += " GROUP BY bp.id ORDER BY bp.created_at DESC"
            
            count_query = """
                SELECT COUNT(DISTINCT bp.id) as total 
                FROM blog_posts bp
                LEFT JOIN users u ON bp.author_id = u.id
                LEFT JOIN blog_likes l ON bp.id = l.post_id
                LEFT JOIN blog_comments c ON bp.id = c.post_id
                LEFT JOIN blog_post_tags pt ON bp.id = pt.post_id
                LEFT JOIN blog_tags t ON pt.tag_id = t.id
                WHERE 1=1
            """
            count_params = []
            
            if category:
                count_query += " AND bp.category = %s"
                count_params.append(category)
            if search:
                count_query += " AND (bp.title LIKE %s OR bp.content LIKE %s OR bp.excerpt LIKE %s)"
                search_term = f"%{search}%"
                count_params.extend([search_term, search_term, search_term])
            if author_id:
                count_query += " AND bp.author_id = %s"
                count_params.append(author_id)
            if tag:
                count_query += " AND EXISTS (SELECT 1 FROM blog_post_tags pt2 WHERE pt2.post_id = bp.id AND pt2.tag_id = %s)"
                count_params.append(tag)
            
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['total']
            
            query += " LIMIT %s OFFSET %s"
            offset = (page - 1) * per_page
            params.extend([per_page, offset])
            
            cursor.execute(query, params)
            posts = cursor.fetchall()
            
            for post in posts:
                is_trending = post['id'] in trending_post_ids
                post['is_trending'] = is_trending
                
                if post['tag_ids']:
                    post['tags'] = [
                        {'id': int(id), 'name': name}
                        for id, name in zip(
                            post['tag_ids'].split(','),
                            post['tag_names'].split(',')
                        )
                    ]
                else:
                    post['tags'] = []
                del post['tag_ids']
                del post['tag_names']
            
            return {
                'posts': posts,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
            
        except Exception as e:
            print(f"\n=== ERROR in get_all ===")
            print(f"Error type: {type(e)}")
            print(f"Error message: {str(e)}")
            print(f"Error details: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_featured(limit=3):
        # Get featured blog posts.
        db = Database()
        conn = db.get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT DISTINCT 
                    bp.*,
                    u.username as author_name,
                    GROUP_CONCAT(DISTINCT t.id) as tag_ids,
                    GROUP_CONCAT(DISTINCT t.name) as tag_names
                FROM blog_posts bp
                LEFT JOIN users u ON bp.author_id = u.id
                LEFT JOIN blog_post_tags pt ON bp.id = pt.post_id
                LEFT JOIN blog_tags t ON pt.tag_id = t.id
                WHERE bp.is_featured = 1
                GROUP BY bp.id
                ORDER BY bp.created_at DESC
                LIMIT %s
            """
            
            cursor.execute(query, [limit])
            posts = cursor.fetchall()
            
            for post in posts:
                if post['tag_ids']:
                    post['tags'] = [
                        {'id': int(id), 'name': name}
                        for id, name in zip(
                            post['tag_ids'].split(','),
                            post['tag_names'].split(',')
                        )
                    ]
                else:
                    post['tags'] = []
                del post['tag_ids']
                del post['tag_names']
            
            return posts
            
        except Exception as e:
            print(f"Error in get_featured: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def increment_views(post_id):
        # Increment the views count for a blog post.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE blog_posts SET views_count = COALESCE(views_count, 0) + 1 WHERE id = %s",
                (post_id,)
            )
            
            conn.commit()
        except Exception as e:
            print(f"Error incrementing views: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(post_id, current_user_id=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    b.*,
                    u.username as author_name,
                    (SELECT COUNT(*) FROM blog_likes WHERE post_id = b.id) as likes_count,
                    (SELECT COUNT(*) FROM blog_comments WHERE post_id = b.id) as comments_count,
                    GROUP_CONCAT(DISTINCT t.id) as tag_ids,
                    GROUP_CONCAT(DISTINCT t.name) as tag_names,
                    CASE 
                        WHEN %s IS NOT NULL THEN EXISTS(
                            SELECT 1 FROM blog_likes 
                            WHERE post_id = b.id AND user_id = %s
                        )
                        ELSE FALSE
                    END as is_liked
                FROM blog_posts b
                LEFT JOIN users u ON b.author_id = u.id
                LEFT JOIN blog_post_tags pt ON b.id = pt.post_id
                LEFT JOIN blog_tags t ON pt.tag_id = t.id
                WHERE b.id = %s
                GROUP BY b.id
            """
            
            cursor.execute(query, (current_user_id, current_user_id, post_id))
            post = cursor.fetchone()
            
            if post:
                # Process tags
                if post['tag_ids']:
                    post['tags'] = [
                        {'id': int(id), 'name': name}
                        for id, name in zip(
                            post['tag_ids'].split(','),
                            post['tag_names'].split(',')
                        )
                    ]
                else:
                    post['tags'] = []
                del post['tag_ids']
                del post['tag_names']
            
            return post
        except Exception as e:
            print(f"Error in get_by_id: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def create(author_id, title, content, excerpt, featured_image_url, tags=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                INSERT INTO blog_posts (
                    author_id, title, content, excerpt, featured_image_url,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """
            
            cursor.execute(query, (author_id, title, content, excerpt, featured_image_url))
            conn.commit()
            post_id = cursor.lastrowid
            
            try:
                UserStats.update_stat_and_achievements(
                    author_id,
                    'blog_posts',
                    {
                        'title': title
                    }
                )
            except Exception as e:
                print(f"Error updating stats and achievements: {str(e)}")
            
            if tags:
                for tag_name in tags:
                    cursor.execute(
                        "INSERT INTO blog_tags (name) VALUES (%s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)",
                        (tag_name,)
                    )
                    tag_id = cursor.lastrowid
                    
                    cursor.execute(
                        "INSERT INTO blog_post_tags (post_id, tag_id) VALUES (%s, %s)",
                        (post_id, tag_id)
                    )
                conn.commit()
            
            return BlogPost.get_by_id(post_id)
        except Exception as e:
            conn.rollback()
            print(f"Error in create: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update(post_id, title=None, content=None, category=None, tags=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            
            if content is not None:
                updates.append("content = %s")
                params.append(content)
            
            if category is not None:
                updates.append("category = %s")
                params.append(category)
            
            if updates:
                updates.append("updated_at = NOW()")
                query = f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = %s"
                params.append(post_id)
                
                cursor.execute(query, params)
                
                # Update tags if provided
                if tags is not None:
                    # Remove existing tags
                    cursor.execute("DELETE FROM blog_post_tags WHERE post_id = %s", (post_id,))
                    
                    # Add new tags
                    for tag_name in tags:
                        # Get or create tag
                        cursor.execute(
                            "INSERT INTO blog_tags (name) VALUES (%s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)",
                            (tag_name,)
                        )
                        tag_id = cursor.lastrowid
                        
                        # Link tag to post
                        cursor.execute(
                            "INSERT INTO blog_post_tags (post_id, tag_id) VALUES (%s, %s)",
                            (post_id, tag_id)
                        )
                
                conn.commit()
            
            return BlogPost.get_by_id(post_id)
        except Exception as e:
            conn.rollback()
            print(f"Error in update: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(post_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM blog_likes WHERE post_id = %s", (post_id,))
            cursor.execute("DELETE FROM blog_comments WHERE post_id = %s", (post_id,))
            cursor.execute("DELETE FROM blog_posts WHERE id = %s", (post_id,))
            
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
    def get_related(post_id, limit=3, current_user_id=None):
        """Get posts related to the specified post based on shared tags."""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            tag_query = """
                SELECT pt.tag_id 
                FROM blog_post_tags pt 
                WHERE pt.post_id = %s
            """
            cursor.execute(tag_query, (post_id,))
            tag_rows = cursor.fetchall()
            
            if not tag_rows:
                return []
            
            tag_ids = [row['tag_id'] for row in tag_rows]
            
            placeholders = ', '.join(['%s'] * len(tag_ids))
            query = f"""
                SELECT DISTINCT 
                    bp.*,
                    u.username as author_name,
                    COALESCE(bp.views_count, 0) as views_count,
                    (SELECT COUNT(*) FROM blog_likes WHERE post_id = bp.id) as likes_count,
                    (SELECT COUNT(*) FROM blog_comments WHERE post_id = bp.id) as comments_count,
                    GROUP_CONCAT(DISTINCT t.id) as tag_ids,
                    GROUP_CONCAT(DISTINCT t.name) as tag_names,
                    COUNT(DISTINCT pt.tag_id) as matching_tags_count,
                    CASE 
                        WHEN %s IS NOT NULL THEN EXISTS(
                            SELECT 1 FROM blog_likes 
                            WHERE post_id = bp.id AND user_id = %s
                        )
                        ELSE FALSE
                    END as is_liked
                FROM blog_posts bp
                JOIN blog_post_tags pt ON bp.id = pt.post_id
                JOIN blog_tags t ON pt.tag_id = t.id
                JOIN users u ON bp.author_id = u.id
                WHERE pt.tag_id IN ({placeholders}) 
                AND bp.id != %s
                GROUP BY bp.id
                ORDER BY matching_tags_count DESC, bp.created_at DESC
                LIMIT %s
            """
            
            params = [current_user_id, current_user_id] + tag_ids + [post_id, limit]
            
            cursor.execute(query, params)
            posts = cursor.fetchall()
            
            for post in posts:
                if post['tag_ids']:
                    post['tags'] = [
                        {'id': int(id), 'name': name}
                        for id, name in zip(
                            post['tag_ids'].split(','),
                            post['tag_names'].split(',')
                        )
                    ]
                else:
                    post['tags'] = []
                del post['tag_ids']
                del post['tag_names']
                del post['matching_tags_count']
            
            return posts
        except Exception as e:
            print(f"Error in get_related: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add_like(post_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT IGNORE INTO blog_likes (post_id, user_id, created_at) VALUES (%s, %s, NOW())",
                (post_id, user_id)
            )
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM blog_likes WHERE post_id = %s",
                (post_id,)
            )
            likes_count = cursor.fetchone()[0]
            
            conn.commit()
            return {
                "message": "Post liked successfully",
                "likes_count": likes_count
            }
        except Exception as e:
            conn.rollback()
            print(f"Error in add_like: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def remove_like(post_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM blog_likes WHERE post_id = %s AND user_id = %s",
                (post_id, user_id)
            )
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM blog_likes WHERE post_id = %s",
                (post_id,)
            )
            likes_count = cursor.fetchone()[0]
            
            conn.commit()
            return {
                "message": "Like removed successfully",
                "likes_count": likes_count
            }
        except Exception as e:
            conn.rollback()
            print(f"Error in remove_like: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_comments(post_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    c.*,
                    u.username as author_name,
                    u.avatar_url as author_avatar_url
                FROM blog_comments c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.post_id = %s
                ORDER BY c.created_at DESC
            """
            
            cursor.execute(query, (post_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error in get_comments: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add_comment(post_id, user_id, content):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                INSERT INTO blog_comments (
                    post_id, user_id, content, created_at
                ) VALUES (%s, %s, %s, NOW())
            """
            
            cursor.execute(query, (post_id, user_id, content))
            conn.commit()
            
            query = """
                SELECT 
                    c.*,
                    u.username as author_name
                FROM blog_comments c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.id = %s
            """
            
            cursor.execute(query, (cursor.lastrowid,))
            try:
                UserStats.update_stat_and_achievements(
                    user_id,
                    'blog_comments',
                    {
                        
                    }
                )
            except Exception as e:
                print(f"Error updating stats and achievements: {str(e)}")
                
            return cursor.fetchone()
        except Exception as e:
            conn.rollback()
            print(f"Error in add_comment: {str(e)}")
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
                SELECT c.*, COUNT(b.id) as post_count
                FROM categories c
                LEFT JOIN blog_posts b ON c.id = b.category_id
                GROUP BY c.id
                ORDER BY c.name
            """)
            
            return cursor.fetchall()
        except Exception as e:
            print(f"Error in get_categories: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_tags():
        # Get all unique blog tags.
        db = Database()
        conn = db.get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT DISTINCT t.id, t.name, COUNT(pt.post_id) as post_count
                FROM blog_tags t
                LEFT JOIN blog_post_tags pt ON t.id = pt.tag_id
                GROUP BY t.id, t.name
                ORDER BY post_count DESC, name ASC
            """
            
            cursor.execute(query)
            tags = cursor.fetchall()
            return tags
            
        except Exception as e:
            print(f"Error in get_tags: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add_comment_like(comment_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO blog_likes (user_id, comment_id, type, created_at)
                VALUES (%s, %s, 'like', NOW())
                """,
                (user_id, comment_id)
            )
            
            conn.commit()
            return {"message": "Comment liked successfully"}
        except Exception as e:
            conn.rollback()
            print(f"Error in add_comment_like: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def remove_comment_like(comment_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM blog_likes WHERE comment_id = %s AND user_id = %s",
                (comment_id, user_id)
            )
            
            conn.commit()
            return {"message": "Comment unliked successfully"}
        except Exception as e:
            conn.rollback()
            print(f"Error in remove_comment_like: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_trending_tags():
        """Get top 3 tags with the most views in the last day."""
        db = Database()
        conn = db.get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    t.id,
                    t.name,
                    COUNT(DISTINCT pt.post_id) as post_count,
                    CAST(SUM(COALESCE(bp.views_count, 0)) as SIGNED) as total_views
                FROM blog_tags t
                JOIN blog_post_tags pt ON t.id = pt.tag_id
                JOIN blog_posts bp ON pt.post_id = bp.id
                WHERE bp.views_count > 0
                GROUP BY t.id, t.name
                HAVING total_views > 0
                ORDER BY total_views DESC, post_count DESC
                LIMIT 3
            """
            
            cursor.execute(query)
            trending_tags = cursor.fetchall()
            
            # Format the response
            for tag in trending_tags:
                tag['total_views'] = int(tag['total_views'])
                tag['post_count'] = int(tag['post_count'])
            
            return trending_tags
            
        except Exception as e:
            print(f"Error in get_trending_tags: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_trending_post_ids():
        # Get IDs of the top 3 most viewed posts.
        db = Database()
        conn = db.get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT id
                FROM blog_posts
                WHERE views_count > 0
                ORDER BY views_count DESC
                LIMIT 3
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            trending_ids = [post['id'] for post in results]
            return trending_ids
            
            
        except Exception as e:
            print(f"Error in get_trending_post_ids: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_top_authors(limit=5):
        # Get top authors based on the number of likes on their blog posts.

        db = Database()
        conn = db.get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    u.id AS author_id,
                    u.username AS author_name,
                    u.avatar_url AS author_avatar_url,
                    COUNT(DISTINCT bp.id) AS post_count,
                    COALESCE(SUM(
                        (SELECT COUNT(*) FROM blog_likes 
                         WHERE post_id = bp.id AND post_id IS NOT NULL)
                    ), 0) AS likes_count
                FROM users u
                JOIN blog_posts bp ON u.id = bp.author_id
                WHERE bp.status = 'published'
                GROUP BY u.id, u.username, u.avatar_url
                ORDER BY likes_count DESC, post_count DESC
                LIMIT %s
            """
            
            cursor.execute(query, (limit,))
            top_authors = cursor.fetchall()
            
            return top_authors
            
        except Exception as e:
            print(f"Error in get_top_authors: {e}")
            raise e
        finally:
            cursor.close()
            conn.close() 
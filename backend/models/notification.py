from database.connection import Database

class Notification:
    @staticmethod
    def get_all(user_id, page=1, limit=10):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            offset = (page - 1) * limit
            
            query = """
                SELECT 
                    id,
                    user_id,
                    type,
                    title,
                    content,
                    link,
                    is_read,
                    created_at
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, (user_id, limit, offset))
            notifications = cursor.fetchall()
            
            transformed_notifications = []
            for notification in notifications:
                transformed_notifications.append({
                    **notification,
                    'data': {'link': notification['link']} if notification['link'] else None
                })
            
            cursor.execute(
                "SELECT COUNT(*) as total FROM notifications WHERE user_id = %s",
                (user_id,)
            )
            total = cursor.fetchone()['total']
            
            return {
                'notifications': transformed_notifications,
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

    @staticmethod
    def get_unread_count(user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT COUNT(*) as unread_count 
                FROM notifications 
                WHERE user_id = %s AND is_read = FALSE
                """,
                (user_id,)
            )
            
            result = cursor.fetchone()
            return {'unread_count': result['unread_count'] if result else 0}
        except Exception as e:
            print(f"Error in get_unread_count: {str(e)}")
            return {'unread_count': 0}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def create(user_id, type, title, content, link=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                INSERT INTO notifications (
                    user_id, type, title, content, link, is_read, created_at
                ) VALUES (%s, %s, %s, %s, %s, FALSE, NOW())
            """
            
            cursor.execute(query, (user_id, type, title, content, link))
            conn.commit()
            
            notification_id = cursor.lastrowid
            cursor.execute("""
                SELECT 
                    id,
                    user_id,
                    type,
                    title,
                    content,
                    link,
                    is_read,
                    created_at
                FROM notifications 
                WHERE id = %s
            """, (notification_id,))
            notification = cursor.fetchone()
            
            if notification:
                notification['data'] = {'link': notification['link']} if notification['link'] else None
            
            return notification
        except Exception as e:
            conn.rollback()
            print(f"Error in create: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def mark_as_read(notification_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE notifications 
                SET is_read = TRUE
                WHERE id = %s AND user_id = %s
                """,
                (notification_id, user_id)
            )
            
            if cursor.rowcount == 0:
                return {"error": "Notification not found"}
            
            conn.commit()
            return {"message": "Notification marked as read"}
        except Exception as e:
            conn.rollback()
            print(f"Error in mark_as_read: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def mark_all_as_read(user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE notifications 
                SET is_read = TRUE
                WHERE user_id = %s AND is_read = FALSE
                """,
                (user_id,)
            )
            
            rows_affected = cursor.rowcount
            
            conn.commit()
            return {
                "message": "All notifications marked as read",
                "notifications_updated": rows_affected
            }
        except Exception as e:
            conn.rollback()
            print(f"Error in mark_all_as_read: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete_all(user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,))
            
            conn.commit()
            return {"message": "All notifications deleted"}
        except Exception as e:
            conn.rollback()
            print(f"Error in delete_all: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close() 
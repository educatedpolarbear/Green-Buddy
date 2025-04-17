from typing import Dict, Optional
from database.connection import Database
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class UserStats:
    # Model for managing user statistics in a centralized table.
    
    STAT_CATEGORIES = {
        'environmental_action': [
            'trees_planted',
            'co2_offset',
            'volunteer_hours',
            'challenges_completed'
        ],
        'community_engagement': [
            'events_joined',
            'events_created',
            'groups_created',
            'forum_discussions',
            'forum_replies',
            'forum_likes',
            'forum_solutions',
            'unique_event_locations',
            'group_members',
            'followers_count',
            'following_count'
        ],
        'knowledge_learning': [
            'learning_completed',
            'materials_read',
            'blog_comments',
            'blog_posts'
        ],
        'platform_engagement': [
            'login_count',
            'login_streak',
            'account_age'
        ]
    }
    
    @staticmethod
    def create_table_if_not_exists():
        # Create the user_stats table if it doesn't exist.
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INT PRIMARY KEY,
                    stats_data JSON NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("User stats table created or already exists")
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_user_stats(user_id: int) -> Dict:
        # Get all stats for a user, creating default stats if none exist.
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT stats_data FROM user_stats WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            
            if result:
                return json.loads(result['stats_data'])
            
            default_stats = UserStats.create_default_stats()
            UserStats.update_user_stats(user_id, default_stats)
            
            return default_stats
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update_user_stats(user_id: int, stats: Dict) -> bool:
        # Update or create stats for a user.
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            stats_json = json.dumps(stats, cls=DecimalEncoder)
            
            cursor.execute("""
                INSERT INTO user_stats (user_id, stats_data, last_updated)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    stats_data = VALUES(stats_data),
                    last_updated = NOW()
            """, (user_id, stats_json))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user stats: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def increment_stat(user_id: int, stat_name: str, increment_by: int = 1) -> bool:
        # Increment a specific stat for a user.
        stats = UserStats.get_user_stats(user_id)
        
        if stat_name in stats:
            stats[stat_name] += increment_by
        else:
            stats[stat_name] = increment_by
        
        return UserStats.update_user_stats(user_id, stats)
    
    @staticmethod
    def set_stat(user_id: int, stat_name: str, value) -> bool:
        # Set a specific stat to a specific value.
        stats = UserStats.get_user_stats(user_id)
        stats[stat_name] = value
        return UserStats.update_user_stats(user_id, stats)
    
    @staticmethod
    def create_default_stats() -> Dict:
        # Create default stats dictionary with all stats initialized to 0.
        default_stats = {}
        
        for category, stat_names in UserStats.STAT_CATEGORIES.items():
            for stat_name in stat_names:
                default_stats[stat_name] = 0
        
        return default_stats
   
    @staticmethod
    def update_stat_from_source(user_id: int, stat_name: str) -> bool:
        # Calculate a stat's current value from its source table and update the user_stats table.

        try:
            valid_stat = False
            for category, stat_names in UserStats.STAT_CATEGORIES.items():
                if stat_name in stat_names:
                    valid_stat = True
                    break
            
            if not valid_stat:
                print(f"Error: '{stat_name}' is not a valid stat name.")
                return False
            
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            try:
                queries = {
                    # Environmental action stats
                    'trees_planted': ("""
                        SELECT COALESCE(SUM(e.trees_planted), 0) as count
                        FROM event_participants ep
                        JOIN events e ON ep.event_id = e.id
                        WHERE ep.user_id = %s
                    """, (user_id,)),
                    
                    'co2_offset': ("""
                        SELECT COALESCE(SUM(e.co2_offset), 0) as count
                        FROM event_participants ep
                        JOIN events e ON ep.event_id = e.id
                        WHERE ep.user_id = %s
                    """, (user_id,)),
                    
                    'volunteer_hours': ("""
                        SELECT COALESCE(SUM(e.volunteer_hour), 0) as count
                        FROM event_participants ep
                        JOIN events e ON ep.event_id = e.id
                        WHERE ep.user_id = %s
                    """, (user_id,)),
                    
                    'challenges_completed': ("""
                        SELECT COUNT(*) as count
                        FROM challenge_status
                        WHERE user_id = %s AND status = 'completed'
                    """, (user_id,)),
                    
                    # Community engagement stats
                    'events_joined': ("""
                        SELECT COUNT(*) as count
                        FROM event_participants WHERE user_id = %s
                    """, (user_id,)),
                    
                    'events_created': ("""
                        SELECT COUNT(*) as count
                        FROM events WHERE organizer_id = %s
                    """, (user_id,)),
                    
                    'groups_created': ("""
                        SELECT COUNT(*) as count
                        FROM groups WHERE creator_id = %s
                    """, (user_id,)),
                    
                    'forum_discussions': ("""
                        SELECT COUNT(*) as count
                        FROM forum_discussions WHERE author_id = %s
                    """, (user_id,)),
                    
                    'forum_replies': ("""
                        SELECT COUNT(*) as count
                        FROM forum_replies WHERE author_id = %s
                    """, (user_id,)),
                    
                    'forum_likes': ("""
                        SELECT 
                            (SELECT COUNT(*) FROM forum_likes WHERE discussion_id IN 
                                (SELECT id FROM forum_discussions WHERE author_id = %s)) +
                            (SELECT COUNT(*) FROM forum_likes WHERE reply_id IN 
                                (SELECT id FROM forum_replies WHERE author_id = %s))
                        as count
                    """, (user_id, user_id)),
                    
                    'forum_solutions': ("""
                        SELECT COUNT(*) as count
                        FROM forum_replies 
                        WHERE author_id = %s AND is_solution = TRUE
                    """, (user_id,)),
                    
                    'unique_event_locations': ("""
                        SELECT COUNT(DISTINCT e.location) as count
                        FROM event_participants ep
                        JOIN events e ON ep.event_id = e.id
                        WHERE ep.user_id = %s
                    """, (user_id,)),
                    
                    'group_members': ("""
                        SELECT COALESCE(MAX(member_count), 0) as count
                        FROM (
                            SELECT g.id, COUNT(gm.id) as member_count
                            FROM groups g
                            LEFT JOIN group_members gm ON g.id = gm.group_id
                            WHERE g.creator_id = %s
                            GROUP BY g.id
                        ) as group_counts
                    """, (user_id,)),
                    
                    # Knowledge & learning stats
                    'learning_completed': ("""
                        SELECT COUNT(*) as count
                        FROM learning_material_progress
                        WHERE user_id = %s AND completion_type = 'completion'
                    """, (user_id,)),
                    
                    'materials_read': ("""
                        SELECT COUNT(*) as count
                        FROM learning_material_progress
                        WHERE user_id = %s AND completion_type = 'view'
                    """, (user_id,)),
                    
                    'blog_comments': ("""
                        SELECT COUNT(*) as count
                        FROM blog_comments WHERE user_id = %s
                    """, (user_id,)),
                    
                    'blog_posts': ("""
                        SELECT COUNT(*) as count
                        FROM blog_posts WHERE author_id = %s
                    """, (user_id,)),
                    
                    # Platform engagement stats
                    'login_count': ("""
                        SELECT COUNT(*) as count
                        FROM user_logins WHERE user_id = %s
                    """, (user_id,)),
                    
                    'account_age': ("""
                        SELECT TIMESTAMPDIFF(MONTH, created_at, NOW()) as count
                        FROM users WHERE id = %s
                    """, (user_id,)),
                    
                    'login_streak': ("""
                        SELECT MAX(streak) as count FROM (
                            SELECT 
                                COUNT(*) as streak
                            FROM (
                                SELECT 
                                    login_date,
                                    @row_num := @row_num + 1 as row_num,
                                    DATE_SUB(login_date, INTERVAL @row_num DAY) as grp
                                FROM (
                                    SELECT DISTINCT DATE(login_time) as login_date
                                    FROM user_logins
                                    WHERE user_id = %s
                                    ORDER BY login_date
                                ) as dates
                                JOIN (SELECT @row_num := 0) as r
                            ) as t
                            GROUP BY grp
                        ) as streaks
                    """, (user_id,)),
                    'followers_count': ("""
                        SELECT COUNT(*) as count
                        FROM user_followers
                        WHERE followed_id = %s
                    """, (user_id,)),
                    'following_count': ("""
                        SELECT COUNT(*) as count
                        FROM user_followers
                        WHERE follower_id = %s
                    """, (user_id,)),
                    
                }
                
                if stat_name not in queries:
                    print(f"Error: No query defined for stat '{stat_name}'.")
                    return False
                
                query, params = queries[stat_name]
                try:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    result = cursor.fetchone()
                    current_value = result['count'] if result and 'count' in result else 0
                    
                    return UserStats.set_stat(user_id, stat_name, current_value)
                except Exception as e:
                    print(f"Error executing query for {stat_name}: {e}")
                    return False
            finally:
                cursor.close()
                conn.close()
        except Exception as e:
            print(f"Error updating stat from source: {e}")
            return False
    
    @staticmethod
    def refresh_user_stats(user_id: int) -> Dict:
        # Refresh all stats for a user by querying the database.
        try:
            stats = UserStats.create_default_stats()
            
            for category, stat_names in UserStats.STAT_CATEGORIES.items():
                for stat_name in stat_names:
                    UserStats.update_stat_from_source(user_id, stat_name)
            
            # Return the updated stats
            return UserStats.get_user_stats(user_id)
        except Exception as e:
            print(f"Error refreshing user stats: {e}")
            return UserStats.create_default_stats()  

    @staticmethod
    def update_single_stat(user_id, stat_name, value):
        # Updates a single statistic in the user_stats table.
        
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT 1 FROM user_stats WHERE user_id = %s", (user_id,))
            has_stats = cursor.fetchone() is not None
            
            if has_stats:
                cursor.execute("SELECT stats_data FROM user_stats WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()
                if not result:
                    stats_data = {}
                else:
                    stats_data = json.loads(result['stats_data']) if result['stats_data'] else {}
                
                stats_data[stat_name] = value
                
                cursor.execute(
                    "UPDATE user_stats SET stats_data = %s, last_updated = NOW() WHERE user_id = %s",
                    (json.dumps(stats_data), user_id)
                )
            else:
                stats_data = {stat_name: value}
                cursor.execute(
                    "INSERT INTO user_stats (user_id, stats_data, last_updated) VALUES (%s, %s, NOW())",
                    (user_id, json.dumps(stats_data))
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error in update_single_stat for {stat_name}: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_stat_and_achievements(user_id: int, stat_name: str, activity_data: Dict) -> bool:
        # Compact function to update a stat, check achievements, and add activity in one call.
        try:
            UserStats.update_stat_from_source(user_id, stat_name)
            
            from models.achievement import achievements
            
            from models.achievement import UserActivity
            UserActivity.add_activity(user_id, stat_name, activity_data)
            awarded = achievements.check_achievement_progress(user_id)

            return True
        except Exception as e:
            print(f"Error in update_stat_and_achievements: {str(e)}")
            return False
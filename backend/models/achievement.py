from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional
from database.connection import Database
from models.user_stats import UserStats
from models.notification import Notification
from models.websockets import send_achievement_notification

DAILY_EXP_LIMIT = 5000 
EXP_PER_LEVEL = 100    
CACHE_DURATION = 300   

class AchievementCache:
    _cache = {}
    
    @staticmethod
    def get(key: str) -> Optional[Dict]:
        if key in AchievementCache._cache:
            data, timestamp = AchievementCache._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=CACHE_DURATION):
                return data
            del AchievementCache._cache[key]
        return None
    
    @staticmethod
    def set(key: str, data: Dict):
        AchievementCache._cache[key] = (data, datetime.now())

    @staticmethod
    def clear(key: str):
        if key in AchievementCache._cache:
            del AchievementCache._cache[key]

    @staticmethod
    def get_cached_achievements(user_id: int) -> Optional[Dict]:
        # Get cached achievements for a user or fetch from database if not cached.
        cache_key = f"user_achievements_{user_id}"
        cached_data = AchievementCache.get(cache_key)
        if cached_data:
            return cached_data
        
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
            SELECT 
                at.id,
                at.name,
                at.description,
                at.icon_name,
                at.exp_reward,
                at.criteria,
                ua.earned_at
            FROM achievement_types at
            JOIN user_achievements ua ON at.id = ua.achievement_id
            WHERE ua.user_id = %s
            ORDER BY ua.earned_at DESC
            """, (user_id,))
        
            achievements = cursor.fetchall()
            
            for achievement in achievements:
                if achievement['criteria']:
                    achievement['criteria'] = json.loads(achievement['criteria'])
            
            result = {
                'achievements': achievements,
                'total_count': len(achievements)
            }
            
            AchievementCache.set(cache_key, result)
            return result
        finally:
            cursor.close()
            conn.close()

class UserActivity:
    def __init__(self, id: int = None, user_id: int = None, activity_type: str = None,
                 activity_data: Dict = None, created_at: datetime = None):
        self.id = id
        self.user_id = user_id
        self.activity_type = activity_type
        self.activity_data = activity_data
        self.created_at = created_at

    @staticmethod
    def get_user_activities(user_id: int, limit: int = 20, offset: int = 0) -> List[Dict]:
        # Get user's activity feed with pagination.
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM user_activities
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, limit, offset))
            activities = []
            for row in cursor.fetchall():
                row['activity_data'] = json.loads(row['activity_data']) if row['activity_data'] else {}
                activities.append(row)
            return activities
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add_activity(user_id: int, activity_type: str, activity_data: Dict) -> Dict:
        # Add a new activity to the user's feed.
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            conn.start_transaction(isolation_level='READ COMMITTED')
            
            cursor.execute("""
                INSERT INTO user_activities (user_id, activity_type, activity_data)
                VALUES (%s, %s, %s)
            """, (user_id, activity_type, json.dumps(activity_data)))
            
            activity_id = cursor.lastrowid
            
            cursor.execute("""
                SELECT * FROM user_activities WHERE id = %s
            """, (activity_id,))
            
            activity = cursor.fetchone()
            
            UserStats.refresh_user_stats(user_id)

            achievements.check_achievement_progress(user_id)
            
            conn.commit()
            activity['activity_data'] = json.loads(activity['activity_data']) if activity['activity_data'] else {}
            return activity
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_stats(user_id: int) -> Dict:
        # Get user's activity statistics.
        return UserStats.get_user_stats(user_id)

class Achievements:
    @staticmethod
    def calculate_level(exp: int) -> int:
        # Calculate user level from experience points consistently across the application.
        return (exp // EXP_PER_LEVEL) + 1
    
    @staticmethod
    def check_and_apply_daily_exp_limit(user_id: int, exp_to_add: int) -> int:
        # Check daily EXP limit and return the actual EXP that can be added.
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
            SELECT COALESCE(SUM(
                CAST(JSON_EXTRACT(activity_data, '$.exp_reward') AS SIGNED)
            ), 0) as daily_exp
            FROM user_activities
            WHERE user_id = %s 
            AND activity_type IN ('achievement_earned', 'challenge_completed', 'learning_completed')
            AND DATE(created_at) = CURDATE()
        """, (user_id,))
            
            result = cursor.fetchone()
            daily_exp = result['daily_exp'] if result else 0
            
            remaining_exp = max(0, DAILY_EXP_LIMIT - daily_exp)
            return min(exp_to_add, remaining_exp)
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def award_exp_with_transaction(user_id: int, exp_amount: int, activity_type: str, activity_data: Dict) -> Dict:
        """Award experience points to a user with proper transaction handling."""
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            conn.start_transaction(isolation_level='READ COMMITTED')
            
            cursor.execute("SELECT exp FROM users WHERE id = %s FOR UPDATE", (user_id,))
            current_exp = cursor.fetchone()['exp']
            
            actual_exp = Achievements.check_and_apply_daily_exp_limit(user_id, exp_amount)
            if actual_exp <= 0:
                conn.rollback()
                return {
                    'success': False,
                    'message': 'Daily EXP limit reached',
                    'exp_gained': 0,
                    'new_level': Achievements.calculate_level(current_exp)
                }
            
            new_exp = current_exp + actual_exp
            cursor.execute(
                "UPDATE users SET exp = %s WHERE id = %s",
                (new_exp, user_id)
            )
            
            activity_data['exp_reward'] = actual_exp
            cursor.execute("""
                INSERT INTO user_activities 
                (user_id, activity_type, activity_data, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (user_id, activity_type, json.dumps(activity_data)))
            
            conn.commit()
            
            return {
                'success': True,
                'exp_gained': actual_exp,
                'new_level': Achievements.calculate_level(new_exp),
                'total_exp': new_exp
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_achievements(user_id: int) -> List[Dict]:
        # Get achievements earned by a specific user.
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT a.*, at.name, at.description, at.criteria, at.exp_reward, at.category
                FROM user_achievements a
                JOIN achievement_types at ON a.achievement_id = at.id
                WHERE a.user_id = %s
                ORDER BY a.earned_at DESC
            """, (user_id,))
            
            achievements = cursor.fetchall()
            
            for achievement in achievements:
                if achievement['criteria']:
                    achievement['criteria'] = json.loads(achievement['criteria'])
            
            return achievements
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_user_progress(user_id: int) -> List[Dict]:
        # Get progress for unearned achievements.
        return Achievements.check_achievement_progress(user_id)
    
    @staticmethod
    def check_achievement_criteria(user_id: int, achievement_id: int) -> bool:
        # Check if a user meets the criteria for an achievement.
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT criteria, category FROM achievement_types WHERE id = %s
            """, (achievement_id,))
            achievement = cursor.fetchone()
            if not achievement or not achievement['criteria']:
                return False
            
            criteria = json.loads(achievement['criteria'])
            
            user_stats = UserStats.get_user_stats(user_id)
            
            criterion_type = criteria['type']
            
            # Handle different field names for required count
            if 'count' in criteria:
                required_count = criteria['count']
            elif 'months' in criteria and criterion_type == 'account_age':
                required_count = criteria['months']
            elif 'days' in criteria and criterion_type == 'login_streak':
                required_count = criteria['days']
            else:
                required_count = criteria.get('count', 0)

            
            if criterion_type in user_stats:
                current_count = user_stats[criterion_type]
                if current_count is None:
                    current_count = 0
                return current_count >= required_count
            
            return False
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def award_achievement(user_id: int, achievement_id: int) -> Optional[Dict]:
        # Award an achievement to a user if they don't already have it.
        db = Database()
        achievement_data = None
        notification_data = None
        
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            conn.start_transaction(isolation_level='READ COMMITTED')
            
            cursor.execute("""
                SELECT id FROM user_achievements
                WHERE user_id = %s AND achievement_id = %s
            """, (user_id, achievement_id))
            if cursor.fetchone():
                conn.rollback()
                return None

            cursor.execute("""
                SELECT * FROM achievement_types WHERE id = %s
            """, (achievement_id,))
            achievement = cursor.fetchone()
            if not achievement:
                conn.rollback()
                return None

            cursor.execute("""
                INSERT INTO user_achievements (user_id, achievement_id)
                VALUES (%s, %s)
            """, (user_id, achievement_id))

            cursor.execute("SELECT exp FROM users WHERE id = %s", (user_id,))
            current_exp = cursor.fetchone()['exp']
            
            cursor.execute("""
                SELECT COALESCE(SUM(
                    CAST(JSON_EXTRACT(activity_data, '$.exp_reward') AS SIGNED)
                ), 0) as daily_exp
                FROM user_activities
                WHERE user_id = %s 
                AND activity_type IN ('achievement_earned', 'challenge_completed', 'learning_completed')
                AND DATE(created_at) = CURDATE()
            """, (user_id,))
            
            result = cursor.fetchone()
            daily_exp = result['daily_exp'] if result else 0
            
            remaining_exp = max(0, DAILY_EXP_LIMIT - daily_exp)
            actual_exp = min(achievement['exp_reward'], remaining_exp)
            
            if actual_exp <= 0:
                conn.rollback()
                return None
            
            new_exp = current_exp + actual_exp
            cursor.execute(
                "UPDATE users SET exp = %s WHERE id = %s",
                (new_exp, user_id)
            )
            
            activity_data = {
                'achievement_id': achievement_id,
                'name': achievement['name'],
                'exp_reward': actual_exp
            }
            cursor.execute("""
                INSERT INTO user_activities 
                (user_id, activity_type, activity_data, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (user_id, 'achievement_earned', json.dumps(activity_data)))

            notification_data = {
                'user_id': user_id,
                'type': "achievement_earned",
                'title': "Achievement Unlocked!",
                'content': f"You've earned the '{achievement['name']}' achievement and {actual_exp} XP!",
                'link': "/achievements"
            }
            
            achievement_data = {
                'id': achievement['id'],
                'name': achievement['name'],
                'description': achievement['description'],
                'exp_reward': actual_exp,
                'icon_name': achievement.get('icon_name', 'award'),
                'category': achievement.get('category', 'general')
            }

            conn.commit()
            
            result = {
                'id': achievement['id'],
                'name': achievement['name'],
                'description': achievement['description'],
                'criteria': json.loads(achievement['criteria']) if achievement['criteria'] else {},
                'exp_awarded': actual_exp,
                'new_level': Achievements.calculate_level(new_exp)
            }
            
            return result
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
            if notification_data:
                try:
                    Notification.create(
                        user_id=notification_data['user_id'],
                        type=notification_data['type'],
                        title=notification_data['title'],
                        content=notification_data['content'],
                        link=notification_data['link']
                    )
                    
                    if achievement_data:
                        send_achievement_notification(user_id, achievement_data)
                except Exception as e:
                    print(f"Error creating notification: {str(e)}")

    @staticmethod
    def get_all() -> List[Dict]:
        # Get all achievement types.
        db = Database()
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT id, name, description, criteria, exp_reward, category, icon_name
                FROM achievement_types
                ORDER BY category, id
            ''')
            
            achievements = cursor.fetchall()
            
            for achievement in achievements:
                if achievement['criteria']:
                    try:
                        achievement['criteria'] = json.loads(achievement['criteria'])
                    except json.JSONDecodeError:
                        print(f"Warning: Invalid JSON in criteria for achievement {achievement['id']}")
            
            return achievements
        finally:
            cursor.close()
            conn.close()
            
    @staticmethod
    def check_achievement_progress(user_id: int) -> List[Dict]:
        # Check progress for all achievements, award those that meet criteria, and return unearned achievements with progress data.
        db = Database()
        newly_awarded = []
        unearned_achievements = []
        
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT id, name, description, criteria, exp_reward, category
                FROM achievement_types
                ORDER BY category, id
            ''')
            
            all_achievements = cursor.fetchall()
            
            cursor.execute('''
                SELECT achievement_id
                FROM user_achievements
                WHERE user_id = %s
            ''', (user_id,))
            
            earned_achievements = {row['achievement_id'] for row in cursor.fetchall()}
            
            UserStats.refresh_user_stats(user_id)
            stats = UserStats.get_user_stats(user_id)
            
            for achievement in all_achievements:

                if achievement['id'] in earned_achievements:
                    continue
                    
                if not achievement['criteria']:
                    continue
                    
                criteria_json = achievement['criteria']
                criteria = json.loads(criteria_json) if criteria_json else {}
                achievement['criteria_obj'] = criteria 
                
                criteria_met = False
                current_count = 0
                required_count = 0

                criterion_type = criteria['type']
                
                if 'count' in criteria:
                    required_count = criteria['count']
                elif 'months' in criteria and criterion_type == 'account_age':
                    required_count = criteria['months']
                elif 'days' in criteria and criterion_type == 'login_streak':
                    required_count = criteria['days']
                else:
                    required_count = criteria.get('count', 0)
                if criterion_type in stats:
                    current_count = stats[criterion_type]
                    if current_count is None:
                        current_count = 0
                    criteria_met = current_count >= required_count
                
                progress_percentage = 0
                if required_count > 0:
                    progress_percentage = min(100, int((current_count / required_count) * 100))
                if criteria_met or progress_percentage == 100:

                    awarded = Achievements.award_achievement(user_id, achievement['id'])
                    if awarded:
                        newly_awarded.append(awarded)
                        continue
                
                progress_data = {
                    'id': achievement['id'],
                    'name': achievement['name'],
                    'description': achievement['description'],
                    'category': achievement['category'],
                    'criteria': criteria_json,  
                }
                
                progress_data.update(stats)
                
                unearned_achievements.append(progress_data)
            
            return unearned_achievements
        finally:
            cursor.close()
            conn.close()

achievements = Achievements() 
import sys
import os
import random
from datetime import datetime, timedelta
import mysql.connector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import Database

def create_achievement_tables_if_not_exist(cursor):
    """Create achievement-related tables if they don't exist"""
    print("Creating achievement tables if they don't exist...")
    
    # Create achievement_types table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `achievement_types` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `name` varchar(100) NOT NULL,
      `description` text DEFAULT NULL,
      `icon_name` varchar(50) DEFAULT NULL,
      `exp_reward` int(11) NOT NULL DEFAULT 0,
      `criteria` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`criteria`)),
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `category` varchar(50) DEFAULT NULL,
      PRIMARY KEY (`id`),
      KEY `idx_achievement_name` (`name`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    print("Achievement tables created or already exist")

def seed_achievement_data():
    """Seed data for achievement types with at least 2 per category"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        create_achievement_tables_if_not_exist(cursor)
        
        print("Starting achievement data seeding...")
        
        seed_achievement_types(cursor)
        
        conn.commit()
        print("Achievement data seeding completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

def seed_achievement_types(cursor):
    """Seed achievement types for all categories"""
    print("Seeding achievement types...")
    
    # Environmental action achievements
    environmental_achievements = [
        {
            'id': 1,
            'name': 'First Tree Planter',
            'description': 'Plant your first tree and begin your environmental journey',
            'icon_name': 'TreePine',
            'exp_reward': 100,
            'criteria': '{"type": "trees_planted", "count": 1}',
            'category': 'environmental_action'
        },
        {
            'id': 2,
            'name': 'Forest Guardian',
            'description': 'Plant 10 trees to help restore our forests',
            'icon_name': 'Forest',
            'exp_reward': 500,
            'criteria': '{"type": "trees_planted", "count": 10}',
            'category': 'environmental_action'
        },
        {
            'id': 3,
            'name': 'Carbon Reducer',
            'description': 'Offset your first kg of CO2 through participation',
            'icon_name': 'Cloud',
            'exp_reward': 150,
            'criteria': '{"type": "co2_offset", "count": 1}',
            'category': 'environmental_action'
        },
        {
            'id': 4,
            'name': 'Climate Champion',
            'description': 'Offset 100kg of CO2 through your environmental actions',
            'icon_name': 'CloudSun',
            'exp_reward': 750,
            'criteria': '{"type": "co2_offset", "count": 100}',
            'category': 'environmental_action'
        },
        {
            'id': 5,
            'name': 'First Volunteer',
            'description': 'Complete your first hour of environmental volunteering',
            'icon_name': 'Clock',
            'exp_reward': 120,
            'criteria': '{"type": "volunteer_hours", "count": 1}',
            'category': 'environmental_action'
        },
        {
            'id': 6,
            'name': 'Dedicated Volunteer',
            'description': 'Volunteer for 25 hours in environmental activities',
            'icon_name': 'ClockCheck',
            'exp_reward': 1000,
            'criteria': '{"type": "volunteer_hours", "count": 25}',
            'category': 'environmental_action'
        },
        {
            'id': 7,
            'name': 'Challenge Taker',
            'description': 'Complete your first environmental challenge',
            'icon_name': 'Flag',
            'exp_reward': 200,
            'criteria': '{"type": "challenges_completed", "count": 1}',
            'category': 'environmental_action'
        },
        {
            'id': 8,
            'name': 'Challenge Master',
            'description': 'Complete 10 environmental challenges',
            'icon_name': 'Award',
            'exp_reward': 800,
            'criteria': '{"type": "challenges_completed", "count": 10}',
            'category': 'environmental_action'
        }
    ]
    
    # Community engagement achievements
    community_achievements = [
        {
            'id': 9,
            'name': 'Event Participant',
            'description': 'Join your first environmental event',
            'icon_name': 'CalendarDays',
            'exp_reward': 100,
            'criteria': '{"type": "events_joined", "count": 1}',
            'category': 'community_engagement'
        },
        {
            'id': 10,
            'name': 'Event Enthusiast',
            'description': 'Participate in 5 environmental events',
            'icon_name': 'Calendar',
            'exp_reward': 300,
            'criteria': '{"type": "events_joined", "count": 5}',
            'category': 'community_engagement'
        },
        {
            'id': 11,
            'name': 'Event Organizer',
            'description': 'Create your first environmental event',
            'icon_name': 'CalendarPlus',
            'exp_reward': 200,
            'criteria': '{"type": "events_created", "count": 1}',
            'category': 'community_engagement'
        },
        {
            'id': 12,
            'name': 'Community Leader',
            'description': 'Create 3 environmental events',
            'icon_name': 'Users',
            'exp_reward': 500,
            'criteria': '{"type": "events_created", "count": 3}',
            'category': 'community_engagement'
        },
        {
            'id': 13,
            'name': 'Group Founder',
            'description': 'Create your first environmental group',
            'icon_name': 'UserPlus',
            'exp_reward': 200,
            'criteria': '{"type": "groups_created", "count": 1}',
            'category': 'community_engagement'
        },
        {
            'id': 14,
            'name': 'Forum Starter',
            'description': 'Create your first forum discussion',
            'icon_name': 'MessageSquare',
            'exp_reward': 100,
            'criteria': '{"type": "forum_discussions", "count": 1}',
            'category': 'community_engagement'
        },
        {
            'id': 15,
            'name': 'Forum Contributor',
            'description': 'Create 5 forum discussions',
            'icon_name': 'MessageCircle',
            'exp_reward': 400,
            'criteria': '{"type": "forum_discussions", "count": 5}',
            'category': 'community_engagement'
        },
        {
            'id': 16,
            'name': 'Conversation Starter',
            'description': 'Post your first forum reply',
            'icon_name': 'Reply',
            'exp_reward': 50,
            'criteria': '{"type": "forum_replies", "count": 1}',
            'category': 'community_engagement'
        },
        {
            'id': 17,
            'name': 'Active Commenter',
            'description': 'Post 25 forum replies',
            'icon_name': 'MessageSquarePlus',
            'exp_reward': 300,
            'criteria': '{"type": "forum_replies", "count": 25}',
            'category': 'community_engagement'
        },
        {
            'id': 18,
            'name': 'First Following',
            'description': 'Gain your first follower',
            'icon_name': 'Heart',
            'exp_reward': 50,
            'criteria': '{"type": "followers_count", "count": 1}',
            'category': 'community_engagement'
        },
        {
            'id': 19,
            'name': 'Community Influencer',
            'description': 'Gain 25 followers',
            'icon_name': 'Flame',
            'exp_reward': 500,
            'criteria': '{"type": "followers_count", "count": 25}',
            'category': 'community_engagement'
        }
    ]
    
    # Knowledge learning achievements
    knowledge_achievements = [
        {
            'id': 20,
            'name': 'First-time Learner',
            'description': 'Complete your first learning material',
            'icon_name': 'BookOpen',
            'exp_reward': 100,
            'criteria': '{"type": "learning_completed", "count": 1}',
            'category': 'knowledge_learning'
        },
        {
            'id': 21,
            'name': 'Knowledge Seeker',
            'description': 'Complete 10 learning materials',
            'icon_name': 'GraduationCap',
            'exp_reward': 500,
            'criteria': '{"type": "learning_completed", "count": 10}',
            'category': 'knowledge_learning'
        },
        {
            'id': 22,
            'name': 'Environmental Scholar',
            'description': 'Complete 25 learning materials',
            'icon_name': 'Diploma',
            'exp_reward': 1000,
            'criteria': '{"type": "learning_completed", "count": 25}',
            'category': 'knowledge_learning'
        },
        {
            'id': 23,
            'name': 'Curious Reader',
            'description': 'Read your first learning material',
            'icon_name': 'BookOpen',
            'exp_reward': 50,
            'criteria': '{"type": "materials_read", "count": 1}',
            'category': 'knowledge_learning'
        },
        {
            'id': 24,
            'name': 'Avid Reader',
            'description': 'Read 15 learning materials',
            'icon_name': 'Book',
            'exp_reward': 300,
            'criteria': '{"type": "materials_read", "count": 15}',
            'category': 'knowledge_learning'
        },
        {
            'id': 25,
            'name': 'First Comment',
            'description': 'Leave your first comment on a blog post',
            'icon_name': 'MessageCircle',
            'exp_reward': 75,
            'criteria': '{"type": "blog_comments", "count": 1}',
            'category': 'knowledge_learning'
        },
        {
            'id': 26,
            'name': 'Active Commenter',
            'description': 'Leave 10 comments on blog posts',
            'icon_name': 'MessageCirclePlus',
            'exp_reward': 300,
            'criteria': '{"type": "blog_comments", "count": 10}',
            'category': 'knowledge_learning'
        },
        {
            'id': 27,
            'name': 'First Post',
            'description': 'Create your first blog post',
            'icon_name': 'PenTool',
            'exp_reward': 100,
            'criteria': '{"type": "blog_posts", "count": 1}',
            'category': 'knowledge_learning'
        },
        {
            'id': 28,
            'name': 'Content Creator',
            'description': 'Create 5 blog posts',
            'icon_name': 'Edit',
            'exp_reward': 500,
            'criteria': '{"type": "blog_posts", "count": 5}',
            'category': 'knowledge_learning'
        }
    ]
    
    # Platform engagement achievements
    platform_achievements = [
        {
            'id': 29,
            'name': 'First Login',
            'description': 'Welcome to the community! Log in for the first time',
            'icon_name': 'LogIn',
            'exp_reward': 50,
            'criteria': '{"type": "login_count", "count": 1}',
            'category': 'platform_engagement'
        },
        {
            'id': 30,
            'name': 'Regular Visitor',
            'description': 'Log in 10 times',
            'icon_name': 'UserCheck',
            'exp_reward': 200,
            'criteria': '{"type": "login_count", "count": 10}',
            'category': 'platform_engagement'
        },
        {
            'id': 31,
            'name': 'Dedicated Member',
            'description': 'Log in 50 times',
            'icon_name': 'Medal',
            'exp_reward': 500,
            'criteria': '{"type": "login_count", "count": 50}',
            'category': 'platform_engagement'
        },
        {
            'id': 32,
            'name': 'One Week Streak',
            'description': 'Log in for 7 consecutive days',
            'icon_name': 'CalendarDays',
            'exp_reward': 200,
            'criteria': '{"type": "login_streak", "days": 7}',
            'category': 'platform_engagement'
        },
        {
            'id': 33,
            'name': 'Month-Long Streak',
            'description': 'Log in for 30 consecutive days',
            'icon_name': 'CalendarCheck',
            'exp_reward': 1000,
            'criteria': '{"type": "login_streak", "days": 30}',
            'category': 'platform_engagement'
        },
        {
            'id': 34,
            'name': 'One Month Member',
            'description': 'Be a member for 1 month',
            'icon_name': 'CalendarHeart',
            'exp_reward': 200,
            'criteria': '{"type": "account_age", "months": 1}',
            'category': 'platform_engagement'
        },
        {
            'id': 35,
            'name': 'Veteran Member',
            'description': 'Be a member for 6 months',
            'icon_name': 'Award',
            'exp_reward': 1000,
            'criteria': '{"type": "account_age", "months": 6}',
            'category': 'platform_engagement'
        }
    ]
    
    all_achievements = (
        environmental_achievements +
        community_achievements +
        knowledge_achievements +
        platform_achievements
    )
    
    for achievement in all_achievements:
        query = """
        INSERT IGNORE INTO achievement_types
        (id, name, description, icon_name, exp_reward, criteria, created_at, category)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        created_at = datetime.now() - timedelta(days=random.randint(1, 30))
        
        cursor.execute(query, (
            achievement['id'],
            achievement['name'],
            achievement['description'],
            achievement['icon_name'],
            achievement['exp_reward'],
            achievement['criteria'],
            created_at,
            achievement['category']
        ))
    
    print(f"Added {len(all_achievements)} achievement types")

if __name__ == "__main__":
    seed_achievement_data() 
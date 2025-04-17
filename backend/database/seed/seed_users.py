import sys
import os
import random
from datetime import datetime, timedelta
import mysql.connector
from werkzeug.security import generate_password_hash

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import Database

def create_users_table_if_not_exists(cursor):
    """Create users table if it doesn't exist"""
    print("Checking if users table exists...")
    
    # Create the users table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `users` (
      `id` bigint(20) NOT NULL AUTO_INCREMENT,
      `username` varchar(50) NOT NULL,
      `email` varchar(100) NOT NULL,
      `password_hash` varchar(255) NOT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `last_login` timestamp NULL DEFAULT NULL,
      `exp` int(11) DEFAULT 0,
      `level` int(11) DEFAULT 1,
      `group_id` int(11) DEFAULT NULL,
      `role` enum('user','moderator','admin') DEFAULT 'user',
      `bio` text DEFAULT NULL,
      `avatar_url` varchar(255) DEFAULT NULL,
      PRIMARY KEY (`id`),
      UNIQUE KEY `email` (`email`),
      UNIQUE KEY `username` (`username`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    print("Users table created or already exists")

def create_user_related_tables(cursor):
    """Create all user-related tables if they don't exist"""
    print("Creating user-related tables if they don't exist...")
    
    # Create user_followers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `user_followers` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `follower_id` bigint(20) NOT NULL,
      `followed_id` bigint(20) NOT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `follower_followed` (`follower_id`,`followed_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create user_achievements table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `user_achievements` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `user_id` bigint(20) NOT NULL,
      `achievement_id` int(11) NOT NULL,
      `earned_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `user_achievement` (`user_id`,`achievement_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create user_activities table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `user_activities` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `user_id` bigint(20) NOT NULL,
      `activity_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`activity_data`)),
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `activity_type` text DEFAULT NULL,
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create user_logins table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `user_logins` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `user_id` bigint(20) NOT NULL,
      `login_time` timestamp NOT NULL DEFAULT current_timestamp(),
      `ip_address` varchar(45) DEFAULT NULL,
      `user_agent` text DEFAULT NULL,
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create user_stats table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `user_stats` (
      `user_id` bigint(20) NOT NULL,
      `stats_data` JSON NOT NULL,
      `last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`user_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create user_challenges table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `user_challenges` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `user_id` bigint(20) NOT NULL,
      `challenge_id` int(11) NOT NULL,
      `status` enum('in_progress','completed','failed') DEFAULT 'in_progress',
      `progress` int(11) DEFAULT 0,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `completed_at` timestamp NULL DEFAULT NULL,
      PRIMARY KEY (`id`),
      UNIQUE KEY `user_challenge` (`user_id`,`challenge_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `notifications` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `user_id` bigint(20) NOT NULL,
    `type` varchar(50) NOT NULL,
    `title` varchar(255) NOT NULL,
    `content` text NOT NULL,
    `link` varchar(255) DEFAULT NULL,
    `is_read` tinyint(1) DEFAULT 0,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """)
    
    print("User-related tables created or already exist")

def seed_users():
    """Seed users data with incremental IDs and different roles"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        create_users_table_if_not_exists(cursor)
        create_user_related_tables(cursor)
        
        print("Starting user data seeding...")
        
        users = [
            # Admin user
            {
                'id': 1,
                'username': 'admin_user',
                'email': 'admin@greenbuddy.com',
                'password': 'Admin123!',  # Will be hashed
                'role': 'admin',
                'bio': 'System administrator for Green Buddy platform',
                'avatar_url': 'https://randomuser.me/api/portraits/men/1.jpg'
            },
            # Moderator users
            {
                'id': 2,
                'username': 'mod_sarah',
                'email': 'sarah@greenbuddy.com',
                'password': 'Mod123!',  # Will be hashed
                'role': 'moderator',
                'bio': 'Environmental science graduate and community moderator',
                'avatar_url': 'https://randomuser.me/api/portraits/women/2.jpg'
            },
            {
                'id': 3,
                'username': 'mod_david',
                'email': 'david@greenbuddy.com',
                'password': 'Mod123!',  # Will be hashed
                'role': 'moderator',
                'bio': 'Conservation biologist and content moderator',
                'avatar_url': 'https://randomuser.me/api/portraits/men/3.jpg'
            },
            # Regular users
            {
                'id': 4,
                'username': 'eco_alex',
                'email': 'alex@example.com',
                'password': 'User123!',  # Will be hashed
                'role': 'user',
                'bio': 'Passionate about renewable energy and sustainability',
                'avatar_url': 'https://randomuser.me/api/portraits/women/4.jpg'
            },
            {
                'id': 5,
                'username': 'green_mike',
                'email': 'mike@example.com',
                'password': 'User123!',  # Will be hashed
                'role': 'user',
                'bio': 'Urban gardener and composting enthusiast',
                'avatar_url': 'https://randomuser.me/api/portraits/men/5.jpg'
            },
            {
                'id': 6,
                'username': 'earth_lisa',
                'email': 'lisa@example.com',
                'password': 'User123!',  # Will be hashed
                'role': 'user',
                'bio': 'Zero waste advocate and community organizer',
                'avatar_url': 'https://randomuser.me/api/portraits/women/6.jpg'
            }
        ]
        
        for user in users:

            #Scrypt
            password_hash = generate_password_hash(user['password'])
            created_at = datetime.now() - timedelta(days=random.randint(7, 90))
            last_login = None
            if random.random() < 0.7:
                last_login = created_at + timedelta(days=random.randint(1, 7))
            
            exp = random.randint(100, 2000)
            level = max(1, exp // 1000)
            
            query = """
            INSERT IGNORE INTO users 
            (id, username, email, password_hash, created_at, last_login, exp, level, role, bio, avatar_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                user['id'],
                user['username'],
                user['email'],
                password_hash,
                created_at,
                last_login,
                exp,
                level,
                user['role'],
                user['bio'],
                user['avatar_url']
            ))
            
            print(f"Added user: {user['username']} (role: {user['role']})")
        
        conn.commit()
        print(f"Successfully seeded {len(users)} users!")
        
        print("\n--- LOGIN CREDENTIALS ---")
        print("Admin User:")
        print("  Username: admin_user")
        print("  Email: admin@greenbuddy.com")
        print("  Password: Admin123!")
        
        print("\nModerator Users:")
        print("  Username: mod_sarah")
        print("  Email: sarah@greenbuddy.com")
        print("  Password: Mod123!")
        
        print("  Username: mod_david")
        print("  Email: david@greenbuddy.com")
        print("  Password: Mod123!")
        
        print("\nRegular Users:")
        print("  Username: eco_alex")
        print("  Email: alex@example.com")
        print("  Password: User123!")
        
        print("  Username: green_mike")
        print("  Email: mike@example.com")
        print("  Password: User123!")
        
        print("  Username: earth_lisa")
        print("  Email: lisa@example.com")
        print("  Password: User123!")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

# User login credentials:
# 1. Admin user:
#    - Username: admin_user
#    - Email: admin@greenbuddy.com
#    - Password: Admin123!
#
# 2. Moderator users:
#    - Username: mod_sarah
#    - Email: sarah@greenbuddy.com
#    - Password: Mod123!
#
#    - Username: mod_david
#    - Email: david@greenbuddy.com
#    - Password: Mod123!
#
# 3. Regular users:
#    - Username: eco_alex
#    - Email: alex@example.com
#    - Password: User123!
#
#    - Username: green_mike
#    - Email: mike@example.com
#    - Password: User123!
#
#    - Username: earth_lisa
#    - Email: lisa@example.com
#    - Password: User123!

if __name__ == "__main__":
    seed_users() 
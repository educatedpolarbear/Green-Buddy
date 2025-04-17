import sys
import os
import random
from datetime import datetime, timedelta
import mysql.connector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import Database

def create_group_tables_if_not_exist(cursor):
    """Create all group-related tables if they don't exist"""
    print("Creating group tables if they don't exist...")
    
    # Create groups table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `groups` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `name` varchar(255) NOT NULL,
      `description` text DEFAULT NULL,
      `creator_id` bigint(20) NOT NULL,
      `image_url` varchar(255) DEFAULT NULL,
      `member_count` int(11) DEFAULT 0,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `is_private` tinyint(1) DEFAULT 0,
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create group_members table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `group_members` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `group_id` int(11) NOT NULL,
      `user_id` bigint(20) NOT NULL,
      `role` enum('member','admin') DEFAULT 'member',
      `joined_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `group_user` (`group_id`,`user_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create group_posts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `group_posts` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `group_id` int(11) NOT NULL,
      `author_id` bigint(20) NOT NULL,
      `content` text NOT NULL,
      `image_url` varchar(255) DEFAULT NULL,
      `likes_count` int(11) DEFAULT 0,
      `comments_count` int(11) DEFAULT 0,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`),
      KEY `group_id` (`group_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create group_comments table
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `group_comments` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `group_post_id` int(11) NOT NULL,
      `author_id` bigint(20) NOT NULL,
      `content` text NOT NULL,
      `likes_count` int(11) DEFAULT 0,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create group_chat_messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `group_chat_messages` (
      `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `group_id` int(11) NOT NULL,
    `author_id` bigint(20) NOT NULL,
  `content` text NOT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      KEY `group_id` (`group_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    print("Group tables created or already exist")

def seed_group_data():
    """Seed data for group-related tables"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        create_group_tables_if_not_exist(cursor)
        
        print("Starting group data seeding...")
        
        seed_groups(cursor)
        seed_group_admins(cursor)
        seed_group_posts(cursor)
        seed_group_comments(cursor)
        
        conn.commit()
        print("Group data seeding completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

def seed_groups(cursor):
    """Seed groups table"""
    print("Seeding groups...")
    
    groups = [
        {
            'name': 'Sustainable Living Collective',
            'description': 'A community of people committed to living sustainably and reducing their environmental footprint. Share tips, challenges, and successes in your sustainability journey.',
            'creator_id': 1,
            'image_url': 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80',
            'is_private': 0
        },
        {
            'name': 'Urban Gardeners Network',
            'description': 'Connect with fellow urban gardeners to share knowledge, exchange seeds, and celebrate the joys of growing food in city spaces.',
            'creator_id': 2,
            'image_url': 'https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80',
            'is_private': 0
        },
        {
            'name': 'Climate Action Alliance',
            'description': 'A group dedicated to organizing and taking action against climate change. Coordinate events, share resources, and work together for a healthier planet.',
            'creator_id': 3,
            'image_url': 'https://images.unsplash.com/photo-1534430480872-3498386e7856?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80',
            'is_private': 0
        },
        {
            'name': 'Zero Waste Community',
            'description': 'Striving for a zero waste lifestyle? Join us to share tips, DIY projects, and solutions for reducing waste in your daily life.',
            'creator_id': 4,
            'image_url': 'https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80',
            'is_private': 0
        },
        {
            'name': 'Renewable Energy Enthusiasts',
            'description': 'Discuss the latest in renewable energy technologies, share your home energy projects, and collaborate on community renewable initiatives.',
            'creator_id': 5,
            'image_url': 'https://images.unsplash.com/photo-1473448912268-2022ce9509d8?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1441&q=80',
            'is_private': 0
        }
    ]
    
    for i, group in enumerate(groups, 1):
        
        try:
            created_at = datetime.now() - timedelta(days=random.randint(30, 120))
            
            query = """
            INSERT IGNORE INTO groups
            (id, name, description, creator_id, image_url, member_count, created_at, is_private)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                i,
                group['name'],
                group['description'],
                group['creator_id'],
                group['image_url'],
                0, 
                created_at,
                group['is_private']
            ))
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
    
    print(f"Added {cursor.rowcount} groups.")

def seed_group_admins(cursor):
    """Seed group creators as members with admin role"""
    print("Seeding group admins...")
    
    cursor.execute("SELECT id, creator_id FROM groups")
    groups = cursor.fetchall()
    
    admin_entries = []
    member_id = 1
    
    for group_id, creator_id in groups:
        joined_at = datetime.now() - timedelta(days=random.randint(30, 120))
        admin_entries.append((member_id, group_id, creator_id, 'admin', joined_at))
        member_id += 1
    
    if admin_entries:
        query = """
        INSERT IGNORE INTO group_members
        (id, group_id, user_id, role, joined_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.executemany(query, admin_entries)
        print(f"Added {cursor.rowcount} group admins.")
        
        for group_id, _ in groups:
            cursor.execute("""
            UPDATE groups 
            SET member_count = (SELECT COUNT(*) FROM group_members WHERE group_id = %s)
            WHERE id = %s
            """, (group_id, group_id))
    else:
        print("No group admins to add.")

def seed_group_posts(cursor):
    """Seed group posts table"""
    print("Seeding group posts...")
    
    post_contents = [
        "Just shared a new resource on sustainable living practices. Check it out and let me know your thoughts!",
        "Looking for recommendations on eco-friendly products that actually work. What has everyone been using lately?",
        "Excited to announce our upcoming community event! Save the date and join us for a day of learning and action.",
        "Question for the group: What's been your biggest challenge in adopting more sustainable habits?",
        "Sharing my latest project - managed to reduce my household waste by 50% this month! Here's how I did it...",
        "Just discovered an amazing local initiative that aligns with our values. Has anyone else heard about this?",
        "Weekly reminder to track your carbon footprint! Even small changes can make a big difference.",
        "Need advice: I'm trying to set up a rainwater collection system. Any tips from those who've done it?",
        "Celebration post: Our community garden just produced its first harvest! So grateful for this group's support.",
        "Important policy update that affects our environmental goals. Let's discuss how we can respond effectively."
    ]
    
    image_urls = [
        "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
        "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
        "https://images.unsplash.com/photo-1466611653911-95081537e5b7?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
        "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
        None,
        None
    ]
    
    # Generate posts for each group
    group_posts = []
    post_id = 1
    
    cursor.execute("SELECT id FROM groups")
    group_ids = [row[0] for row in cursor.fetchall()]
    
    for group_id in group_ids:
        num_posts = random.randint(2, 4)
        
        for _ in range(num_posts):
            cursor.execute("SELECT creator_id FROM groups WHERE id = %s", (group_id,))
            creator_id = cursor.fetchone()[0]
            
            author_id = creator_id if random.random() < 0.6 else random.randint(1, 5)
            
            content = random.choice(post_contents)
            image_url = random.choice(image_urls)
            created_at = datetime.now() - timedelta(days=random.randint(1, 60))
            
            group_posts.append((post_id, group_id, author_id, content, image_url, created_at))
            post_id += 1
    
    if group_posts:
        query = """
        INSERT IGNORE INTO group_posts
        (id, group_id, author_id, content, image_url, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(query, group_posts)
        print(f"Added {cursor.rowcount} group posts.")
    else:
        print("No group posts to add.")

def seed_group_comments(cursor):
    """Seed group comments table"""
    print("Seeding group comments...")
    
    comment_contents = [
        "Thanks for sharing! This is really helpful information.",
        "I've been thinking about this too. Great to see others are interested.",
        "Count me in for the event! Looking forward to it.",
        "This is exactly what our community needs right now.",
        "I tried something similar and had great results!",
        "Has anyone found a solution to the challenge mentioned?",
        "Would love to learn more about how to implement this.",
        "This inspires me to make changes in my own habits.",
        "Great point! I hadn't considered that perspective before.",
        "Let's organize a meeting to discuss this further."
    ]
    
    cursor.execute("SELECT id FROM group_posts")
    post_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate comments for posts
    group_comments = []
    comment_id = 1
    
    for post_id in post_ids:
        num_comments = random.randint(0, 3)
        
        for _ in range(num_comments):
            author_id = random.randint(1, 5) 
            content = random.choice(comment_contents)
            created_at = datetime.now() - timedelta(days=random.randint(1, 30))
            
            group_comments.append((comment_id, post_id, author_id, content, created_at))
            comment_id += 1
    
    if group_comments:
        query = """
        INSERT IGNORE INTO group_comments
        (id, group_post_id, author_id, content, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.executemany(query, group_comments)
        print(f"Added {cursor.rowcount} group comments.")
    else:
        print("No group comments to add.")

if __name__ == "__main__":
    seed_group_data() 
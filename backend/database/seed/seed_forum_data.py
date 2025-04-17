import sys
import os
import random
from datetime import datetime, timedelta
import mysql.connector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import Database

def create_forum_tables_if_not_exist(cursor):
    """Create all forum-related tables if they don't exist"""
    print("Creating forum tables if they don't exist...")
    
    # Create forum_categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `forum_categories` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `name` varchar(100) NOT NULL,
      `description` text DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create forum_discussions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `forum_discussions` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `title` varchar(255) NOT NULL,
      `content` text NOT NULL,
      `excerpt` text DEFAULT NULL,
      `author_id` bigint(20) NOT NULL,
      `category_id` int(11) NOT NULL,
      `views_count` int(11) DEFAULT 0,
      `likes_count` int(11) DEFAULT 0,
      `replies_count` int(11) DEFAULT 0,
      `has_solution` tinyint(1) DEFAULT 0,
      `status` enum('open','closed','deleted') DEFAULT 'open',
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create forum_replies table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `forum_replies` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `discussion_id` int(11) NOT NULL,
      `author_id` bigint(20) NOT NULL,
      `content` text NOT NULL,
      `likes_count` int(11) DEFAULT 0,
      `is_solution` tinyint(1) DEFAULT 0,
      `parent_id` int(11) DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`),
      KEY `discussion_id` (`discussion_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create forum_likes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `forum_likes` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `user_id` bigint(20) NOT NULL,
      `discussion_id` int(11) DEFAULT NULL,
      `reply_id` int(11) DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `user_discussion` (`user_id`,`discussion_id`),
      UNIQUE KEY `user_reply` (`user_id`,`reply_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    

def seed_forum_data():
    """Seed data for forum-related tables"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        create_forum_tables_if_not_exist(cursor)
        
        print("Starting forum data seeding...")
        
        seed_forum_categories(cursor)
        seed_forum_discussions(cursor)        
        seed_forum_replies(cursor)
        seed_forum_likes(cursor)
        
        conn.commit()
        print("Forum data seeding completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

def seed_forum_categories(cursor):
    """Seed forum categories table"""
    print("Seeding forum categories...")
    
    categories = [
        {
            'id': 1,
            'name': 'General Discussion',
            'description': 'General discussions about environmental topics'
        },
        {
            'id': 2,
            'name': 'Tips & Tricks',
            'description': 'Share and learn eco-friendly tips'
        },
        {
            'id': 3,
            'name': 'Events',
            'description': 'Discuss upcoming environmental events'
        },
        {
            'id': 4,
            'name': 'Projects',
            'description': 'Share and collaborate on green projects'
        },
        {
            'id': 5,
            'name': 'News',
            'description': 'Discuss environmental news and updates'
        }
    ]
    
    for category in categories:
        query = """
        INSERT IGNORE INTO forum_categories 
        (id, name, description)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (
            category['id'],
            category['name'],
            category['description']
        ))
    
    print(f"Added {cursor.rowcount} forum categories.")

def seed_forum_discussions(cursor):
    """Seed forum discussions table"""
    print("Seeding forum discussions...")
    
    discussions = [
        {
            'title': 'Sustainable Transportation Options',
            'content': '<p>What sustainable transportation options do you use in your daily life? I\'ve been trying to reduce my carbon footprint by biking to work, but I\'m looking for other ideas for longer commutes.</p>',
            'excerpt': 'What sustainable transportation options do you use in your daily life? I\'ve been trying to reduce my carbon footprint by biking to work.',
            'author_id': 1,
            'category_id': 1
        },
        {
            'title': 'Zero-Waste Kitchen Tips',
            'content': '<p>I\'m trying to create a zero-waste kitchen. So far I\'ve switched to reusable containers, composting, and buying in bulk. What are your best tips for reducing kitchen waste?</p>',
            'excerpt': 'I\'m trying to create a zero-waste kitchen. So far I\'ve switched to reusable containers, composting, and buying in bulk.',
            'author_id': 2,
            'category_id': 2
        },
        {
            'title': 'Climate Change Documentary Recommendations',
            'content': '<p>I recently watched "An Inconvenient Truth" and found it very informative. Can anyone recommend other good documentaries about climate change and environmental issues?</p>',
            'excerpt': 'I recently watched "An Inconvenient Truth" and found it very informative. Can anyone recommend other good documentaries?',
            'author_id': 3,
            'category_id': 1
        },
        {
            'title': 'Urban Gardening in Small Spaces',
            'content': '<p>I live in an apartment with a small balcony and want to start growing some of my own food. Has anyone had success with urban gardening in limited spaces? What plants work best?</p>',
            'excerpt': 'I live in an apartment with a small balcony and want to start growing some of my own food. Has anyone had success with urban gardening?',
            'author_id': 4,
            'category_id': 4
        },
        {
            'title': 'Energy-Saving Home Improvements',
            'content': '<p>I\'m planning some home renovations with a focus on energy efficiency. What improvements have given you the best results in terms of reducing energy consumption and costs?</p>',
            'excerpt': 'I\'m planning some home renovations with a focus on energy efficiency. What improvements have given you the best results?',
            'author_id': 5,
            'category_id': 2
        },
        {
            'title': 'Local Environmental Cleanup Events',
            'content': '<p>I\'m interested in participating in local cleanup events. Does anyone know of any upcoming opportunities or organizations that coordinate these kinds of activities?</p>',
            'excerpt': 'I\'m interested in participating in local cleanup events. Does anyone know of any upcoming opportunities?',
            'author_id': 1,
            'category_id': 3
        },
        {
            'title': 'Recycling Confusion: What Can Actually Be Recycled?',
            'content': '<p>I\'m often confused about what can and cannot be recycled in my area. Some plastics have recycling symbols but aren\'t accepted. Does anyone have tips for navigating recycling guidelines?</p>',
            'excerpt': 'I\'m often confused about what can and cannot be recycled in my area. Some plastics have recycling symbols but aren\'t accepted.',
            'author_id': 2,
            'category_id': 2
        },
        {
            'title': 'Recent Climate Policy Changes',
            'content': '<p>I\'d like to discuss the recent climate policy changes announced by the government. What are your thoughts on their effectiveness and implementation timeline?</p>',
            'excerpt': 'I\'d like to discuss the recent climate policy changes announced by the government. What are your thoughts on their effectiveness?',
            'author_id': 3,
            'category_id': 5
        },
        {
            'title': 'Sustainable Fashion Brands',
            'content': '<p>I\'m trying to make more ethical choices with my clothing purchases. Can anyone recommend sustainable and ethical fashion brands that don\'t break the bank?</p>',
            'excerpt': 'I\'m trying to make more ethical choices with my clothing purchases. Can anyone recommend sustainable and ethical fashion brands?',
            'author_id': 4,
            'category_id': 2
        },
        {
            'title': 'Starting a Neighborhood Compost Program',
            'content': '<p>I\'m considering starting a neighborhood composting program. Has anyone done this successfully? What were the challenges and benefits?</p>',
            'excerpt': 'I\'m considering starting a neighborhood composting program. Has anyone done this successfully? What were the challenges and benefits?',
            'author_id': 5,
            'category_id': 4
        }
    ]
    
    for i, discussion in enumerate(discussions, 1):
        created_at = datetime.now() - timedelta(days=random.randint(1, 60))
        
        query = """
        INSERT IGNORE INTO forum_discussions
        (id, title, content, excerpt, author_id, category_id, views_count, likes_count, replies_count, has_solution, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            i,
            discussion['title'],
            discussion['content'],
            discussion['excerpt'],
            discussion['author_id'],
            discussion['category_id'],
            random.randint(0, 100),  # Random view count
            0,  # Likes count starts at 0
            0,  # Replies count starts at 0
            0,  # Initially no solution
            'open',
            created_at
        ))
    
    print(f"Added {cursor.rowcount} forum discussions.")

def seed_forum_replies(cursor):
    """Seed forum replies table"""
    print("Seeding forum replies...")
    
    cursor.execute("SELECT id FROM forum_discussions")
    discussion_ids = [row[0] for row in cursor.fetchall()]
    
    replies = [
        "<p>This is a great topic! I've been wondering about this too.</p>",
        "<p>Thanks for bringing this up. I think it's important for our community to discuss.</p>",
        "<p>I've had some experience with this. The key thing I learned is to start small and be consistent.</p>",
        "<p>Have you considered trying a different approach? I found that X worked better than Y for me.</p>",
        "<p>Here's a resource that might help: [link]</p>",
        "<p>I disagree with some points here. In my experience, the reality is more complex.</p>",
        "<p>This has been discussed before, but I think we need fresh perspectives on it.</p>",
        "<p>I'm following this thread with interest. Please keep us updated on your progress!</p>",
        "<p>I can share what worked for me, but your situation might be different.</p>",
        "<p>The research on this topic suggests that multiple factors are at play.</p>",
        "<p>I'd recommend talking to local experts who can provide more context-specific advice.</p>",
        "<p>This is something I'm passionate about too. Happy to connect offline to discuss more.</p>"
    ]
    
    forum_replies = []
    reply_id = 1
    
    for discussion_id in discussion_ids:
        num_replies = random.randint(0, 3)
        
        for _ in range(num_replies):
            author_id = random.randint(1, 5)
            content = random.choice(replies)
            created_at = datetime.now() - timedelta(days=random.randint(1, 30))
            is_solution = 1 if random.random() < 0.2 else 0
            
            forum_replies.append((reply_id, discussion_id, author_id, content, 0, is_solution, created_at))
            reply_id += 1
    
    if forum_replies:
        query = """
        INSERT IGNORE INTO forum_replies
        (id, discussion_id, author_id, content, likes_count, is_solution, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(query, forum_replies)
        print(f"Added {cursor.rowcount} forum replies.")
        
        for reply_id, discussion_id, _, _, _, is_solution, _ in forum_replies:
            if is_solution:
                cursor.execute(
                    "UPDATE forum_discussions SET has_solution = 1 WHERE id = %s",
                    (discussion_id,)
                )
        
        cursor.execute("""
        UPDATE forum_discussions d
        SET replies_count = (
            SELECT COUNT(*) FROM forum_replies r WHERE r.discussion_id = d.id
        )
        """)
    else:
        print("No forum replies to add.")

def seed_forum_likes(cursor):
    """Seed forum likes table"""
    print("Seeding forum likes...")
    
    cursor.execute("SELECT id FROM forum_discussions")
    discussion_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM forum_replies")
    reply_ids = [row[0] for row in cursor.fetchall()]
    
    forum_likes = []
    like_id = 1
    
    # Likes for discussions
    for discussion_id in discussion_ids:
        # Each discussion gets 0-5 likes
        num_likes = random.randint(0, 5)
        user_ids = random.sample(range(1, 6), min(num_likes, 5))  
        
        for user_id in user_ids:
            created_at = datetime.now() - timedelta(days=random.randint(1, 20))
            forum_likes.append((like_id, user_id, discussion_id, None, created_at))
            like_id += 1
    
    # Likes for replies
    for reply_id in reply_ids:
        # Each reply gets 0-3 likes
        num_likes = random.randint(0, 3)
        user_ids = random.sample(range(1, 6), min(num_likes, 5))
        
        for user_id in user_ids:
            created_at = datetime.now() - timedelta(days=random.randint(1, 20))
            forum_likes.append((like_id, user_id, None, reply_id, created_at))
            like_id += 1
    
    if forum_likes:
        query = """
        INSERT IGNORE INTO forum_likes
        (id, user_id, discussion_id, reply_id, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.executemany(query, forum_likes)
        print(f"Added {cursor.rowcount} forum likes.")
        
        cursor.execute("""
        UPDATE forum_discussions d
        SET likes_count = (
            SELECT COUNT(*) FROM forum_likes l WHERE l.discussion_id = d.id
        )
        """)
        
        cursor.execute("""
        UPDATE forum_replies r
        SET likes_count = (
            SELECT COUNT(*) FROM forum_likes l WHERE l.reply_id = r.id
        )
        """)
    else:
        print("No forum likes to add.")

if __name__ == "__main__":
    seed_forum_data() 
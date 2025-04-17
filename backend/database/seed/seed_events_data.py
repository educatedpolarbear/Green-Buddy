import sys
import os
import random
from datetime import datetime, timedelta
import mysql.connector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import Database

def create_event_tables_if_not_exist(cursor):
    """Create all event-related tables if they don't exist"""
    print("Creating event tables if they don't exist...")
    
    # Create event_categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `event_categories` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `name` varchar(100) NOT NULL,
      `description` text DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `events` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `title` varchar(255) NOT NULL,
      `description` text NOT NULL,
      `location` varchar(255) NOT NULL,
      `latitude` decimal(10,8) DEFAULT NULL,
      `longitude` decimal(11,8) DEFAULT NULL,
      `start_date` datetime NOT NULL,
      `end_date` datetime NOT NULL,
      `registration_deadline` datetime DEFAULT NULL,
      `image_url` varchar(255) DEFAULT NULL,
      `organizer_id` bigint(20) NOT NULL,
      `category_id` int(11) NOT NULL,
      `participants_count` int(11) DEFAULT 0,
      `max_participants` int(11) DEFAULT NULL,
      `requirements` text DEFAULT NULL,
      `schedule` text DEFAULT NULL,
      `status` enum('draft','published','cancelled','completed') DEFAULT 'published',
      `co2_offset` decimal(10,2) DEFAULT 0.00,
      `trees_planted` int(11) DEFAULT 0,
      `volunteer_hour` decimal(10,2) DEFAULT 0.00,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`),
      KEY `organizer_id` (`organizer_id`),
      KEY `category_id` (`category_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create event_participants table
    cursor.execute("""  
    CREATE TABLE IF NOT EXISTS `event_participants` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `event_id` int(11) NOT NULL,
    `user_id` bigint(20) NOT NULL,
    `registered_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `event_user` (`event_id`,`user_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create event_comments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `event_comments` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `event_id` int(11) NOT NULL,
      `user_id` bigint(20) NOT NULL,
      `content` text NOT NULL,
      `parent_id` int(11) DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      KEY `event_id` (`event_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create event_votes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `event_votes` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `event_id` int(11) NOT NULL,
      `user_id` bigint(20) NOT NULL,
      `vote_type` enum('interested','going') NOT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `event_user_vote` (`event_id`,`user_id`,`vote_type`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    print("Event tables created or already exist")

def seed_events_data():
    """Seed data for events-related tables"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        create_event_tables_if_not_exist(cursor)
        
        print("Starting events data seeding...")
        
        seed_event_categories(cursor)
        seed_events(cursor)
        seed_event_comments(cursor)
        
        conn.commit()
        print("Events data seeding completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

def seed_event_categories(cursor):
    """Seed event categories table"""
    print("Seeding event categories...")
    
    categories = [
        {
            'id': 1,
            'name': 'Tree Planting',
            'description': 'Plant trees'
        },
        {
            'id': 2,
            'name': 'Clean Up',
            'description': 'Community Cleanup'
        },
        {
            'id': 3,
            'name': 'Workshop',
            'description': 'Educational workshops about sustainability'
        },
        {
            'id': 4,
            'name': 'Conservation',
            'description': 'Wildlife and habitat conservation'
        },
        {
            'id': 5,
            'name': 'Recycling',
            'description': 'Recycling and waste reduction initiatives'
        }
    ]
    
    for category in categories:
        query = """
        INSERT IGNORE INTO event_categories 
        (id, name, description)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (
            category['id'],
            category['name'],
            category['description']
        ))
    
    print(f"Added {cursor.rowcount} event categories.")

def seed_events(cursor):
    """Seed events table"""
    print("Seeding events...")
    
    locations = [
        "Central Park, New York, NY",
        "Golden Gate Park, San Francisco, CA",
        "Lincoln Park, Chicago, IL",
        "Griffith Park, Los Angeles, CA",
        "Boston Common, Boston, MA",
        "Piedmont Park, Atlanta, GA",
        "Fairmount Park, Philadelphia, PA",
        "Discovery Green, Houston, TX",
        "Gas Works Park, Seattle, WA",
        "Balboa Park, San Diego, CA"
    ]
    
    image_urls = [
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80",
        "https://images.unsplash.com/photo-1472851294608-062f824d29cc?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80",
        "https://plus.unsplash.com/premium_photo-1681885143542-dc9303b9775d?fm=jpg&q=60&w=3000&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTd8fHN1c3RhaW5hYmxlJTIwbGl2aW5nfGVufDB8fDB8fHww",
        "https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80",
        "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80",
        "https://images.unsplash.com/photo-1600880292089-90a7e086ee0c?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=687&q=80",
        "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1441&q=80",
        "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80",
        "https://images.unsplash.com/photo-1472145246862-b24cf25c4a36?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1471&q=80",
        "https://images.unsplash.com/photo-1617718295766-0f839c2853f7?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=687&q=80"
    ]
    
    events = [
        {
            'title': 'Community Tree Planting Day',
            'description': 'Join us for a day of planting trees to make our neighborhood greener and combat climate change. No experience necessary - we will provide tools and guidance!',
            'category_id': 1,  # Tree Planting
            'organizer_id': 1,
            'max_participants': 50,
            'requirements': 'Wear comfortable clothes and closed-toe shoes. Bring water and sun protection. Tools will be provided.',
            'schedule': '9:00 AM - Welcome and instructions\n10:00 AM - Tree planting begins\n12:00 PM - Lunch break\n1:00 PM - Continue planting\n3:00 PM - Cleanup and closing remarks',
            'status': 'published',
            'co2_offset': 5.8,
            'trees_planted': 25,
            'volunteer_hour': 4
        },
        {
            'title': 'Beach Cleanup Initiative',
            'description': 'Help us clean the shoreline and protect marine wildlife from plastic pollution. Together we can make a difference for our oceans.',
            'category_id': 2,  # Clean Up
            'organizer_id': 2,
            'max_participants': 100,
            'requirements': 'Bring gloves if you have them. Wear sun protection. Trash bags and pickup tools will be provided.',
            'schedule': '8:00 AM - Registration and equipment distribution\n8:30 AM - Cleanup begins\n11:30 AM - Collection and weighing of trash\n12:00 PM - Thank you and refreshments',
            'status': 'published',
            'co2_offset': 2.3,
            'trees_planted': 0,
            'volunteer_hour': 4
        },
        {
            'title': 'Sustainable Living Workshop',
            'description': 'Learn practical skills for living more sustainably at home. Topics include energy conservation, waste reduction, and eco-friendly product choices.',
            'category_id': 3,  # Workshop
            'organizer_id': 3,
            'max_participants': 30,
            'requirements': 'Bring a notebook and pen. Optional: bring examples of challenging waste items from your home for discussion.',
            'schedule': '6:00 PM - Introduction to sustainability principles\n6:30 PM - Energy conservation workshop\n7:15 PM - Waste reduction strategies\n8:00 PM - Q&A and networking',
            'status': 'published',
            'co2_offset': 1.5,
            'trees_planted': 0,
            'volunteer_hour': 2
        },
        {
            'title': 'River Cleanup Project',
            'description': 'Join our effort to clean up the local river and improve water quality. This event will help protect aquatic wildlife and improve recreational areas.',
            'category_id': 2,  # Clean Up
            'organizer_id': 1,
            'max_participants': 75,
            'requirements': 'Wear boots or shoes that can get wet. Bring work gloves if you have them. All cleanup supplies will be provided.',
            'schedule': '9:00 AM - Safety briefing and equipment distribution\n9:30 AM - Cleanup begins\n12:30 PM - Lunch break\n1:30 PM - Continue cleanup\n3:30 PM - Wrap-up and discussion of impacts',
            'status': 'published',
            'co2_offset': 3.2,
            'trees_planted': 0,
            'volunteer_hour': 6.5
        },
        {
            'title': 'Urban Garden Planning Workshop',
            'description': 'Learn how to plan and create an urban garden in small spaces. Perfect for apartment dwellers and those with limited outdoor space.',
            'category_id': 3,  # Workshop
            'organizer_id': 4,
            'max_participants': 25,
            'requirements': 'No special requirements. All materials and handouts will be provided.',
            'schedule': '10:00 AM - Introduction to urban gardening\n10:45 AM - Container gardening techniques\n11:30 AM - Plant selection for small spaces\n12:15 PM - Q&A and resource sharing',
            'status': 'published',
            'co2_offset': 0.8,
            'trees_planted': 0,
            'volunteer_hour': 2.5
        },
        {
            'title': 'Neighborhood Beautification Project',
            'description': 'Help beautify our community by planting flowers, picking up litter, and creating public art. A fun event for the whole family!',
            'category_id': 2,  # Clean Up
            'organizer_id': 5,
            'max_participants': 60,
            'requirements': 'Wear clothes that can get dirty. Bring gardening gloves if you have them.',
            'schedule': '10:00 AM - Check-in and project assignments\n10:30 AM - Work begins\n12:30 PM - Lunch and community social\n1:30 PM - Continue projects\n3:30 PM - Celebration and photos',
            'status': 'published',
            'co2_offset': 1.7,
            'trees_planted': 0,
            'volunteer_hour': 5
        },
        {
            'title': 'Wildlife Habitat Restoration',
            'description': 'Help restore natural habitat for local wildlife by removing invasive species and planting native plants. Learn about local ecosystems while making a real difference.',
            'category_id': 4,  # Conservation
            'organizer_id': 2,
            'max_participants': 40,
            'requirements': 'Wear long pants and closed-toe shoes. Bring water and sun protection. Tools and gloves will be provided.',
            'schedule': '8:30 AM - Introduction to habitat restoration and safety briefing\n9:00 AM - Begin removal of invasive species\n11:00 AM - Educational talk about local ecosystem\n12:00 PM - Lunch break\n1:00 PM - Native plant installation\n3:00 PM - Wrap-up and future volunteer opportunities',
            'status': 'published',
            'co2_offset': 4.2,
            'trees_planted': 10,
            'volunteer_hour': 6
        },
        {
            'title': 'Recycling Education Fair',
            'description': 'An interactive fair to learn about proper recycling techniques, creative reuse, and waste reduction. Fun activities for all ages!',
            'category_id': 5,  # Recycling
            'organizer_id': 3,
            'max_participants': 150,
            'requirements': 'No special requirements. Optional: bring a challenging item to learn if/how it can be recycled.',
            'schedule': '10:00 AM - Fair opens\n11:00 AM - Recycling demonstration\n12:00 PM - Upcycling workshop\n1:00 PM - Documentary screening\n2:00 PM - Panel discussion\n4:00 PM - Fair closes',
            'status': 'published',
            'co2_offset': 3.0,
            'trees_planted': 0,
            'volunteer_hour': 6
        },
        {
            'title': 'Community Garden Planting Day',
            'description': 'Help plant and maintain our community garden. Learn gardening tips and meet neighbors who share your interest in growing food locally.',
            'category_id': 1,  # Tree Planting (closest match)
            'organizer_id': 4,
            'max_participants': 35,
            'requirements': 'Wear clothes that can get dirty. Bring gardening gloves if you have them. Tools and plants will be provided.',
            'schedule': '9:00 AM - Check-in and garden plan review\n9:30 AM - Bed preparation and planting begins\n12:00 PM - Lunch and gardening tips presentation\n1:00 PM - Continue planting\n3:00 PM - Watering and cleanup',
            'status': 'published',
            'co2_offset': 2.1,
            'trees_planted': 0,
            'volunteer_hour': 6
        },
        {
            'title': 'Green Energy Expo',
            'description': 'Learn about renewable energy options for your home and community. Meet local providers and see demonstrations of solar, wind, and other technologies.',
            'category_id': 3,  # Workshop
            'organizer_id': 5,
            'max_participants': 200,
            'requirements': 'No special requirements.',
            'schedule': '10:00 AM - Expo opens\n11:00 AM - Solar energy presentation\n12:00 PM - Lunch break\n1:00 PM - Wind energy presentation\n2:00 PM - Home energy efficiency workshop\n3:00 PM - Panel Q&A\n5:00 PM - Expo closes',
            'status': 'published',
            'co2_offset': 5.5,
            'trees_planted': 0,
            'volunteer_hour': 7
        }
    ]
    
    for i, event in enumerate(events, 1):
        created_at = datetime.now() - timedelta(days=random.randint(30, 90))
        start_date = datetime.now() + timedelta(days=random.randint(10, 60))
        end_date = start_date + timedelta(hours=random.randint(2, 8))
        
        location = random.choice(locations)
        image_url = random.choice(image_urls)
        
        query = """
        INSERT IGNORE INTO events
        (id, title, description, location, start_date, end_date, category_id, organizer_id, max_participants,
        image_url, requirements, schedule, status, created_at, co2_offset, trees_planted, volunteer_hour)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            i,
            event['title'],
            event['description'],
            location,
            start_date,
            end_date,
            event['category_id'],
            event['organizer_id'],
            event['max_participants'],
            image_url,
            event['requirements'],
            event['schedule'],
            event['status'],
            created_at,
            event['co2_offset'],
            event['trees_planted'],
            event['volunteer_hour']
        ))
    
    print(f"Added {cursor.rowcount} events.")

def seed_event_comments(cursor):
    """Seed event comments table"""
    print("Seeding event comments...")
    
    cursor.execute("SELECT id FROM events")
    event_ids = [row[0] for row in cursor.fetchall()]
    
    comments = [
        "Looking forward to this event!",
        "Can't wait to participate in this.",
        "This is exactly what our community needs.",
        "Will there be refreshments provided?",
        "Is this event suitable for children?",
        "I participated in a similar event last year and it was great.",
        "Thanks for organizing this important initiative.",
        "What should we bring to the event?",
        "Is carpooling available?",
        "This looks like a great opportunity to meet like-minded people.",
        "How long is the event expected to last?",
        "Will there be any follow-up events?",
        "I'm excited to learn new skills!",
        "This is a great way to give back to the community.",
        "Are there any pre-requisites for participation?"
    ]
    
    event_comments = []
    comment_id = 1
    
    for event_id in event_ids:
        num_comments = random.randint(0, 5)
        
        for _ in range(num_comments):
            user_id = random.randint(1, 5)
            content = random.choice(comments)
            created_at = datetime.now() - timedelta(days=random.randint(1, 15))
            
            event_comments.append((comment_id, event_id, user_id, content, None, created_at))
            comment_id += 1
    
    if event_comments:
        query = """
        INSERT IGNORE INTO event_comments
        (id, event_id, user_id, content, parent_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(query, event_comments)
        print(f"Added {cursor.rowcount} event comments.")
    else:
        print("No event comments to add.")

if __name__ == "__main__":
    seed_events_data() 
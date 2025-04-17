import sys
import os
import random
from datetime import datetime, timedelta
import json
import mysql.connector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import Database

def create_challenge_tables_if_not_exist(cursor):
    """Create all challenge-related tables if they don't exist"""
    print("Creating challenge tables if they don't exist...")
    
    # Create challenges table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `challenges` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `title` varchar(255) NOT NULL,
      `description` text NOT NULL,
      `category` enum('daily','weekly','monthly','one_time') NOT NULL,
      `difficulty` enum('easy','medium','hard','expert') NOT NULL,
      `exp_reward` int(11) NOT NULL DEFAULT 0,
      `icon_name` varchar(50) DEFAULT NULL,
      `requirements` text DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `is_active` tinyint(1) DEFAULT 1,
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create challenge_status table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `challenge_status` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
    `challenge_id` int(11) NOT NULL,
    `user_id` bigint(20) NOT NULL,
    `status` enum('in_progress','submitted','completed') NOT NULL DEFAULT 'in_progress',
    `progress` int(11) DEFAULT 0,
    `started_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `submitted_at` timestamp NULL DEFAULT NULL,
    `completed_at` timestamp NULL DEFAULT NULL,
    `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    `feedback` text DEFAULT NULL,
      PRIMARY KEY (`id`),
      UNIQUE KEY `user_challenge` (`user_id`,`challenge_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create challenge_submissions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `challenge_submissions` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
        `user_id` bigint(20) NOT NULL,
        `challenge_id` int(11) NOT NULL,
        `proof_text` text NOT NULL,
        `proof_urls` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`proof_urls`)),
        `status` enum('pending','approved','rejected') DEFAULT 'pending',
        `feedback` text DEFAULT NULL,
        `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
        `reviewed_at` timestamp NULL DEFAULT NULL,
      PRIMARY KEY (`id`),
      KEY `challenge_id` (`challenge_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    print("Challenge tables created or already exist")

def seed_challenges_data():
    """Seed data for challenge-related tables"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        create_challenge_tables_if_not_exist(cursor)

        print("Starting challenges data seeding...")
        
        seed_challenges(cursor)
        
        conn.commit()
        print("Challenges data seeding completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

def seed_challenges(cursor):
    """Seed challenges table"""
    print("Seeding challenges...")
    
    challenges = [
        # Daily Challenges
        {
            'title': 'Meatless Monday',
            'description': 'Eat vegetarian or vegan meals for a day to reduce your carbon footprint from meat production.',
            'category': 'daily',
            'difficulty': 'easy',
            'exp_reward': 50,
            'icon_name': 'salad',
            'requirements': 'Share your meatless meals for the day and explain how this reduces environmental impact.'
        },
        {
            'title': 'No Single-Use Plastic Day',
            'description': 'Avoid all single-use plastics for a day - bring your own bags, containers, and utensils.',
            'category': 'daily',
            'difficulty': 'medium',
            'exp_reward': 75,
            'icon_name': 'no-plastic',
            'requirements': 'Document your day without single-use plastics and share alternatives you used.'
        },
        {
            'title': 'Energy Saving Day',
            'description': 'Reduce your electricity usage by unplugging devices, using natural light, and minimizing appliance use.',
            'category': 'daily',
            'difficulty': 'easy',
            'exp_reward': 50,
            'icon_name': 'lightbulb',
            'requirements': 'Track and report your energy-saving measures and estimated kWh saved.'
        },
        {
            'title': 'Zero Food Waste Day',
            'description': 'Plan and prepare meals to produce zero food waste for an entire day.',
            'category': 'daily',
            'difficulty': 'medium',
            'exp_reward': 75,
            'icon_name': 'food',
            'requirements': 'Document your meal planning, preparation, and how you avoided food waste.'
        },
        {
            'title': 'Digital Detox',
            'description': 'Reduce your digital carbon footprint by limiting screen time and unnecessary internet usage for a day.',
            'category': 'daily',
            'difficulty': 'easy',
            'exp_reward': 50,
            'icon_name': 'power-off',
            'requirements': 'Share your experience and alternative activities you engaged in during your digital detox.'
        },
        
        # Weekly Challenges
        {
            'title': 'Waste Audit',
            'description': 'Conduct a waste audit of your household trash for a week to identify areas for waste reduction.',
            'category': 'weekly',
            'difficulty': 'medium',
            'exp_reward': 200,
            'icon_name': 'trash-audit',
            'requirements': 'Categorize and weigh your waste, then create a plan to reduce your highest waste categories.'
        },
        {
            'title': 'Local Food Week',
            'description': 'Source your meals primarily from local producers (within 100 miles) for a week to reduce food miles.',
            'category': 'weekly',
            'difficulty': 'medium',
            'exp_reward': 250,
            'icon_name': 'local-food',
            'requirements': 'Document your local food sources, meals prepared, and estimated food miles saved.'
        },
        {
            'title': 'Sustainable Transportation Week',
            'description': 'Use only sustainable transportation (walking, cycling, public transit, carpooling) for an entire week.',
            'category': 'weekly',
            'difficulty': 'hard',
            'exp_reward': 350,
            'icon_name': 'bus',
            'requirements': 'Log your travel methods, distances, and estimated carbon emissions saved compared to driving alone.'
        },
        {
            'title': 'Neighborhood Cleanup',
            'description': 'Organize or participate in a cleanup of your neighborhood, park, or natural area.',
            'category': 'weekly',
            'difficulty': 'medium',
            'exp_reward': 300,
            'icon_name': 'broom',
            'requirements': 'Document the cleanup with before/after photos and the amount of waste collected.'
        },
        {
            'title': 'DIY Natural Cleaning Products',
            'description': 'Make and use only homemade, natural cleaning products for a week.',
            'category': 'weekly',
            'difficulty': 'medium',
            'exp_reward': 200,
            'icon_name': 'spray-bottle',
            'requirements': 'Share your recipes, photos of your products, and how they performed compared to commercial products.'
        },
        
        # Monthly Challenges
        {
            'title': 'Create a Compost System',
            'description': 'Set up a composting system at home and maintain it for a month.',
            'category': 'monthly',
            'difficulty': 'hard',
            'exp_reward': 500,
            'icon_name': 'compost',
            'requirements': 'Document your compost setup, what you\'ve composted, and your progress throughout the month.'
        },
        {
            'title': 'Plastic-Free Month',
            'description': 'Eliminate or significantly reduce plastic packaging and products for an entire month.',
            'category': 'monthly',
            'difficulty': 'hard',
            'exp_reward': 600,
            'icon_name': 'plastic-free',
            'requirements': 'Track your plastic reduction strategies, alternatives used, and challenges faced.'
        },
        {
            'title': 'Sustainable Wardrobe Challenge',
            'description': 'Avoid buying new clothes for a month and focus on repairing, upcycling, or thrifting instead.',
            'category': 'monthly',
            'difficulty': 'medium',
            'exp_reward': 400,
            'icon_name': 'clothes',
            'requirements': 'Document your wardrobe projects, repairs, or thrifted finds that replaced new purchases.'
        },
        {
            'title': 'Water Conservation Month',
            'description': 'Implement comprehensive water-saving measures throughout your home for a month.',
            'category': 'monthly',
            'difficulty': 'medium',
            'exp_reward': 450,
            'icon_name': 'water',
            'requirements': 'Track your water conservation methods and estimated gallons saved compared to previous months.'
        },
        {
            'title': 'Grow Your Own Food',
            'description': 'Start and maintain a small food garden or indoor herb garden for a month.',
            'category': 'monthly',
            'difficulty': 'medium',
            'exp_reward': 500,
            'icon_name': 'seedling',
            'requirements': 'Document your garden setup, plant care, and harvest progress throughout the month.'
        },
        
        # One-Time Challenges
        {
            'title': 'Home Energy Audit',
            'description': 'Conduct a comprehensive energy audit of your home and implement efficiency improvements.',
            'category': 'one_time',
            'difficulty': 'hard',
            'exp_reward': 700,
            'icon_name': 'house-energy',
            'requirements': 'Document your audit process, findings, and the improvements you\'ve implemented.'
        },
        {
            'title': 'Environmental Education Workshop',
            'description': 'Organize an educational workshop or presentation about environmental issues for your community or workplace.',
            'category': 'one_time',
            'difficulty': 'expert',
            'exp_reward': 1000,
            'icon_name': 'teaching',
            'requirements': 'Provide details about your workshop content, attendance, and feedback received.'
        },
        {
            'title': 'Sustainable Home Makeover',
            'description': 'Complete at least five sustainable upgrades or improvements to your living space.',
            'category': 'one_time',
            'difficulty': 'hard',
            'exp_reward': 800,
            'icon_name': 'home',
            'requirements': 'Document each upgrade with before/after photos and explain the environmental benefits.'
        },
        {
            'title': 'Plant 10 Native Plants or Trees',
            'description': 'Research, obtain, and plant native species that support local biodiversity.',
            'category': 'one_time',
            'difficulty': 'medium',
            'exp_reward': 600,
            'icon_name': 'plant',
            'requirements': 'Identify the native species you\'ve planted, their ecological benefits, and document their planting and care.'
        },
        {
            'title': 'Create a Community Sustainability Initiative',
            'description': 'Develop and launch a sustainability initiative or project that engages your community.',
            'category': 'one_time',
            'difficulty': 'expert',
            'exp_reward': 1500,
            'icon_name': 'community',
            'requirements': 'Document your project planning, implementation, community involvement, and environmental impact.'
        }
    ]
    
    for i, challenge in enumerate(challenges, 1):
        created_at = datetime.now() - timedelta(days=random.randint(30, 90))
        updated_at = created_at + timedelta(days=random.randint(0, 10))
        
        query = """
        INSERT IGNORE INTO challenges 
        (id, title, description, category, difficulty, exp_reward, icon_name, requirements, created_at, is_active, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            i,
            challenge['title'],
            challenge['description'],
            challenge['category'],
            challenge['difficulty'],
            challenge['exp_reward'],
            challenge['icon_name'],
            challenge['requirements'],
            created_at,
            1,
            updated_at
        ))
    
    print(f"Added {cursor.rowcount} challenges.")

if __name__ == "__main__":
    seed_challenges_data() 
import sys
import os
from datetime import datetime
import mysql.connector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import Database

def create_chat_tables_if_not_exist(cursor):
    """Create all chat-related tables if they don't exist"""
    print("Creating chat tables if they don't exist...")
    
    # Create chat_rooms table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `chat_rooms` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `name` varchar(100) NOT NULL,
      `description` text DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `type` enum('public','private','group') NOT NULL DEFAULT 'public',
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create chat_messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `chat_messages` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `room_id` int(11) NOT NULL,
      `sender_id` bigint(20) NOT NULL,
      `content` text NOT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      KEY `room_id` (`room_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create chat_room_users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `chat_room_participants` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `room_id` int(11) NOT NULL,
    `user_id` bigint(20) NOT NULL,
    `role` enum('member','moderator','admin') DEFAULT 'member',
    `joined_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `last_read_at` timestamp NULL DEFAULT NULL,
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """)
    
    print("Chat tables created or already exist")

def seed_chat_rooms():
    """Seed data for chat rooms"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Create chat table if they don't exist
        create_chat_tables_if_not_exist(cursor)
        
        print("Starting chat rooms data seeding...")
        
        # Chat rooms
        chat_rooms = [
            {
                'id': 1,
                'name': 'Global Chat',
                'description': 'Public chat room for all users',
                'created_at': '2025-02-27 19:54:50',
                'type': 'public'
            },
            {
                'id': 3,
                'name': 'Help & Support',
                'description': 'Get help from the community',
                'created_at': '2025-03-04 17:32:16',
                'type': 'public'
            },
            {
                'id': 4,
                'name': 'Off-Topic',
                'description': 'Chat about anything',
                'created_at': '2025-03-04 17:32:16',
                'type': 'public'
            },
            {
                'id': 5,
                'name': 'Announcements',
                'description': 'Important updates and announcements',
                'created_at': '2025-03-04 17:32:16',
                'type': 'public'
            }
        ]
        
        for room in chat_rooms:
            query = """
            INSERT IGNORE INTO chat_rooms
            (id, name, description, created_at, type)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                room['id'],
                room['name'],
                room['description'],
                room['created_at'],
                room['type']
            ))
        
        conn.commit()
        print(f"Added {cursor.rowcount} chat rooms.")
        print("Chat rooms data seeding completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    seed_chat_rooms() 
import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import importlib.util
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import Database

load_dotenv()

class DatabaseSeeder:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'green_buddy')
        
    def create_database_if_not_exists(self):
        """Create the database if it doesn't exist"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            
            if connection.is_connected():
                cursor = connection.cursor()
                
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
                print(f"Database '{self.database}' created or already exists.")
                
                cursor.close()
                connection.close()
                return True
            else:
                print("Failed to connect to MySQL server")
                return False
                
        except Error as e:
            print(f"Error while creating database: {e}")
            return False
    
    def run_all_seed_scripts(self):
        """Run all seed scripts in the proper order"""
        # Define the order of seed scripts to run
        seed_scripts = [
            'seed_users.py',             
            'seed_achievement_data.py',  
            'seed_forum_data.py',        
            'seed_group_data.py',        
            'seed_chat_rooms.py',        
            'seed_events_data.py',       
            'seed_challenges_data.py',   
            'seed_blogs_data.py',        
            'seed_learning_data.py'      
        ]
        
        seed_dir = os.path.dirname(os.path.abspath(__file__))
        
        for script in seed_scripts:
            try:
                print(f"\n{'='*50}")
                print(f"Running {script}...")
                print(f"{'='*50}\n")
                
                script_path = os.path.join(seed_dir, script)
                
                spec = importlib.util.spec_from_file_location(script[:-3], script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                main_function_name = None
                for name in dir(module):
                    if name.startswith('seed_') and callable(getattr(module, name)):
                        if name.endswith('_data'):
                            main_function_name = name
                            break
                        elif main_function_name is None:
                            main_function_name = name
                
                if main_function_name:
                    main_function = getattr(module, main_function_name)
                    main_function()
                    print(f"Successfully executed {script} ({main_function_name})")
                else:
                    print(f"Could not find a seeding function in {script}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error executing {script}: {str(e)}")

        print("\n\n")
        print("="*80)
        print("Database seeding completed!")
        print("="*80)
        print("\nYou can now use the database with the following credentials:")
        print(f"  - Database: {self.database}")
        print(f"  - Host: {self.host}")
        print(f"  - User: {self.user}")
        print("\nAdmin user credentials:")
        print("  - Username: admin_user")
        print("  - Email: admin@greenbuddy.com")
        print("  - Password: Admin123!")

def seed_database():
    """Main function to seed the database"""
    seeder = DatabaseSeeder()
    
    if seeder.create_database_if_not_exists():
        seeder.run_all_seed_scripts()
    else:
        print("Failed to create database. Seeding aborted.")

if __name__ == "__main__":
    seed_database() 
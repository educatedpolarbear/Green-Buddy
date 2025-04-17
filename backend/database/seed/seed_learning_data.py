import sys
import os
import random
from datetime import datetime, timedelta
import mysql.connector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import Database

def create_learning_tables_if_not_exist(cursor):
    """Create all learning-related tables if they don't exist"""
    print("Creating learning tables if they don't exist...")
    
    # Create learning_categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `learning_categories` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `slug` varchar(100) NOT NULL,
      `title` varchar(255) NOT NULL,
      `description` text DEFAULT NULL,
      `icon_name` varchar(50) DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `content_type` enum('general','video','article','wiki','community') DEFAULT 'general',
      PRIMARY KEY (`id`),
      UNIQUE KEY `slug` (`slug`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create learning_materials table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `learning_materials` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `category_id` int(11) NOT NULL,
    `type` enum('video','article','wiki','community') NOT NULL,
    `title` varchar(255) NOT NULL,
    `content` text NOT NULL,
    `excerpt` text DEFAULT NULL,
    `thumbnail_url` varchar(255) DEFAULT NULL,
    `author_id` bigint(20) NOT NULL,
    `status` enum('draft','published','archived') DEFAULT 'published',
    `views_count` int(11) DEFAULT 0,
    `likes_count` int(11) DEFAULT 0,
    `duration` varchar(50) DEFAULT NULL,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """)
    
    # Create learning_material_likes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `learning_material_likes` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `material_id` int(11) NOT NULL,
      `user_id` bigint(20) NOT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `material_user` (`material_id`,`user_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create learning_material_comments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `learning_material_comments` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `material_id` int(11) NOT NULL,
      `user_id` bigint(20) NOT NULL,
      `parent_id` int(11) DEFAULT NULL,
      `content` text NOT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`),
      KEY `material_id` (`material_id`),
      KEY `parent_id` (`parent_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create learning_material_comment_likes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `learning_material_comment_likes` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `comment_id` int(11) NOT NULL,
      `user_id` bigint(20) NOT NULL,
      `type` enum('like','dislike') DEFAULT 'like',
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `comment_user` (`comment_id`,`user_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create learning_material_progress table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `learning_material_progress` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `user_id` int(11) NOT NULL,
      `material_id` int(11) NOT NULL,
      `completed_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `completion_type` enum('view','completion') NOT NULL,
      PRIMARY KEY (`id`),
      UNIQUE KEY `unique_user_material` (`user_id`,`material_id`,`completion_type`) USING BTREE,
      KEY `idx_learning_material_read_user_id` (`user_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    print("Learning tables created or already exist")

def seed_learning_data():
    """Seed data for learning-related tables"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        create_learning_tables_if_not_exist(cursor)
        
        print("Starting learning data seeding...")
        
        seed_general_categories(cursor)
        seed_video_categories(cursor)
        seed_article_categories(cursor)
        seed_wiki_categories(cursor)
        seed_community_categories(cursor)
        
        seed_video_materials(cursor)
        seed_article_materials(cursor)
        seed_wiki_materials(cursor)
        seed_community_materials(cursor)
        
        seed_material_likes(cursor)
        seed_material_comments(cursor)        
        seed_material_comment_likes(cursor)
        
        conn.commit()
        print("Learning data seeding completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

def seed_general_categories(cursor):
    """Seed general learning categories"""
    print("Seeding general learning categories...")
    
    categories = [
        {
            'id': 1,
            'slug': 'climate-action',
            'title': 'Climate Action',
            'description': 'Learn about climate change and how to take action',
            'icon_name': 'TreePine',
            'content_type': 'general'
        },
        {
            'id': 2,
            'slug': 'sustainable-living',
            'title': 'Sustainable Living',
            'description': 'Discover ways to live more sustainably',
            'icon_name': 'Leaf',
            'content_type': 'general'
        },
        {
            'id': 3,
            'slug': 'conservation',
            'title': 'Conservation',
            'description': 'Understanding ecosystems and conservation efforts',
            'icon_name': 'Globe',
            'content_type': 'general'
        },
        {
            'id': 4,
            'slug': 'renewable-energy',
            'title': 'Renewable Energy',
            'description': 'Exploring clean and renewable energy solutions',
            'icon_name': 'Zap',
            'content_type': 'general'
        }
    ]
    
    for category in categories:
        created_at = datetime.now() - timedelta(days=random.randint(30, 90))
        
        query = """
        INSERT IGNORE INTO learning_categories
        (id, slug, title, description, icon_name, created_at, content_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            category['id'],
            category['slug'],
            category['title'],
            category['description'],
            category['icon_name'],
            created_at,
            category['content_type']
        ))
    
    print(f"Added {len(categories)} general learning categories.")

def seed_video_categories(cursor):
    """Seed video learning categories"""
    print("Seeding video learning categories...")
    
    categories = [
        {
            'id': 5,
            'slug': 'tutorials',
            'title': 'Video Tutorials',
            'description': 'Step-by-step video guides on environmental topics',
            'icon_name': 'Play',
            'content_type': 'video'
        },
        {
            'id': 6,
            'slug': 'documentaries',
            'title': 'Documentaries',
            'description': 'In-depth documentaries about environmental issues',
            'icon_name': 'Film',
            'content_type': 'video'
        },
        {
            'id': 7,
            'slug': 'expert-talks',
            'title': 'Expert Talks',
            'description': 'Video presentations from environmental experts',
            'icon_name': 'Mic',
            'content_type': 'video'
        },
        {
            'id': 8,
            'slug': 'how-to-videos',
            'title': 'How-To Videos',
            'description': 'Practical demonstrations of eco-friendly practices',
            'icon_name': 'Video',
            'content_type': 'video'
        }
    ]
    
    for category in categories:
        created_at = datetime.now() - timedelta(days=random.randint(30, 90))
        
        query = """
        INSERT IGNORE INTO learning_categories
        (id, slug, title, description, icon_name, created_at, content_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            category['id'],
            category['slug'],
            category['title'],
            category['description'],
            category['icon_name'],
            created_at,
            category['content_type']
        ))
    
    print(f"Added {len(categories)} video learning categories.")

def seed_article_categories(cursor):
    """Seed article learning categories"""
    print("Seeding article learning categories...")
    
    categories = [
        {
            'id': 9,
            'slug': 'news',
            'title': 'Environmental News',
            'description': 'Latest updates and news in environmental conservation',
            'icon_name': 'Newspaper',
            'content_type': 'article'
        },
        {
            'id': 10,
            'slug': 'guides',
            'title': 'How-to Guides',
            'description': 'Practical guides for sustainable living',
            'icon_name': 'BookMarked',
            'content_type': 'article'
        },
        {
            'id': 11,
            'slug': 'research',
            'title': 'Research & Studies',
            'description': 'Scientific research and environmental studies',
            'icon_name': 'Microscope',
            'content_type': 'article'
        },
        {
            'id': 12,
            'slug': 'opinion',
            'title': 'Opinion Pieces',
            'description': 'Thought-provoking perspectives on environmental issues',
            'icon_name': 'MessageSquare',
            'content_type': 'article'
        }
    ]
    
    for category in categories:
        created_at = datetime.now() - timedelta(days=random.randint(30, 90))
        
        query = """
        INSERT IGNORE INTO learning_categories
        (id, slug, title, description, icon_name, created_at, content_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            category['id'],
            category['slug'],
            category['title'],
            category['description'],
            category['icon_name'],
            created_at,
            category['content_type']
        ))
    
    print(f"Added {len(categories)} article learning categories.")

def seed_wiki_categories(cursor):
    """Seed wiki learning categories"""
    print("Seeding wiki learning categories...")
    
    categories = [
        {
            'id': 13,
            'slug': 'species-guide',
            'title': 'Species Guide',
            'description': 'Information about plant and animal species',
            'icon_name': 'TreePine',
            'content_type': 'wiki'
        },
        {
            'id': 14,
            'slug': 'eco-technologies',
            'title': 'Eco Technologies',
            'description': 'Detailed guides on environmental technologies',
            'icon_name': 'Lightbulb',
            'content_type': 'wiki'
        },
        {
            'id': 15,
            'slug': 'conservation-methods',
            'title': 'Conservation Methods',
            'description': 'Techniques and approaches for environmental conservation',
            'icon_name': 'Wrench',
            'content_type': 'wiki'
        },
        {
            'id': 16,
            'slug': 'climate-science',
            'title': 'Climate Science',
            'description': 'Scientific explanations of climate phenomena',
            'icon_name': 'Thermometer',
            'content_type': 'wiki'
        }
    ]
    
    for category in categories:
        created_at = datetime.now() - timedelta(days=random.randint(30, 90))
        
        query = """
        INSERT IGNORE INTO learning_categories
        (id, slug, title, description, icon_name, created_at, content_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            category['id'],
            category['slug'],
            category['title'],
            category['description'],
            category['icon_name'],
            created_at,
            category['content_type']
        ))
    
    print(f"Added {len(categories)} wiki learning categories.")

def seed_community_categories(cursor):
    """Seed community learning categories"""
    print("Seeding community learning categories...")
    
    categories = [
        {
            'id': 17,
            'slug': 'success-stories',
            'title': 'Success Stories',
            'description': 'Community success stories in environmental action',
            'icon_name': 'Star',
            'content_type': 'community'
        },
        {
            'id': 18,
            'slug': 'local-initiatives',
            'title': 'Local Initiatives',
            'description': 'Community-led environmental projects',
            'icon_name': 'Users',
            'content_type': 'community'
        },
        {
            'id': 19,
            'slug': 'tips-tricks',
            'title': 'Tips & Tricks',
            'description': 'Community-shared environmental tips',
            'icon_name': 'Lightbulb',
            'content_type': 'community'
        },
        {
            'id': 20,
            'slug': 'discussions',
            'title': 'Open Discussions',
            'description': 'Environmental discussion topics',
            'icon_name': 'MessageSquare',
            'content_type': 'community'
        }
    ]
    
    for category in categories:
        created_at = datetime.now() - timedelta(days=random.randint(30, 90))
        
        query = """
        INSERT IGNORE INTO learning_categories
        (id, slug, title, description, icon_name, created_at, content_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            category['id'],
            category['slug'],
            category['title'],
            category['description'],
            category['icon_name'],
            created_at,
            category['content_type']
        ))
    
    print(f"Added {len(categories)} community learning categories.")

def seed_video_materials(cursor):
    """Seed video learning materials"""
    print("Seeding video learning materials...")
    
    videos = [
        {
            'id': 1,
            'category_id': 5,
            'title': 'How to Start Your Own Compost Bin',
            'content': 'dQw4w9WgXcQ',  # YouTube video ID
            'excerpt': 'A step-by-step guide to creating and maintaining a compost bin for organic waste recycling.',
            'thumbnail_url': 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
            'author_id': 1,
            'duration': '15:20'
        },
        {
            'id': 2,
            'category_id': 6,
            'title': 'The Hidden Life of Trees: Documentary',
            'content': 'XQiDFkEfHy4',
            'excerpt': 'An exploration of forest ecosystems and the complex social networks of trees.',
            'thumbnail_url': 'https://img.youtube.com/vi/XQiDFkEfHy4/maxresdefault.jpg',
            'author_id': 2,
            'duration': '42:15'
        },
        {
            'id': 3,
            'category_id': 7,
            'title': 'Climate Science Explained by Dr. Emily Johnson',
            'content': 'LOH0IZwp_nA',
            'excerpt': 'Leading climate scientist explains the latest research on global climate patterns.',
            'thumbnail_url': 'https://img.youtube.com/vi/LOH0IZwp_nA/maxresdefault.jpg',
            'author_id': 3,
            'duration': '28:45'
        },
        {
            'id': 4,
            'category_id': 8,
            'title': 'DIY Rainwater Collection System',
            'content': 'IKEKukDycMo',
            'excerpt': 'Learn how to build an efficient rainwater harvesting system for your home.',
            'thumbnail_url': 'https://img.youtube.com/vi/IKEKukDycMo/maxresdefault.jpg',
            'author_id': 1,
            'duration': '18:30'
        },
        {
            'id': 5,
            'category_id': 5,
            'title': 'Growing Vegetables in Small Spaces',
            'content': '_38JDGnr0vA',
            'excerpt': 'Urban gardening techniques for growing vegetables in apartments and small yards.',
            'thumbnail_url': 'https://img.youtube.com/vi/_38JDGnr0vA/maxresdefault.jpg',
            'author_id': 2,
            'duration': '22:10'
        }
    ]
    
    for video in videos:
        created_at = datetime.now() - timedelta(days=random.randint(10, 60))
        updated_at = created_at + timedelta(days=random.randint(1, 10))
        views_count = random.randint(50, 2000)
        likes_count = random.randint(5, int(views_count * 0.1))
        
        query = """
        INSERT IGNORE INTO learning_materials
        (id, category_id, type, title, content, excerpt, thumbnail_url, author_id, 
        status, views_count, likes_count, duration, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            video['id'],
            video['category_id'],
            'video',
            video['title'],
            video['content'],
            video['excerpt'],
            video['thumbnail_url'],
            video['author_id'],
            'published',
            views_count,
            likes_count,
            video['duration'],
            created_at,
            updated_at
        ))
    
    print(f"Added {len(videos)} video learning materials.")

def seed_article_materials(cursor):
    """Seed article learning materials"""
    print("Seeding article learning materials...")
    
    articles = [
        {
            'id': 6,
            'category_id': 9,
            'title': 'Global Carbon Emissions Show Slight Decline in 2023',
            'content': '<h1>Global Carbon Emissions Show Slight Decline in 2023</h1>\n<p>For the first time in five years, global carbon emissions have shown a measurable decline according to new data released by the International Energy Agency (IEA).</p>\n\n<h2>Key Findings</h2>\n<p>The IEA report highlights several important trends:</p>\n<ul>\n  <li>Global CO2 emissions decreased by 1.3% compared to 2022</li>\n  <li>Renewable energy implementation increased by 8.5%</li>\n  <li>Coal use declined by 3.2% globally</li>\n  <li>Electric vehicle adoption rose by 35% year-over-year</li>\n</ul>\n\n<h2>Regional Variations</h2>\n<p>While the overall trend is positive, there are significant regional differences:</p>\n<ul>\n  <li>Europe led with a 5.2% reduction in emissions</li>\n  <li>North America achieved a 3.1% reduction</li>\n  <li>Emissions in Asia remained relatively flat (0.3% increase)</li>\n  <li>Africa saw a 2.1% increase in emissions due to development needs</li>\n</ul>\n\n<h2>Future Outlook</h2>\n<p>Climate scientists caution that while this decline is encouraging, it must accelerate to meet global climate targets. The report suggests that maintaining a 3-4% annual reduction is necessary to limit warming to 1.5°C above pre-industrial levels.</p>',
            'excerpt': 'New data shows global carbon emissions decreased by 1.3% in 2023, marking the first decline in five years.',
            'thumbnail_url': 'https://plus.unsplash.com/premium_photo-1661880571980-6b9cbcc25b75?fm=jpg&q=60&w=3000&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8Y2FyYm9uJTIwZW1pc3Npb25zfGVufDB8fDB8fHww',
            'author_id': 3,
            'duration': '8 min read'
        },
        {
            'id': 7,
            'category_id': 10,
            'title': 'A Beginner\'s Guide to Plastic-Free Living',
            'content': '<h1>A Beginner\'s Guide to Plastic-Free Living</h1>\n<p>Reducing plastic use doesn\'t have to be overwhelming. This step-by-step guide helps you transition to a plastic-free lifestyle at your own pace.</p>\n\n<h2>Start in the Kitchen</h2>\n<p>The kitchen is often where the most plastic waste accumulates:</p>\n<ul>\n  <li>Replace plastic wrap with beeswax wraps</li>\n  <li>Use glass containers instead of plastic for food storage</li>\n  <li>Bring reusable produce bags and shopping bags to the store</li>\n  <li>Buy from bulk bins using your own containers</li>\n  <li>Choose cardboard or glass packaging over plastic when possible</li>\n</ul>\n\n<h2>Bathroom Swaps</h2>\n<p>Once you\'ve tackled the kitchen, move to the bathroom:</p>\n<ul>\n  <li>Use bar soap instead of liquid soap in plastic bottles</li>\n  <li>Try shampoo and conditioner bars</li>\n  <li>Switch to a bamboo toothbrush</li>\n  <li>Use a safety razor instead of disposable plastic razors</li>\n  <li>Make or buy plastic-free deodorant</li>\n</ul>\n\n<h2>On-the-Go Essentials</h2>\n<p>Prepare a kit to avoid single-use plastics when away from home:</p>\n<ul>\n  <li>Reusable water bottle</li>\n  <li>Travel coffee mug</li>\n  <li>Portable cutlery set</li>\n  <li>Foldable shopping bag</li>\n  <li>Reusable straw (if needed)</li>\n</ul>\n\n<h2>Remember: Progress Over Perfection</h2>\n<p>Going plastic-free is a journey, not a destination. Focus on consistent small changes rather than trying to eliminate all plastic at once. Each plastic item you refuse or replace makes a difference!</p>',
            'excerpt': 'A practical guide to reducing plastic use in your daily life with simple swaps and sustainable alternatives.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1530587191325-3db32d826c18?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 1,
            'duration': '12 min read'
        },
        {
            'id': 8,
            'category_id': 11,
            'title': 'The Role of Soil Carbon Sequestration in Climate Mitigation',
            'content': '<h1>The Role of Soil Carbon Sequestration in Climate Mitigation</h1>\n<p>Recent research highlights soil\'s remarkable potential to capture and store atmospheric carbon, offering a natural solution to climate change.</p>\n\n<h2>The Science of Soil Carbon</h2>\n<p>Soil represents the largest terrestrial carbon sink on Earth, containing approximately three times the carbon found in the atmosphere. Through photosynthesis, plants convert atmospheric CO2 into biomass, much of which eventually transfers to soil through:</p>\n<ul>\n  <li>Root exudates and sloughing</li>\n  <li>Plant litter and residue decomposition</li>\n  <li>Microbial processing and stabilization</li>\n</ul>\n\n<h2>Agricultural Practices That Enhance Sequestration</h2>\n<p>Several farming methods have been scientifically proven to increase carbon storage:</p>\n<ol>\n  <li><strong>Reduced tillage:</strong> Minimizes soil disturbance, protecting carbon structures</li>\n  <li><strong>Cover cropping:</strong> Extends photosynthesis periods and adds diverse biomass</li>\n  <li><strong>Crop rotation:</strong> Improves soil structure and microbial diversity</li>\n  <li><strong>Integrated livestock:</strong> Adds nutrient cycling through manure distribution</li>\n  <li><strong>Agroforestry:</strong> Incorporates deep-rooted woody plants that store carbon at greater depths</li>\n</ol>\n\n<h2>Quantifying the Potential</h2>\n<p>The latest data from a global meta-analysis suggests properly managed soils could sequester an additional 0.9-1.85 billion tons of carbon dioxide equivalent annually, representing approximately 3-6% of global fossil fuel emissions. This potential varies significantly by region, climate, and soil type.</p>\n\n<h2>Challenges and Limitations</h2>\n<p>Despite its promise, soil carbon sequestration faces several obstacles:</p>\n<ul>\n  <li>Carbon saturation in soils over time</li>\n  <li>Reversal risk during droughts or with management changes</li>\n  <li>Measurement and verification difficulties</li>\n  <li>Economic barriers to changing established practices</li>\n</ul>\n\n<h2>Policy Implications</h2>\n<p>For soil carbon sequestration to reach its potential, supportive policies are essential. Developing robust carbon markets, providing technical assistance to farmers, and investing in monitoring technology will all play crucial roles in scaling this natural climate solution.</p>',
            'excerpt': 'Explore how agricultural practices that enhance soil carbon storage could provide a significant tool for combating climate change.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 2,
            'duration': '15 min read'
        },
        {
            'id': 9,
            'category_id': 12,
            'title': 'Beyond Recycling: Why We Need Systemic Change for Environmental Progress',
            'content': '<h1>Beyond Recycling: Why We Need Systemic Change for Environmental Progress</h1>\n<p>While individual actions matter, addressing our environmental crisis requires fundamental shifts in how our economies and societies function.</p>\n\n<h2>The Limits of Individual Action</h2>\n<p>For decades, environmental messaging has focused on personal responsibility: recycle, use less water, drive less. These actions are valuable but insufficient for several reasons:</p>\n<ul>\n  <li>80% of global emissions come from just 100 companies</li>\n  <li>Individual choices are constrained by available infrastructure</li>\n  <li>Social and economic pressures make sustainable choices difficult for many</li>\n  <li>The scale of change needed exceeds what individual action can achieve</li>\n</ul>\n\n<h2>Necessary Systemic Changes</h2>\n<p>True environmental progress requires transformation at multiple levels:</p>\n\n<h3>Economic Systems</h3>\n<p>Our economies must evolve beyond the growth-at-all-costs model:</p>\n<ul>\n  <li>Incorporate true environmental costs into pricing</li>\n  <li>Shift from ownership to service models in many sectors</li>\n  <li>Prioritize wellbeing indicators alongside GDP</li>\n  <li>Reform subsidies that incentivize harmful practices</li>\n</ul>\n\n<h3>Energy Infrastructure</h3>\n<p>The transition to renewable energy requires:</p>\n<ul>\n  <li>Massive public investment in clean energy infrastructure</li>\n  <li>Grid modernization for distributed generation</li>\n  <li>Just transition planning for affected communities</li>\n  <li>Research funding for next-generation solutions</li>\n</ul>\n\n<h3>Urban Planning</h3>\n<p>Cities must be redesigned to enable sustainable living:</p>\n<ul>\n  <li>Mixed-use development that reduces transportation needs</li>\n  <li>Robust public transit systems</li>\n  <li>Green building codes and retrofitting programs</li>\n  <li>Urban agriculture and ecosystem integration</li>\n</ul>\n\n<h2>The Role of Individuals</h2>\n<p>While system change is paramount, individuals still have crucial roles:</p>\n<ul>\n  <li>Civic engagement and voting for pro-environment policies</li>\n  <li>Supporting businesses committed to sustainable practices</li>\n  <li>Community organizing and collective action</li>\n  <li>Advocating for corporate accountability</li>\n</ul>\n\n<h2>A Both/And Approach</h2>\n<p>Moving beyond the false dichotomy of individual vs. systemic change, we need both. Individual actions create cultural shifts that make systemic changes politically possible, while systemic changes make sustainable choices accessible to everyone.</p>',
            'excerpt': 'Why individual environmental actions are important but insufficient without broader systemic changes to our economy and society.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 4,
            'duration': '10 min read'
        },
        {
            'id': 10,
            'category_id': 9,
            'title': 'New Research Shows Microplastics Found in Human Placentas',
            'content': '<h1>New Research Shows Microplastics Found in Human Placentas</h1>\n<p>A concerning study published this month in Environmental Health Perspectives has detected microplastic particles in human placentas, raising new questions about health impacts.</p>\n\n<h2>Study Findings</h2>\n<p>Researchers analyzed 40 placenta samples collected from healthy pregnancies, finding:</p>\n<ul>\n  <li>Microplastic particles were present in 72% of samples</li>\n  <li>Four common plastic types were identified: polyethylene, PVC, polypropylene, and polystyrene</li>\n  <li>Particles ranged from 5 to 50 micrometers in size</li>\n  <li>An average of 4.6 particles per placenta were detected</li>\n</ul>\n\n<h2>Potential Health Implications</h2>\n<p>While the study doesn\'t demonstrate health impacts, it raises several concerns:</p>\n<ul>\n  <li>The placenta is a critical barrier protecting developing fetuses</li>\n  <li>Microplastics can carry environmental pollutants and chemicals</li>\n  <li>Some plastic additives are known endocrine disruptors</li>\n  <li>Particles may interfere with placental function</li>\n</ul>\n\n<h2>Sources of Exposure</h2>\n<p>The researchers identified several likely exposure sources:</p>\n<ul>\n  <li>Food and beverages packaged in plastic</li>\n  <li>Airborne microplastic particles</li>\n  <li>Personal care products containing microbeads</li>\n  <li>Synthetic clothing fibers</li>\n</ul>\n\n<h2>Scientific Perspective</h2>\n<p>Dr. Maria Rodriguez, the study\'s lead author, emphasized caution in interpreting the results: "While this discovery is concerning, we don\'t yet know if these particles cause harm. This research highlights the need for further studies on potential developmental effects and expanded investigation into how these particles enter the body."</p>\n\n<h2>Reducing Exposure</h2>\n<p>Until more is known, experts suggest reasonable precautions:</p>\n<ul>\n  <li>Filter drinking water</li>\n  <li>Reduce plastic food packaging when possible</li>\n  <li>Avoid heating food in plastic containers</li>\n  <li>Choose natural fabric clothing</li>\n  <li>Use HEPA air filters in homes</li>\n</ul>',
            'excerpt': 'Scientists have detected microplastic particles in human placentas, raising concerns about potential health impacts on developing babies.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1579154204601-01588f351e67?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 5,
            'duration': '7 min read'
        }
    ]
    
    for article in articles:
        created_at = datetime.now() - timedelta(days=random.randint(10, 60))
        updated_at = created_at + timedelta(days=random.randint(1, 10))
        views_count = random.randint(50, 2000)
        likes_count = random.randint(5, int(views_count * 0.1))
        
        query = """
        INSERT IGNORE INTO learning_materials
        (id, category_id, type, title, content, excerpt, thumbnail_url, author_id, 
        status, views_count, likes_count, duration, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            article['id'],
            article['category_id'],
            'article',
            article['title'],
            article['content'],
            article['excerpt'],
            article['thumbnail_url'],
            article['author_id'],
            'published',
            views_count,
            likes_count,
            article['duration'],
            created_at,
            updated_at
        ))
    
    print(f"Added {len(articles)} article learning materials.")

def seed_wiki_materials(cursor):
    """Seed wiki learning materials"""
    print("Seeding wiki learning materials...")
    
    wikis = [
        {
            'id': 11,
            'category_id': 13,
            'title': 'Endangered Species of the Amazon Rainforest',
            'content': '<h1>Endangered Species of the Amazon Rainforest</h1>\n<p>The Amazon rainforest is home to countless species, many of which are currently threatened with extinction. This guide provides detailed information on the most critically endangered animals and plants, their habitats, and conservation efforts.</p>\n\n<h2>Mammals</h2>\n\n<h3>Giant Otter (<em>Pteronura brasiliensis</em>)</h3>\n<p>Status: Endangered</p>\n<ul>\n  <li><strong>Description:</strong> The giant otter can reach up to 1.8m in length and is the largest member of the mustelid family.</li>\n  <li><strong>Habitat:</strong> Slow-moving rivers, streams, and lakes within the Amazon Basin.</li>\n  <li><strong>Threats:</strong> Poaching for fur, habitat destruction, water pollution from mining.</li>\n  <li><strong>Population:</strong> Estimated 3,000-5,000 individuals remaining.</li>\n  <li><strong>Conservation efforts:</strong> Protected areas establishment, anti-poaching patrols, habitat restoration.</li>\n</ul>\n\n<h3>Amazonian Manatee (<em>Trichechus inunguis</em>)</h3>\n<p>Status: Vulnerable</p>\n<ul>\n  <li><strong>Description:</strong> Aquatic mammal that can grow up to 2.8m long and weigh 450kg.</li>\n  <li><strong>Habitat:</strong> Freshwater rivers, lakes, and flooded forests.</li>\n  <li><strong>Threats:</strong> Illegal hunting for meat, accidental entanglement in fishing gear, boat collisions.</li>\n  <li><strong>Population:</strong> Unknown, but continuing to decline.</li>\n  <li><strong>Conservation efforts:</strong> Legal protection, education programs, rehabilitation centers.</li>\n</ul>\n\n<h2>Birds</h2>\n\n<h3>Harpy Eagle (<em>Harpia harpyja</em>)</h3>\n<p>Status: Near Threatened</p>\n<ul>\n  <li><strong>Description:</strong> One of the world\'s largest and most powerful eagles, with a wingspan of up to 2m.</li>\n  <li><strong>Habitat:</strong> Emergent canopy trees in undisturbed rainforest.</li>\n  <li><strong>Threats:</strong> Deforestation, hunting, nest destruction.</li>\n  <li><strong>Population:</strong> Less than 50,000 adult individuals estimated.</li>\n  <li><strong>Conservation efforts:</strong> Captive breeding programs, nest monitoring, local education initiatives.</li>\n</ul>\n\n<h2>Plants</h2>\n\n<h3>Amazon Water Lily (<em>Victoria amazonica</em>)</h3>\n<p>Status: Vulnerable in certain regions</p>\n<ul>\n  <li><strong>Description:</strong> Giant water lily with leaves that can grow up to 3m in diameter.</li>\n  <li><strong>Habitat:</strong> Oxbow lakes and flooded areas with still water.</li>\n  <li><strong>Threats:</strong> Water pollution, habitat destruction, climate change.</li>\n  <li><strong>Conservation efforts:</strong> Protected area designation, water quality monitoring, seed banking.</li>\n</ul>\n\n<h2>Conservation Challenges</h2>\n<p>Major threats to Amazon biodiversity include:</p>\n<ol>\n  <li>Deforestation for agriculture, particularly soy cultivation and cattle ranching</li>\n  <li>Infrastructure projects including dams, roads, and mining operations</li>\n  <li>Climate change altering rainfall patterns and temperature regimes</li>\n  <li>Illegal wildlife trafficking and poaching</li>\n  <li>Forest fires, both natural and human-caused</li>\n</ol>\n\n<h2>How to Support Conservation</h2>\n<p>Individuals can contribute to Amazon conservation through:</p>\n<ul>\n  <li>Supporting organizations working directly in the Amazon</li>\n  <li>Making sustainable consumer choices (avoiding products linked to deforestation)</li>\n  <li>Offsetting carbon footprints</li>\n  <li>Raising awareness about Amazon conservation issues</li>\n  <li>Supporting indigenous land rights</li>\n</ul>',
            'excerpt': 'An overview of critically endangered species in the Amazon rainforest ecosystem and current conservation efforts.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1535930891776-0c2dfb7fda1a?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 2
        },
        {
            'id': 12,
            'category_id': 14,
            'title': 'Solar Panel Technology: Principles and Innovations',
            'content': '<h1>Solar Panel Technology: Principles and Innovations</h1>\n<p>This comprehensive guide explains how solar panels work, the different types available, and emerging technologies that are revolutionizing the field.</p>\n\n<h2>Basic Principles</h2>\n<p>Solar panels, or photovoltaic (PV) cells, convert sunlight directly into electricity through the photovoltaic effect:</p>\n<ol>\n  <li>Photons from sunlight strike the solar panel and are absorbed by semiconducting materials</li>\n  <li>Electrons are knocked loose from atoms, creating an electric current</li>\n  <li>The direct current (DC) electricity flows to an inverter, which converts it to alternating current (AC)</li>\n  <li>The AC electricity powers homes and businesses or feeds into the grid</li>\n</ol>\n\n<h2>Types of Solar Panels</h2>\n\n<h3>Monocrystalline Silicon Panels</h3>\n<ul>\n  <li><strong>Efficiency:</strong> 15-22%</li>\n  <li><strong>Lifespan:</strong> 25-40 years</li>\n  <li><strong>Advantages:</strong> Higher efficiency, space-efficient, longer lifespan</li>\n  <li><strong>Disadvantages:</strong> More expensive, performance decreases in high temperatures</li>\n</ul>\n\n<h3>Polycrystalline Silicon Panels</h3>\n<ul>\n  <li><strong>Efficiency:</strong> 13-16%</li>\n  <li><strong>Lifespan:</strong> 23-35 years</li>\n  <li><strong>Advantages:</strong> Lower cost, less waste in production</li>\n  <li><strong>Disadvantages:</strong> Lower efficiency, requires more space</li>\n</ul>\n\n<h3>Thin-Film Solar Panels</h3>\n<ul>\n  <li><strong>Efficiency:</strong> 10-13%</li>\n  <li><strong>Lifespan:</strong> 15-20 years</li>\n  <li><strong>Advantages:</strong> Flexible, lightweight, better performance in high heat</li>\n  <li><strong>Disadvantages:</strong> Shortest lifespan, requires significant space</li>\n</ul>\n\n<h2>Recent Innovations</h2>\n\n<h3>Bifacial Solar Panels</h3>\n<p>These panels capture sunlight from both sides, increasing energy production by 5-30% depending on installation and surrounding reflectivity.</p>\n\n<h3>Perovskite Solar Cells</h3>\n<p>A breakthrough technology with:</p>\n<ul>\n  <li>Rapidly increasing efficiency (now exceeding 25% in lab settings)</li>\n  <li>Lower production costs</li>\n  <li>Flexibility and versatility in applications</li>\n  <li>Challenges in stability and durability being addressed</li>\n</ul>\n\n<h3>Building-Integrated Photovoltaics (BIPV)</h3>\n<p>Solar materials that replace conventional building materials:</p>\n<ul>\n  <li>Solar roof tiles</li>\n  <li>Photovoltaic windows</li>\n  <li>Solar facades</li>\n</ul>\n\n<h3>Floating Solar Farms</h3>\n<p>Solar installations on water bodies offering:</p>\n<ul>\n  <li>Land conservation</li>\n  <li>Higher efficiency due to water cooling</li>\n  <li>Reduced water evaporation</li>\n  <li>Potential for pairing with hydroelectric facilities</li>\n</ul>\n\n<h2>Efficiency Improvements</h2>\n<p>Several approaches are increasing solar panel efficiency:</p>\n<ul>\n  <li>Multi-junction cells using multiple semiconductor layers</li>\n  <li>Concentrated photovoltaics using lenses or mirrors</li>\n  <li>Surface texturing to reduce reflection</li>\n  <li>Maximum power point tracking (MPPT) systems</li>\n  <li>Anti-soiling coatings</li>\n</ul>',
            'excerpt': 'A detailed explanation of solar panel technology, including different types, working principles, and cutting-edge innovations.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1509391366360-2e959784a276?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 3
        },
        {
            'id': 13,
            'category_id': 15,
            'title': 'Permaculture Design Principles',
            'content': '<h1>Permaculture Design Principles</h1>\n<p>Permaculture is an approach to land management and settlement design that adopts arrangements observed in flourishing natural ecosystems. This guide explores the core principles and their practical applications.</p>\n\n<h2>Core Ethics</h2>\n<p>Permaculture is founded on three ethical principles:</p>\n<ol>\n  <li><strong>Earth Care:</strong> Providing for all life systems to continue and multiply</li>\n  <li><strong>People Care:</strong> Providing for people to have access to resources necessary for their existence</li>\n  <li><strong>Fair Share:</strong> Setting limits to consumption and redistributing surplus</li>\n</ol>\n\n<h2>Design Principles</h2>\n\n<h3>1. Observe and Interact</h3>\n<p>Take time to engage with nature, to design solutions that suit a particular situation.</p>\n<ul>\n  <li><strong>Application:</strong> Spend a full year observing land before making major changes</li>\n  <li><strong>Examples:</strong> Noting sun patterns, water flow, wind direction, existing vegetation</li>\n</ul>\n\n<h3>2. Catch and Store Energy</h3>\n<p>Develop systems that collect resources at peak abundance for use in times of need.</p>\n<ul>\n  <li><strong>Application:</strong> Designing water harvesting systems, solar collection, soil building</li>\n  <li><strong>Examples:</strong> Rainwater tanks, swales, solar panels, food preservation</li>\n</ul>\n\n<h3>3. Obtain a Yield</h3>\n<p>Ensure that you are getting truly useful rewards as part of the work that you are doing.</p>\n<ul>\n  <li><strong>Application:</strong> Growing food, generating energy, creating practical items</li>\n  <li><strong>Examples:</strong> Productive gardens, fuel production, craft making</li>\n</ul>\n\n<h3>4. Apply Self-Regulation and Accept Feedback</h3>\n<p>Discourage inappropriate activity to ensure that systems can continue to function well.</p>\n<ul>\n  <li><strong>Application:</strong> Monitoring and responding to changes in systems</li>\n  <li><strong>Examples:</strong> Managed grazing, pest threshold monitoring, soil testing</li>\n</ul>\n\n<h3>5. Use and Value Renewable Resources and Services</h3>\n<p>Make the best use of nature\'s abundance to reduce consumption and dependence on non-renewable resources.</p>\n<ul>\n  <li><strong>Application:</strong> Utilizing natural processes for system needs</li>\n  <li><strong>Examples:</strong> Passive solar design, biological pest control, animal tractors</li>\n</ul>\n\n<h3>6. Produce No Waste</h3>\n<p>Value and make use of all resources that are available, including waste streams.</p>\n<ul>\n  <li><strong>Application:</strong> Composting, repurposing, recycling</li>\n  <li><strong>Examples:</strong> Worm farms, upcycling, mulching, biogas production</li>\n</ul>\n\n<h3>7. Design From Patterns to Details</h3>\n<p>Observe patterns in nature and society and use them to inform design, later filling in the details.</p>\n<ul>\n  <li><strong>Application:</strong> Basing layouts on natural patterns</li>\n  <li><strong>Examples:</strong> Keyline design, zone planning, sector analysis</li>\n</ul>\n\n<h3>8. Integrate Rather Than Segregate</h3>\n<p>Place elements in ways that they work together to support each other.</p>\n<ul>\n  <li><strong>Application:</strong> Creating polycultures, guilds, and mutually beneficial arrangements</li>\n  <li><strong>Examples:</strong> Forest gardens, companion planting, integrated animal systems</li>\n</ul>\n\n<h3>9. Use Small and Slow Solutions</h3>\n<p>Small and slow systems are easier to maintain, make better use of local resources, and produce more sustainable outcomes.</p>\n<ul>\n  <li><strong>Application:</strong> Gradual implementation, appropriate technology</li>\n  <li><strong>Examples:</strong> Sheet mulching, hand tools, incremental land clearing</li>\n</ul>\n\n<h3>10. Use and Value Diversity</h3>\n<p>Diversity reduces vulnerability and takes advantage of the unique nature of the environment.</p>\n<ul>\n  <li><strong>Application:</strong> Growing multiple crop varieties, keeping different animal breeds</li>\n  <li><strong>Examples:</strong> Polycultures, seed saving, heritage breeds</li>\n</ul>\n\n<h3>11. Use Edges and Value the Marginal</h3>\n<p>The interface between things is where the most interesting events take place.</p>\n<ul>\n  <li><strong>Application:</strong> Maximizing edge environments in design</li>\n  <li><strong>Examples:</strong> Keyhole beds, pond edges, hedgerows</li>\n</ul>\n\n<h3>12. Creatively Use and Respond to Change</h3>\n<p>We can have a positive impact on inevitable change by carefully observing and then intervening at the right time.</p>\n<ul>\n  <li><strong>Application:</strong> Anticipating natural successions, adapting to climate variations</li>\n  <li><strong>Examples:</strong> Managed succession, climate-adaptive species selection</li>\n</ul>',
            'excerpt': 'A comprehensive overview of permaculture design principles and their practical applications for sustainable land management.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1515150144380-bca9f1650ed9?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 1
        },
        {
            'id': 14,
            'category_id': 16,
            'title': 'Climate Feedback Loops Explained',
            'content': '<h1>Climate Feedback Loops Explained</h1>\n<p>Feedback loops are processes that can either amplify (positive feedback) or diminish (negative feedback) the effects of climate change. Understanding these mechanisms is crucial for climate modeling and prediction.</p>\n\n<h2>Positive Feedback Loops</h2>\n<p>These amplify the warming effect and can accelerate climate change:</p>\n\n<h3>Arctic Ice-Albedo Feedback</h3>\n<ul>\n  <li><strong>Process:</strong> As ice melts, darker ocean water is exposed, which absorbs more heat than reflective ice</li>\n  <li><strong>Result:</strong> More heat absorption leads to more ice melting, creating a self-reinforcing cycle</li>\n  <li><strong>Current status:</strong> Arctic sea ice has declined by approximately 13% per decade since satellite measurements began in 1979</li>\n</ul>\n\n<h3>Permafrost Methane Release</h3>\n<ul>\n  <li><strong>Process:</strong> Warming temperatures thaw permafrost, releasing trapped methane (a potent greenhouse gas)</li>\n  <li><strong>Result:</strong> More methane in the atmosphere increases warming, which thaws more permafrost</li>\n  <li><strong>Current status:</strong> An estimated 1.7 trillion tons of carbon is stored in permafrost, twice the amount currently in the atmosphere</li>\n</ul>\n\n<h3>Water Vapor Feedback</h3>\n<ul>\n  <li><strong>Process:</strong> Warmer air holds more water vapor (a greenhouse gas)</li>\n  <li><strong>Result:</strong> More water vapor traps more heat, causing further warming</li>\n  <li><strong>Current status:</strong> Atmospheric water vapor has increased by approximately 4% since 1970</li>\n</ul>\n\n<h3>Forest Dieback</h3>\n<ul>\n  <li><strong>Process:</strong> Climate change stresses forests through drought, fire, and pests</li>\n  <li><strong>Result:</strong> Declining forests absorb less CO2, leaving more in the atmosphere</li>\n  <li><strong>Current status:</strong> Amazon rainforest has lost approximately 17% of its forest cover over the past 50 years</li>\n</ul>\n\n<h2>Negative Feedback Loops</h2>\n<p>These tend to counteract warming, potentially stabilizing the climate:</p>\n\n<h3>Increased Plant Growth</h3>\n<ul>\n  <li><strong>Process:</strong> Higher CO2 levels and temperatures can increase plant growth in some regions</li>\n  <li><strong>Result:</strong> More plants absorb more CO2 from the atmosphere</li>\n  <li><strong>Limitations:</strong> Only effective up to certain temperature thresholds; benefits offset by increased plant respiration and climate-related disruptions</li>\n</ul>\n\n<h3>Cloud Formation</h3>\n<ul>\n  <li><strong>Process:</strong> Warmer temperatures increase evaporation and potentially cloud formation</li>\n  <li><strong>Result:</strong> Some cloud types reflect sunlight back to space, cooling the planet</li>\n  <li><strong>Complexity:</strong> Different cloud types and altitudes have varying effects, some actually warm the planet; one of the largest uncertainties in climate modeling</li>\n</ul>\n\n<h3>Ocean CO2 Absorption</h3>\n<ul>\n  <li><strong>Process:</strong> Oceans absorb CO2 from the atmosphere</li>\n  <li><strong>Result:</strong> Reduces atmospheric CO2 concentration, limiting warming</li>\n  <li><strong>Downside:</strong> Leads to ocean acidification, harming marine ecosystems; absorption efficiency decreases as oceans warm</li>\n</ul>\n\n<h2>Tipping Points</h2>\n<p>Some feedback systems have critical thresholds beyond which large, irreversible changes occur:</p>\n<ul>\n  <li><strong>West Antarctic Ice Sheet collapse:</strong> Could raise sea levels by 3+ meters</li>\n  <li><strong>Amazon rainforest dieback:</strong> Potential transition from rainforest to savanna</li>\n  <li><strong>Atlantic Meridional Overturning Circulation slowdown:</strong> Would significantly alter European climate</li>\n  <li><strong>Coral reef ecosystem collapse:</strong> Loss of biodiversity hotspots and coastal protection</li>\n</ul>\n\n<h2>Research Challenges</h2>\n<p>Scientists face several challenges in studying feedback loops:</p>\n<ul>\n  <li>Complex interactions between multiple feedback mechanisms</li>\n  <li>Time lags between cause and effect</li>\n  <li>Regional variations in feedback processes</li>\n  <li>Limited historical data for validation</li>\n  <li>Computational constraints in modeling</li>\n</ul>\n\n<h2>Implications</h2>\n<p>Understanding feedback loops has important implications:</p>\n<ul>\n  <li>Highlights the urgency of emissions reductions</li>\n  <li>Suggests potential for rapid, nonlinear climate change</li>\n  <li>Identifies key monitoring needs for early warning systems</li>\n  <li>Informs climate intervention and geoengineering proposals</li>\n</ul>',
            'excerpt': 'An in-depth explanation of climate feedback loops that can either amplify or diminish the effects of climate change.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1561553873-e8491a564fd0?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 3
        },
        {
            'id': 15,
            'category_id': 13,
            'title': 'Native Pollinators: Identification and Conservation',
            'content': '<h1>Native Pollinators: Identification and Conservation</h1>\n<p>Beyond honeybees, thousands of native pollinator species play crucial roles in ecosystem health and food production. This guide helps identify common native pollinators and outlines conservation strategies.</p>\n\n<h2>Importance of Native Pollinators</h2>\n<p>Native pollinators offer several advantages over introduced honeybees:</p>\n<ul>\n  <li>Adapted to local flora and environmental conditions</li>\n  <li>Active in diverse weather conditions (some can forage in cold or rain)</li>\n  <li>More efficient at pollinating certain native plants and crops</li>\n  <li>Provide resilience through pollinator diversity</li>\n  <li>Integral parts of food webs and ecosystem functions</li>\n</ul>\n\n<h2>Major Native Pollinator Groups</h2>\n\n<h3>Native Bees</h3>\n<p>With over 4,000 species in North America alone, native bees are diverse in size, appearance, and behavior:</p>\n\n<h4>Bumble Bees (<em>Bombus</em> spp.)</h4>\n<ul>\n  <li><strong>Identification:</strong> Large, fuzzy bees with black and yellow/orange bands</li>\n  <li><strong>Nesting:</strong> Social bees that nest in abandoned rodent burrows or other cavities</li>\n  <li><strong>Behavior:</strong> "Buzz pollinators" that vibrate flowers to release pollen</li>\n  <li><strong>Key features:</strong> Active in cool weather; excellent pollinators for tomatoes, blueberries, and other crops</li>\n</ul>\n\n<h4>Mason Bees (<em>Osmia</em> spp.)</h4>\n<ul>\n  <li><strong>Identification:</strong> Metallic blue/green/black, smaller than honeybees</li>\n  <li><strong>Nesting:</strong> Solitary bees that use hollow stems or holes in wood</li>\n  <li><strong>Behavior:</strong> Early spring emergence; carry pollen on specialized abdominal hairs</li>\n  <li><strong>Key features:</strong> Extremely efficient orchard pollinators; non-aggressive</li>\n</ul>\n\n<h4>Leafcutter Bees (<em>Megachile</em> spp.)</h4>\n<ul>\n  <li><strong>Identification:</strong> Medium-sized with striped abdomen; carry pollen on underside of abdomen</li>\n  <li><strong>Nesting:</strong> Cut circular pieces from leaves to line nest cells</li>\n  <li><strong>Behavior:</strong> Active in summer; efficient alfalfa pollinators</li>\n  <li><strong>Key features:</strong> Distinctive leaf-cutting behavior; rarely sting</li>\n</ul>\n\n<h4>Sweat Bees (Halictidae family)</h4>\n<ul>\n  <li><strong>Identification:</strong> Small (3-10mm), often metallic green or black</li>\n  <li><strong>Nesting:</strong> Usually ground nesters in bare or sparsely vegetated soil</li>\n  <li><strong>Behavior:</strong> Attracted to perspiration; some species social, others solitary</li>\n  <li><strong>Key features:</strong> Abundant and widespread; important pollinators of wildflowers and crops</li>\n</ul>\n\n<h3>Butterflies and Moths</h3>\n<p>Lepidopterans are important pollinators for certain plant species:</p>\n<ul>\n  <li><strong>Identification:</strong> Distinctive wings, long proboscis, clubbed antennae (butterflies) or feathery antennae (moths)</li>\n  <li><strong>Pollination role:</strong> Transfer pollen while feeding on nectar; specialized for flowers with deep tubes</li>\n  <li><strong>Key species:</strong> Monarch, swallowtails, sphinx moths, yucca moths (some with species-specific plant relationships)</li>\n</ul>\n\n<h3>Flies</h3>\n<p>Often overlooked but numerous fly species are important pollinators:</p>\n<ul>\n  <li><strong>Key groups:</strong> Hover flies (Syrphidae), bee flies (Bombyliidae), tachinid flies</li>\n  <li><strong>Identification:</strong> Hover flies often mimic bees/wasps with yellow and black patterns; single pair of wings</li>\n  <li><strong>Pollination role:</strong> Critical in cool, moist habitats and for early-blooming plants</li>\n</ul>\n\n<h3>Beetles</h3>\n<p>The most diverse pollinator group evolutionarily:</p>\n<ul>\n  <li><strong>Key families:</strong> Soldier beetles, longhorned beetles, scarab beetles</li>\n  <li><strong>Pollination role:</strong> Important for ancient flowering plants (magnolias, spicebush); "mess and soil" pollinators</li>\n</ul>\n\n<h2>Conservation Strategies</h2>\n\n<h3>Habitat Provision</h3>\n<ul>\n  <li><strong>Nesting sites:</strong> Maintain bare ground patches, dead wood, hollow stems, leaf litter</li>\n  <li><strong>Plant diversity:</strong> Provide diverse native flowering plants with sequential bloom periods</li>\n  <li><strong>Larval host plants:</strong> Include plants that support caterpillars and immature stages</li>\n</ul>\n\n<h3>Reduce Threats</h3>\n<ul>\n  <li><strong>Pesticide reduction:</strong> Minimize or eliminate insecticide use, especially neonicotinoids</li>\n  <li><strong>Disease management:</strong> Support research on pollinator diseases and parasites</li>\n  <li><strong>Habitat connectivity:</strong> Create pollinator corridors to connect fragmented habitats</li>\n</ul>\n\n<h3>Monitoring and Citizen Science</h3>\n<ul>\n  <li>Participate in pollinator counts and monitoring programs</li>\n  <li>Document pollinator diversity through photography and observation</li>\n  <li>Report sightings of rare or declining species to conservation organizations</li>\n</ul>\n\n<h3>Policy and Advocacy</h3>\n<ul>\n  <li>Support pollinator protection legislation</li>\n  <li>Advocate for pollinator-friendly land management practices</li>\n  <li>Promote integrated pest management in agricultural settings</li>\n</ul>',
            'excerpt': 'Learn to identify and support native pollinator species beyond honeybees, including conservation strategies for these essential ecosystem partners.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1475809913362-28a064062ccd?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 2
        }
    ]
    
    for wiki in wikis:
        created_at = datetime.now() - timedelta(days=random.randint(10, 60))
        updated_at = created_at + timedelta(days=random.randint(1, 10))
        views_count = random.randint(50, 1000)
        likes_count = random.randint(5, int(views_count * 0.1))
        
        query = """
        INSERT IGNORE INTO learning_materials
        (id, category_id, type, title, content, excerpt, thumbnail_url, author_id, 
        status, views_count, likes_count, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            wiki['id'],
            wiki['category_id'],
            'wiki',
            wiki['title'],
            wiki['content'],
            wiki['excerpt'],
            wiki['thumbnail_url'],
            wiki['author_id'],
            'published',
            views_count,
            likes_count,
            created_at,
            updated_at
        ))
    
    print(f"Added {len(wikis)} wiki learning materials.")

def seed_community_materials(cursor):
    """Seed community learning materials"""
    print("Seeding community learning materials...")
    
    communities = [
        {
            'id': 16,
            'category_id': 17,
            'title': 'How Our Community Reduced Waste by 50% in One Year',
            'content': '<h1>How Our Community Reduced Waste by 50% in One Year</h1>\n<p>Our neighborhood initiative to reduce waste achieved remarkable results through simple cooperative actions.</p>\n<h2>Key Actions</h2>\n<ul>\n<li>Community composting program</li>\n<li>Monthly repair cafe events</li>\n<li>Bulk buying club</li>\n<li>Tool library establishment</li>\n<li>Package-free shop support</li>\n</ul>\n<h2>Results</h2>\n<p>We tracked a 50% reduction in waste sent to landfill and built stronger community connections.</p>',
            'excerpt': 'A success story of how one community worked together to dramatically reduce waste through collaborative initiatives.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1523293182086-7651a899d37f?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 1,
            'duration': '5 min read'
        },
        {
            'id': 17,
            'category_id': 18,
            'title': 'Starting a Neighborhood Tree Planting Program',
            'content': '<h1>Starting a Neighborhood Tree Planting Program</h1>\n<p>Our experience creating a successful community tree planting initiative with limited resources.</p>\n<h2>Getting Started</h2>\n<ul>\n<li>Form a core committee</li>\n<li>Partner with local government</li>\n<li>Secure donated trees</li>\n<li>Map planting locations</li>\n<li>Recruit volunteers</li>\n</ul>\n<h2>Implementation</h2>\n<p>We planted 75 native trees in one weekend with 35 volunteers, focusing on public spaces and willing private properties.</p>',
            'excerpt': 'A practical guide to organizing and implementing a neighborhood tree planting program based on real community experience.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1444392061186-9fc38f84f726?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 2,
            'duration': '7 min read'
        },
        {
            'id': 18,
            'category_id': 19,
            'title': 'Five Simple Energy-Saving Changes Anyone Can Make',
            'content': '<h1>Five Simple Energy-Saving Changes Anyone Can Make</h1>\n<p>Community-tested tips that significantly reduce energy use without major lifestyle changes.</p>\n<h2>Effective Changes</h2>\n<ol>\n<li>Strategic LED bulb placement</li>\n<li>Smart power strip usage</li>\n<li>Thermal curtain installation</li>\n<li>Water heater temperature adjustment</li>\n<li>Refrigerator coil cleaning</li>\n</ol>\n<h2>Results</h2>\n<p>Community members implementing all five changes reported an average 18% reduction in energy bills.</p>',
            'excerpt': 'Community-tested tips for reducing energy consumption with minimal cost and effort that deliver meaningful savings.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 3,
            'duration': '4 min read'
        },
        {
            'id': 19,
            'category_id': 20,
            'title': 'The Case for Car-Free Streets in Urban Neighborhoods',
            'content': '<h1>The Case for Car-Free Streets in Urban Neighborhoods</h1>\n<p>How limited vehicle access can transform urban spaces into vibrant, safe, community-centered environments.</p>\n<h2>Benefits Observed</h2>\n<ul>\n<li>Increased foot traffic for local businesses</li>\n<li>Reduced air and noise pollution</li>\n<li>More children playing outdoors</li>\n<li>Stronger community connections</li>\n<li>Improved safety metrics</li>\n</ul>\n<h2>Implementation Approaches</h2>\n<p>From temporary weekend closures to permanent pedestrian zones, various models can work for different community contexts.</p>',
            'excerpt': 'Exploring the community and environmental benefits of car-free streets based on successful implementations worldwide.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1506003094589-53954a26283f?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 4,
            'duration': '6 min read'
        },
        {
            'id': 20,
            'category_id': 17,
            'title': 'How Our School Achieved Zero Waste Lunches',
            'content': '<h1>How Our School Achieved Zero Waste Lunches</h1>\n<p>Our elementary school eliminated lunch waste through a collaborative approach involving students, staff, and parents.</p>\n<h2>Key Components</h2>\n<ul>\n<li>Reusable container program</li>\n<li>On-site composting system</li>\n<li>Bulk food purchasing</li>\n<li>Student-led monitoring team</li>\n<li>Monthly waste audits</li>\n</ul>\n<h2>Outcomes</h2>\n<p>Besides eliminating 15 bags of daily waste, students developed environmental leadership skills and brought practices home.</p>',
            'excerpt': 'A success story from an elementary school that implemented a zero-waste lunch program through student-led initiatives.',
            'thumbnail_url': 'https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
            'author_id': 5,
            'duration': '5 min read'
        }
    ]
    
    for community in communities:
        created_at = datetime.now() - timedelta(days=random.randint(10, 60))
        updated_at = created_at + timedelta(days=random.randint(1, 10))
        views_count = random.randint(50, 1500)
        likes_count = random.randint(5, int(views_count * 0.1))
        
        query = """
        INSERT IGNORE INTO learning_materials
        (id, category_id, type, title, content, excerpt, thumbnail_url, author_id, 
        status, views_count, likes_count, duration, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            community['id'],
            community['category_id'],
            'community',
            community['title'],
            community['content'],
            community['excerpt'],
            community['thumbnail_url'],
            community['author_id'],
            'published',
            views_count,
            likes_count,
            community['duration'],
            created_at,
            updated_at
        ))
    
    print(f"Added {len(communities)} community learning materials.")

def seed_material_likes(cursor):
    """Seed learning material likes"""
    print("Seeding learning material likes...")
    
    cursor.execute("SELECT id FROM learning_materials")
    material_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate likes for materials
    material_likes = []
    like_id = 1
    
    for material_id in material_ids:
        num_likes = random.randint(3, 8)
        
        users = random.sample(range(1, 6), min(5, num_likes))
        
        for user_id in users:
            created_at = datetime.now() - timedelta(days=random.randint(1, 30))
            material_likes.append((like_id, material_id, user_id, created_at))
            like_id += 1
        
        cursor.execute("""
        UPDATE learning_materials
        SET likes_count = %s
        WHERE id = %s
        """, (len(users), material_id))
    
    if material_likes:
        query = """
        INSERT IGNORE INTO learning_material_likes
        (id, material_id, user_id, created_at)
        VALUES (%s, %s, %s, %s)
        """
        cursor.executemany(query, material_likes)
        print(f"Added {cursor.rowcount} learning material likes.")
    else:
        print("No learning material likes to add.")

def seed_material_comments(cursor):
    """Seed learning material comments"""
    print("Seeding learning material comments...")
    
    comment_contents = [
        "Great resource! I learned a lot from this.",
        "This information was exactly what I needed. Thank you!",
        "I appreciate the detailed explanation, very helpful.",
        "Interesting perspective on this topic. Got me thinking.",
        "Will definitely share this with others in my community.",
        "The practical tips are very useful. Already trying some of them.",
        "Clear and concise explanation of a complex topic.",
        "This has helped me understand the issue much better.",
        "Looking forward to more content like this!",
        "Are there any follow-up resources you'd recommend?",
        "This complements what I've been learning elsewhere. Thanks!",
        "Well-presented information with good examples.",
        "I had no idea about this aspect of environmental science.",
        "How does this apply to urban environments specifically?",
        "The visuals really helped explain the concepts."
    ]
    
    cursor.execute("SELECT id FROM learning_materials")
    material_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate comments for materials
    material_comments = []
    comment_id = 1
    
    for material_id in material_ids:
        num_comments = random.randint(0, 5)
        
        for _ in range(num_comments):
            user_id = random.randint(1, 5)
            content = random.choice(comment_contents)
            created_at = datetime.now() - timedelta(days=random.randint(1, 30))
            updated_at = created_at
            
            # Some comments get replies (parent comments)
            parent_id = None
            if random.random() < 0.3 and comment_id > 1:
                cursor.execute("""
                SELECT id FROM learning_material_comments 
                WHERE material_id = %s AND parent_id IS NULL
                ORDER BY RAND() LIMIT 1
                """, (material_id,))
                parent_result = cursor.fetchone()
                if parent_result:
                    parent_id = parent_result[0]
            
            material_comments.append((comment_id, material_id, user_id, parent_id, content, created_at, updated_at))
            comment_id += 1
    
    if material_comments:
        query = """
        INSERT IGNORE INTO learning_material_comments
        (id, material_id, user_id, parent_id, content, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(query, material_comments)
        print(f"Added {cursor.rowcount} learning material comments.")
    else:
        print("No learning material comments to add.")

def seed_material_comment_likes(cursor):
    """Seed learning material comment likes"""
    print("Seeding learning material comment likes...")
    
    cursor.execute("SELECT id FROM learning_material_comments")
    comment_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate likes for comments
    comment_likes = []
    like_id = 1
    
    for comment_id in comment_ids:
        if random.random() < 0.7:
            num_likes = random.randint(1, 3)
            
            users = random.sample(range(1, 6), min(5, num_likes))
            
            for user_id in users:
                created_at = datetime.now() - timedelta(days=random.randint(1, 30))
                like_type = 'like'
                comment_likes.append((like_id, comment_id, user_id, like_type, created_at))
                like_id += 1
    
    if comment_likes:
        query = """
        INSERT IGNORE INTO learning_material_comment_likes
        (id, comment_id, user_id, type, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.executemany(query, comment_likes)
        print(f"Added {cursor.rowcount} learning material comment likes.")
    else:
        print("No learning material comment likes to add.")

if __name__ == "__main__":
    seed_learning_data() 
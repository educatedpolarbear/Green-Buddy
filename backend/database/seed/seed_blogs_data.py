import sys
import os
import random
from datetime import datetime, timedelta
import json
import mysql.connector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from connection import Database

def create_blog_tables_if_not_exist(cursor):
    """Create all blog-related tables if they don't exist"""
    print("Creating blog tables if they don't exist...")
    
    # Create blog_tags table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `blog_tags` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `name` varchar(50) NOT NULL,
      `description` text DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `name` (`name`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create blog_posts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `blog_posts` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `title` varchar(255) NOT NULL,
      `content` text NOT NULL,
      `excerpt` text DEFAULT NULL,
      `author_id` bigint(20) NOT NULL,
      `is_featured` tinyint(1) DEFAULT 0,
      `views_count` int(11) DEFAULT 0,
      `status` enum('draft','published','archived') DEFAULT 'published',
      `comments_count` int(11) DEFAULT 0,
      `featured_image_url` varchar(255) DEFAULT NULL,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create blog_post_tags table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `blog_post_tags` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `post_id` int(11) NOT NULL,
      `tag_id` int(11) NOT NULL,
      PRIMARY KEY (`id`),
      UNIQUE KEY `post_tag` (`post_id`,`tag_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)
    
    # Create blog_comments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `blog_comments` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `post_id` int(11) NOT NULL,
    `user_id` bigint(20) NOT NULL,
    `content` text NOT NULL,
    `parent_id` int(11) DEFAULT NULL,
    `likes_count` int(11) DEFAULT 0,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """)
    
    # Create blog_likes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `blog_likes` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `user_id` bigint(20) NOT NULL,
    `post_id` int(11) DEFAULT NULL,
    `comment_id` int(11) DEFAULT NULL,
    `type` enum('like','dislike') NOT NULL,
    `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """);
    
    print("Blog tables created or already exist")

def seed_blog_data():
    """Seed data for blog-related tables"""
    try:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        create_blog_tables_if_not_exist(cursor)
        
        print("Starting blog data seeding...")
        
        seed_blog_tags(cursor)
        seed_blog_posts(cursor)
        seed_blog_post_tags(cursor)
        seed_blog_comments(cursor)
        seed_blog_likes(cursor)
        
        conn.commit()
        print("Blog data seeding completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

def seed_blog_tags(cursor):
    """Seed blog tags table"""
    print("Seeding blog tags...")
    
    tags = [
        (1, 'sustainability', 'Topics related to sustainable living and practices'),
        (2, 'eco-friendly', 'Environment-friendly initiatives and tips'),
        (3, 'green-tech', 'Technology solutions for environmental challenges'),
        (4, 'climate-action', 'Actions and initiatives addressing climate change'),
        (5, 'zero-waste', 'Tips and guides for zero waste lifestyle'),
        (6, 'renewable-energy', 'Information about renewable energy sources'),
        (7, 'conservation', 'Wildlife and nature conservation efforts'),
        (8, 'recycling', 'Recycling tips and best practices'),
        (9, 'organic', 'Organic farming and lifestyle'),
        (10, 'community', 'Community environmental initiatives'),
        (11, 'water-conservation', 'Water saving and conservation techniques'),
        (12, 'biodiversity', 'Protecting and promoting biodiversity'),
        (13, 'sustainable-fashion', 'Eco-friendly fashion and textiles'),
        (14, 'clean-energy', 'Clean and renewable energy solutions'),
        (15, 'environmental-education', 'Educational content about the environment')
    ]
    
    query = """
    INSERT IGNORE INTO blog_tags (id, name, description)
    VALUES (%s, %s, %s)
    """
    cursor.executemany(query, tags)
    print(f"Added {cursor.rowcount} blog tags.")

def seed_blog_posts(cursor):
    """Seed blog posts table"""
    print("Seeding blog posts...")
    
    cursor.execute("SELECT id FROM users LIMIT 10")
    user_ids = [row[0] for row in cursor.fetchall()]
    
    if not user_ids:
        print("No users found in the database. Please seed user data first.")
        user_ids = [1]  # Default to user ID 1 if no users exist
    
    posts = [
        {
            'title': 'Understanding Carbon Footprints: A Comprehensive Guide',
            'content': """<p>Carbon footprints are a measure of the total greenhouse gas emissions caused directly and indirectly by an individual, organization, event, or product. Understanding your carbon footprint is the first step towards reducing your environmental impact.</p>
            
            <h2>What Contributes to Your Carbon Footprint?</h2>
            <ul>
                <li>Transportation (cars, planes, public transport)</li>
                <li>Home energy use (electricity, heating, cooling)</li>
                <li>Food consumption (especially meat and dairy)</li>
                <li>Shopping habits and consumption of goods</li>
                <li>Waste disposal and recycling practices</li>
            </ul>
            
            <h2>How to Calculate Your Carbon Footprint</h2>
            <p>Several online calculators can help you estimate your carbon footprint based on your lifestyle. These tools typically ask questions about your transportation habits, home energy use, diet, and consumption patterns.</p>
            
            <h2>Simple Steps to Reduce Your Carbon Footprint</h2>
            <ol>
                <li>Use public transportation, carpool, bike, or walk when possible</li>
                <li>Reduce meat consumption and food waste</li>
                <li>Use energy-efficient appliances and lighting</li>
                <li>Minimize air travel</li>
                <li>Buy local and seasonal products</li>
                <li>Reduce, reuse, and recycle</li>
                <li>Support renewable energy</li>
            </ol>
            
            <p>Remember, even small changes in your daily habits can significantly reduce your carbon footprint over time.</p>""",
            'excerpt': 'Learn about carbon footprints, how they\'re calculated, and simple steps to reduce your environmental impact.',
            'is_featured': True,
            'views_count': random.randint(100, 500),
            'featured_image_url': 'https://images.unsplash.com/photo-1529773464063-f6810c569277?q=80&w=1935&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'
        },
        {
            'title': 'Sustainable Gardening: Growing Food in Small Spaces',
            'content': """<p>You don't need a large backyard to grow your own food. Urban gardening in small spaces is not only possible but can be highly productive and rewarding.</p>
            
            <h2>Container Gardening Basics</h2>
            <p>Almost any vegetable that grows in a garden will also do well in a container. Some plants that thrive in containers include:</p>
            <ul>
                <li>Tomatoes</li>
                <li>Lettuce and other leafy greens</li>
                <li>Herbs (basil, mint, cilantro)</li>
                <li>Peppers</li>
                <li>Radishes</li>
            </ul>
            
            <h2>Vertical Gardening Solutions</h2>
            <p>When floor space is limited, grow up! Vertical gardening maximizes your growing area:</p>
            <ul>
                <li>Trellises for climbing plants like cucumbers and beans</li>
                <li>Wall-mounted planters</li>
                <li>Hanging baskets for strawberries and trailing herbs</li>
                <li>Tiered plant stands</li>
            </ul>
            
            <h2>Balcony and Window Gardening</h2>
            <p>Even the smallest outdoor space can become productive:</p>
            <ul>
                <li>Window boxes for herbs and salad greens</li>
                <li>Railing planters for small vegetables</li>
                <li>Dwarf varieties bred for small spaces</li>
            </ul>
            
            <h2>Sustainable Practices</h2>
            <ul>
                <li>Collect rainwater for irrigation</li>
                <li>Compost kitchen scraps for natural fertilizer</li>
                <li>Choose organic pest control methods</li>
                <li>Select appropriate plants for your climate</li>
            </ul>
            
            <p>With a little creativity and planning, you can grow fresh, organic produce regardless of how small your living space might be.</p>""",
            'excerpt': 'Discover how to grow your own food in small spaces using container and vertical gardening techniques.',
            'is_featured': False,
            'views_count': random.randint(100, 500),
            'featured_image_url': 'https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?q=80&w=1000&auto=format&fit=crop'
        },
        {
            'title': 'Biophilic Design: Bringing Nature Into Your Home',
            'content': """<p>Biophilic design is an innovative approach that seeks to connect people more closely to nature through architecture and interior design. This concept recognizes humans' innate need to connect with natural systems and processes.</p>
            
            <h2>Key Elements of Biophilic Design</h2>
            
            <h3>1. Direct Nature Connections</h3>
            <ul>
                <li>Indoor plants and living walls</li>
                <li>Natural light and ventilation</li>
                <li>Water features</li>
                <li>Views of nature</li>
            </ul>
            
            <h3>2. Natural Materials and Textures</h3>
            <ul>
                <li>Wood, stone, and other natural materials</li>
                <li>Organic shapes and forms</li>
                <li>Natural color palettes</li>
                <li>Variety of textures that mimic nature</li>
            </ul>
            
            <h3>3. Natural Patterns and Processes</h3>
            <ul>
                <li>Fractals and patterns that occur in nature</li>
                <li>Dynamic and diffuse light</li>
                <li>Sensory variability</li>
            </ul>
            
            <h2>Benefits of Biophilic Design</h2>
            <ul>
                <li>Reduced stress and improved well-being</li>
                <li>Enhanced creativity and cognitive function</li>
                <li>Improved air quality</li>
                <li>Connection to natural cycles</li>
                <li>Greater sense of place and belonging</li>
            </ul>
            
            <h2>Simple Ways to Incorporate Biophilic Design</h2>
            <ul>
                <li>Add a variety of houseplants</li>
                <li>Maximize natural light</li>
                <li>Choose natural materials for furniture and decor</li>
                <li>Incorporate nature-inspired artwork</li>
                <li>Create views to the outdoors</li>
                <li>Use natural scents like essential oils</li>
            </ul>
            
            <p>By thoughtfully incorporating elements of nature into our homes, we can create spaces that support our health, productivity, and connection to the natural world.</p>""",
            'excerpt': 'Learn how biophilic design principles can transform your living space and improve well-being by connecting you with nature.',
            'is_featured': False,
            'views_count': random.randint(100, 500),
            'featured_image_url': 'https://images.unsplash.com/photo-1493552152660-f915ab47ae9d?q=80&w=1000&auto=format&fit=crop'
        },
        {
            'title': 'The Environmental Impact of Fast Fashion',
            'content': """<p>Fast fashion has revolutionized the clothing industry, but at a significant environmental cost. Understanding these impacts can help us make more sustainable choices.</p>
            
            <h2>What Is Fast Fashion?</h2>
            <p>Fast fashion refers to inexpensive, trendy clothing that samples ideas from fashion shows and celebrity culture but is mass-produced at low cost. The result is a business model built on quick turnover of styles, encouraging consumers to frequently update their wardrobes.</p>
            
            <h2>Environmental Impacts</h2>
            
            <h3>Water Pollution and Consumption</h3>
            <p>The fashion industry is the second-largest consumer of water and produces 20% of global wastewater. Textile dyeing is the second largest polluter of water globally.</p>
            
            <h3>Textile Waste</h3>
            <p>The average consumer throws away 70 pounds (31.75 kg) of clothing per year. Globally, we produce 13 million tons of textile waste annually, 95% of which could be reused or recycled.</p>
            
            <h3>Carbon Footprint</h3>
            <p>The fashion industry produces 10% of global carbon emissions, more than international flights and maritime shipping combined.</p>
            
            <h3>Microplastic Pollution</h3>
            <p>Synthetic fabrics like polyester shed microplastics when washed, which end up in our oceans and eventually in the food chain.</p>
            
            <h2>Sustainable Alternatives</h2>
            
            <h3>Slow Fashion</h3>
            <ul>
                <li>Buy fewer, higher-quality pieces that last longer</li>
                <li>Choose timeless styles over trendy items</li>
                <li>Research brands' environmental practices</li>
            </ul>
            
            <h3>Secondhand Shopping</h3>
            <ul>
                <li>Thrift stores and vintage shops</li>
                <li>Online marketplaces for used clothing</li>
                <li>Clothing swaps with friends</li>
            </ul>
            
            <h3>Sustainable Fabrics</h3>
            <ul>
                <li>Organic cotton (uses 88% less water and 62% less energy)</li>
                <li>Hemp (requires minimal water and no pesticides)</li>
                <li>Linen (made from flax, a renewable resource)</li>
                <li>Recycled materials</li>
            </ul>
            
            <p>By making more conscious choices about our clothing, we can reduce our environmental impact while still expressing our personal style.</p>""",
            'excerpt': 'Explore the environmental consequences of fast fashion and discover sustainable alternatives for your wardrobe.',
            'is_featured': False,
            'views_count': random.randint(100, 500),
            'featured_image_url': 'https://images.unsplash.com/photo-1523381294911-8d3cead13475?q=80&w=1000&auto=format&fit=crop'
        },
        {
            'title': 'Renewable Energy Innovations Changing Our World',
            'content': """<p>The renewable energy sector is experiencing rapid innovation, with new technologies promising to accelerate our transition to a clean energy future.</p>
            
            <h2>Solar Energy Breakthroughs</h2>
            
            <h3>Perovskite Solar Cells</h3>
            <p>These newer solar cells can be produced at lower temperatures using less energy and fewer materials than traditional silicon cells. They're approaching efficiency levels of 25%, making them competitive with conventional solar panels while potentially being much cheaper to produce.</p>
            
            <h3>Building-Integrated Photovoltaics (BIPV)</h3>
            <p>Solar cells are being integrated directly into building materials like windows, facades, and roofing tiles, turning entire buildings into power generators without sacrificing aesthetics.</p>
            
            <h2>Wind Energy Innovations</h2>
            
            <h3>Bladeless Wind Turbines</h3>
            <p>These innovative designs capture wind energy without rotating blades, reducing noise, visual impact, and danger to birds. They operate using vortex shedding, where wind causes the structure to oscillate and generate electricity from this movement.</p>
            
            <h3>Floating Offshore Wind Farms</h3>
            <p>These platforms can be installed in deeper waters farther from shore, accessing stronger, more consistent winds while reducing visual impact and conflicts with coastal activities.</p>
            
            <h2>Energy Storage Solutions</h2>
            
            <h3>Flow Batteries</h3>
            <p>Unlike conventional batteries, flow batteries store energy in liquid electrolyte solutions, allowing for independent scaling of power and energy capacity. They can provide long-duration storage for grid applications with minimal degradation over thousands of cycles.</p>
            
            <h3>Gravitational Energy Storage</h3>
            <p>These systems store energy by lifting heavy weights when excess power is available, then generating electricity by lowering them when energy is needed. They offer long-duration storage without the chemical limitations of batteries.</p>
            
            <h2>The Future of Renewable Energy</h2>
            <p>As these innovations mature and scale, renewable energy will become increasingly affordable, reliable, and accessible worldwide. Combined with smart grids and energy efficiency measures, these technologies are paving the way for a sustainable energy future.</p>
            
            <p>The transition to renewable energy isn't just an environmental imperative—it's becoming an economic opportunity and technological revolution that will reshape how we power our world.</p>""",
            'excerpt': 'Discover the cutting-edge innovations in renewable energy that are accelerating our transition to a sustainable future.',
            'is_featured': True,
            'views_count': random.randint(100, 500),
            'featured_image_url': 'https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?q=80&w=1000&auto=format&fit=crop'
        }
    ]
    
    for i, post in enumerate(posts, 1):
        author_id = random.choice(user_ids)
        created_at = datetime.now() - timedelta(days=random.randint(1, 30))
        updated_at = created_at + timedelta(days=random.randint(0, 5))
        
        query = """
        INSERT IGNORE INTO blog_posts 
        (id, title, content, author_id, excerpt, featured_image_url, views_count, comments_count, is_featured, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            i,
            post['title'],
            post['content'],
            author_id,
            post['excerpt'],
            post['featured_image_url'],
            post['views_count'],
            0,
            post['is_featured'],
            'published',
            created_at,
            updated_at
        ))
    
    print(f"Added {cursor.rowcount} blog posts.")

def seed_blog_post_tags(cursor):
    """Seed blog post tags relationships"""
    print("Seeding blog post tags relationships...")
    
    cursor.execute("SELECT id FROM blog_posts")
    post_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM blog_tags")
    tag_ids = [row[0] for row in cursor.fetchall()]
    
    post_tags = []
    relationship_id = 1
    
    for post_id in post_ids:
        num_tags = random.randint(2, 4)
        post_tags_ids = random.sample(tag_ids, min(num_tags, len(tag_ids)))
        
        for tag_id in post_tags_ids:
            post_tags.append((relationship_id, post_id, tag_id))
            relationship_id += 1
    
    query = """
    INSERT IGNORE INTO blog_post_tags (id, post_id, tag_id)
    VALUES (%s, %s, %s)
    """
    cursor.executemany(query, post_tags)
    print(f"Added {cursor.rowcount} blog post tag relationships.")

def seed_blog_comments(cursor):
    """Seed blog comments"""
    print("Seeding blog comments...")
    
    cursor.execute("SELECT id FROM blog_posts")
    post_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM users LIMIT 10")
    user_ids = [row[0] for row in cursor.fetchall()]
    
    if not user_ids:
        print("No users found in the database. Using default user ID 1.")
        user_ids = [1]
    
    comment_templates = [
        "Great article! I learned a lot about {topic}.",
        "This is exactly what I've been looking for. The information about {topic} is especially helpful.",
        "I've been implementing some of these tips and they've made a real difference.",
        "Thanks for sharing this. I'll definitely be trying out the suggestions on {topic}.",
        "Well-written and informative. I hadn't considered the impact of {topic} before reading this.",
        "This post inspired me to make some changes in how I approach {topic}.",
        "Do you have any additional resources about {topic}? I'd love to learn more.",
        "I've shared this with my friends who are also interested in {topic}.",
        "The section on {topic} was particularly eye-opening for me.",
        "Looking forward to more content like this!"
    ]
    
    topics = [
        "sustainable living",
        "renewable energy",
        "reducing waste",
        "eco-friendly products",
        "carbon footprint reduction",
        "gardening",
        "biophilic design",
        "sustainable fashion",
        "energy conservation",
        "environmental impact"
    ]
    
    comments = []
    comment_id = 1
    
    for post_id in post_ids:
        num_comments = random.randint(3, 8)
        
        for _ in range(num_comments):
            user_id = random.choice(user_ids)
            comment_template = random.choice(comment_templates)
            topic = random.choice(topics)
            content = comment_template.format(topic=topic)
            created_at = datetime.now() - timedelta(days=random.randint(0, 28))
            
            comments.append((comment_id, post_id, user_id, content, None, 0, created_at))
            comment_id += 1
    
    query = """
    INSERT IGNORE INTO blog_comments (id, post_id, user_id, content, parent_id, likes_count, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(query, comments)
    print(f"Added {cursor.rowcount} blog comments.")
    
    for post_id in post_ids:
        cursor.execute("SELECT COUNT(*) FROM blog_comments WHERE post_id = %s", (post_id,))
        comment_count = cursor.fetchone()[0]
        
        cursor.execute("UPDATE blog_posts SET comments_count = %s WHERE id = %s", (comment_count, post_id))

def seed_blog_likes(cursor):
    """Seed blog likes"""
    print("Seeding blog likes...")
    
    cursor.execute("SELECT id FROM blog_posts")
    post_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM blog_comments")
    comment_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM users LIMIT 15")
    user_ids = [row[0] for row in cursor.fetchall()]
    
    if not user_ids:
        print("No users found in the database. Using default user ID 1.")
        user_ids = [1]
    
    post_likes = []
    comment_likes = []
    like_id = 1
    
    # Generate likes for posts
    for post_id in post_ids:
        num_likes = int(len(user_ids) * random.uniform(0.4, 0.7))
        liking_users = random.sample(user_ids, num_likes)
        
        for user_id in liking_users:
            created_at = datetime.now() - timedelta(days=random.randint(0, 28))
            post_likes.append((like_id, user_id, post_id, None, 'like', created_at))
            like_id += 1
    
    # Generate likes for comments
    for comment_id in comment_ids:
        num_likes = int(len(user_ids) * random.uniform(0.1, 0.3))
        liking_users = random.sample(user_ids, num_likes)
        
        for user_id in liking_users:
            created_at = datetime.now() - timedelta(days=random.randint(0, 28))
            comment_likes.append((like_id, user_id, None, comment_id, 'like', created_at))
            like_id += 1
    
    all_likes = post_likes + comment_likes
    
    query = """
    INSERT IGNORE INTO blog_likes (id, user_id, post_id, comment_id, type, created_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(query, all_likes)
    print(f"Added {cursor.rowcount} blog likes.")
    
    for comment_id in comment_ids:
        cursor.execute("SELECT COUNT(*) FROM blog_likes WHERE comment_id = %s", (comment_id,))
        likes_count = cursor.fetchone()[0]
        
        cursor.execute("UPDATE blog_comments SET likes_count = %s WHERE id = %s", (likes_count, comment_id))

if __name__ == "__main__":
    seed_blog_data() 
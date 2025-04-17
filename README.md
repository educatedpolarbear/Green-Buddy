# Green Buddy Application

## Getting Started

1. Use `setup.bat` to install dependencies and set up the web app.
2. After setup, use `run.bat` to run the server.
3. Make sure phpMyAdmin MySQL server is running before starting the application.

## Running the Application

- The first time, run `setup.bat` to install all dependencies.
- For subsequent runs, you can directly use `run.bat` (no need to setup again, building the frontend might take a while).
- The web application can be accessed at http://localhost:3000

## User Credentials

### Admin User
- Username: admin_user
- Email: admin@greenbuddy.com
- Password: Admin123!

### Moderator Users
- Username: mod_sarah
- Email: sarah@greenbuddy.com  
- Password: Mod123!

- Username: mod_david
- Email: david@greenbuddy.com
- Password: Mod123!

### Regular Users
- Username: eco_alex
- Email: alex@example.com
- Password: User123!

- Username: green_mike
- Email: mike@example.com
- Password: User123!

- Username: earth_lisa
- Email: lisa@example.com
- Password: User123!

# Features description:

### Core Features

1. Achievement System: 
   Track user achievements with:
   - EXP rewards and leveling system
   - Multi-category achievements system
   - Automatically award achievements and send real-time notifications

2. Authentication System: 
   Security framework with:
   - JWT token authentication
   - Different roles: admin, user, moderator
   - Password validation system

3. Events System: 
   Event management system including:
   - Event creation that support rich details
   - Participant registration tracking
   - Voting system for events
   - Comments sections for events
   - Location using Google Maps

4. Blog System: 
   Blog system including:
   - Rich text article creation with media support
   - Categories system and trending content selection
   - Comments section
   - Search bar
   - View tracking system
   - Tag filtering system

5. Chat System: 
   Real-time chatting system:
   - Participant tracking and message history
   - Socket.IO for real-time communication
   - Presence indicators and typing status
   - Support for group messaging

6. Notification System: 
   Notifications system consists of:
   - Websocket for real-time notification sending
   - Read/unread status tracking
   - Read all feature.
   - Multiple notification types

7. Groups System: 
   Group features include
   - Role-based membership management
   - Comments or each posts
   - Group chat feature
   - Search bar
   - Activity feeds for group page

8. Challenges System: 
   Challenges system containing rich features such as:
   - Multiple challenge categories (daily, weekly, monthly) with corresponding reward
   - Progress tracking and submission verification
   - Leaderboards for user with the most exp
   - Moderation panel for approving or rejecting submissions

9. Learning System: 
   Educational platform featuring:
   - Diverse content types (articles, videos, courses, community)
   - View and completion tracking
   - Related material recommendation
   - Comments section

10. Forum System: 
    Discussion platform providing:
    - Comments section with likes and nested replies.
    - Solution marking feature
    - Engagement tracking (likes, views, replies)
    - Content editting tools
    - Related content recommendations

11. Users System: 
    User information management with:
    - Basic information and secure authentication
    - Profile customization and privacy controls
    - Follow/unfollow feature
    - Activity and achievements tracking
    - Public and private profile views

### Frontend additional features
1. Middleware API Security:
    - Centralized authentication and token validation  
    - API handling to avoid code duplication
    - Standardized error handling
    - CORS and rate limiting

2. Modern, Responsive Design:
    - Modern, responsive and intuitive design.
    - Optimized performance and accessibility
    - Smooth animations and transitions
    - Nice constrast nature theme.


## Bug Reports

If you encounter any bugs or issues while using the application, please report them by sending an email to:

trung.dangquoc@hcmut.edu.vn

Made with claude, v0 and a lot of coffee ☕


from models.notification import Notification
from database.connection import Database
from enum import Enum
import json

class ChallengeCategory(Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    ONE_TIME = 'one_time'

class ChallengeDifficulty(Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'
    EXPERT = 'expert'

class Challenge:
    @staticmethod
    def get_all(category=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    c.*,
                    COUNT(DISTINCT cs.user_id) as participants_count,
                    COUNT(DISTINCT CASE WHEN cs.status = 'completed' THEN cs.user_id END) as completions_count
                FROM challenges c
                LEFT JOIN challenge_status cs ON c.id = cs.challenge_id
                WHERE c.is_active = TRUE
            """
            params = []
            
            if category:
                if isinstance(category, ChallengeCategory):
                    category = category.value
                query += " AND c.category = %s"
                params.append(category)
            
            query += " GROUP BY c.id ORDER BY c.difficulty ASC, c.title ASC"
            
            cursor.execute(query, params)
            challenges = cursor.fetchall()
            
            return challenges
        except Exception as e:
            print(f"Error in get_all: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(challenge_id, user_id=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    c.*,
                    COUNT(DISTINCT cs.user_id) as participants_count,
                    COUNT(DISTINCT CASE WHEN cs.status = 'completed' THEN cs.user_id END) as completions_count,
                    user_status.status as user_status,
                    user_status.progress as user_progress
                FROM challenges c
                LEFT JOIN challenge_status cs ON c.id = cs.challenge_id
                LEFT JOIN challenge_status user_status ON c.id = user_status.challenge_id AND user_status.user_id = %s
                WHERE c.id = %s
                GROUP BY c.id
            """
            
            cursor.execute(query, (user_id, challenge_id) if user_id else (None, challenge_id))
            challenge = cursor.fetchone()
            
            return challenge
        except Exception as e:
            print(f"Error in get_by_id: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def create(title, description, category, difficulty, exp_reward, requirements=None, resources=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            if isinstance(category, ChallengeCategory):
                category = category.value
            elif category not in [c.value for c in ChallengeCategory]:
                raise ValueError(f"Invalid category: {category}")
            
            if isinstance(difficulty, ChallengeDifficulty):
                difficulty = difficulty.value
            elif difficulty not in [d.value for d in ChallengeDifficulty]:
                raise ValueError(f"Invalid difficulty: {difficulty}")
            
            query = """
                INSERT INTO challenges (
                    title, description, category, difficulty,
                    exp_reward, requirements, resources, is_active, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
            """
            
            cursor.execute(query, (
                title, description, category, difficulty,
                exp_reward, requirements, resources
            ))
            
            conn.commit()
            challenge_id = cursor.lastrowid
            
            return Challenge.get_by_id(challenge_id)
        except Exception as e:
            conn.rollback()
            print(f"Error in create: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update(challenge_id, title=None, description=None, category=None, 
              difficulty_level=None, exp_reward=None, requirements=None, resources=None, is_active=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            
            if category is not None:
                if isinstance(category, ChallengeCategory):
                    category = category.value
                elif category not in [c.value for c in ChallengeCategory]:
                    raise ValueError(f"Invalid category: {category}")
                updates.append("category = %s")
                params.append(category)
            
            if difficulty_level is not None:
                if isinstance(difficulty_level, ChallengeDifficulty):
                    difficulty_level = difficulty_level.value
                elif difficulty_level not in [d.value for d in ChallengeDifficulty]:
                    raise ValueError(f"Invalid difficulty level: {difficulty_level}")
                updates.append("difficulty_level = %s")
                params.append(difficulty_level)
            
            if exp_reward is not None:
                updates.append("exp_reward = %s")
                params.append(exp_reward)
            
            if requirements is not None:
                updates.append("requirements = %s")
                params.append(requirements)
            
            if resources is not None:
                updates.append("resources = %s")
                params.append(resources)
            
            if is_active is not None:
                updates.append("is_active = %s")
                params.append(is_active)
            
            if updates:
                query = f"UPDATE challenges SET {', '.join(updates)} WHERE id = %s"
                params.append(challenge_id)
                
                cursor.execute(query, params)
                conn.commit()
            
            return Challenge.get_by_id(challenge_id)
        except Exception as e:
            conn.rollback()
            print(f"Error in update: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def start(challenge_id, user_id):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT id FROM challenges 
                WHERE id = %s AND is_active = TRUE
            """, (challenge_id,))
            
            challenge = cursor.fetchone()
            if not challenge:
                raise ValueError("Challenge not found or is not active")

            cursor.execute("""
                SELECT id, status FROM challenge_status 
                WHERE challenge_id = %s AND user_id = %s
            """, (challenge_id, user_id))
            
            existing = cursor.fetchone()
            if existing:
                if existing['status'] == 'completed':
                    raise ValueError("Challenge already completed")
                elif existing['status'] == 'in_progress':
                    raise ValueError("Challenge already in progress")

            cursor.execute("""
                INSERT INTO challenge_status (
                    challenge_id, user_id, status, progress, started_at
                ) VALUES (%s, %s, 'in_progress', 0, NOW())
            """, (challenge_id, user_id))
            
            conn.commit()

            cursor.execute("""
                SELECT 
                    cs.*,
                    c.title,
                    c.description,
                    c.category,
                    c.difficulty,
                    c.exp_reward
                FROM challenge_status cs
                JOIN challenges c ON cs.challenge_id = c.id
                WHERE cs.challenge_id = %s AND cs.user_id = %s
            """, (challenge_id, user_id))
            
            result = cursor.fetchone()
            return result

        except Exception as e:
            print(f"Error in start: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update_progress(challenge_id, user_id, progress):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                UPDATE challenge_status 
                SET progress = %s, updated_at = NOW()
                WHERE challenge_id = %s AND user_id = %s AND status = 'in_progress'
                """,
                (progress, challenge_id, user_id)
            )
            
            conn.commit()
            return {"message": "Progress updated successfully"}
        except Exception as e:
            conn.rollback()
            print(f"Error in update_progress: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def submit_challenge(challenge_id, user_id, proof_text, proof_urls=None):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT cs.status, c.exp_reward
                FROM challenge_status cs
                JOIN challenges c ON cs.challenge_id = c.id
                WHERE cs.challenge_id = %s AND cs.user_id = %s
                """,
                (challenge_id, user_id)
            )
            status = cursor.fetchone()
            
            if not status:
                raise ValueError("Challenge not started")
            if status['status'] == 'completed':
                raise ValueError("Challenge already completed")
            
            # Create submission
            cursor.execute(
                """
                INSERT INTO challenge_submissions (
                    challenge_id, user_id, proof_text, proof_urls, submitted_at, status
                ) VALUES (%s, %s, %s, %s, NOW(), 'pending')
                """,
                (challenge_id, user_id, proof_text, proof_urls)
            )
            
            cursor.execute(
                """
                UPDATE challenge_status 
                SET status = 'submitted', updated_at = NOW()
                WHERE challenge_id = %s AND user_id = %s
                """,
                (challenge_id, user_id)
            )
            
            conn.commit()
            return {"message": "Challenge submitted successfully"}
        except Exception as e:
            conn.rollback()
            print(f"Error in submit_challenge: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_pending_submissions():
        db = Database()
        conn = None
        cursor = None
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    s.id as submission_id,
                    s.challenge_id,
                    s.user_id,
                    s.proof_text,
                    s.proof_urls,
                    s.created_at as submitted_at,
                    c.title as challenge_title,
                    c.description as challenge_description,
                    c.exp_reward,
                    u.username as submitter_username
                FROM challenge_submissions s
                JOIN challenges c ON s.challenge_id = c.id
                JOIN users u ON s.user_id = u.id
                WHERE s.status = 'pending'
                ORDER BY s.created_at ASC
            """
            
            cursor.execute(query)
            submissions = cursor.fetchall()
            
            for submission in submissions:
                if submission['proof_urls']:
                    try:
                        submission['proof_urls'] = json.loads(submission['proof_urls'])
                    except:
                        submission['proof_urls'] = []
            
            return submissions

        except Exception as e:
            print(f"Error in get_pending_submissions: {str(e)}")
            raise e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_categories():
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT c.*, COUNT(ch.id) as challenge_count
                FROM categories c
                LEFT JOIN challenges ch ON c.id = ch.category_id
                GROUP BY c.id
                ORDER BY c.name
            """)
            
            return cursor.fetchall()
        except Exception as e:
            print(f"Error in get_categories: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def submit(challenge_id, user_id, submission):
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT id FROM challenges 
                WHERE id = %s AND is_active = TRUE
            """, (challenge_id,))
            
            challenge = cursor.fetchone()
            if not challenge:
                raise ValueError("Challenge not found or is not active")

            cursor.execute("""
                SELECT id, status FROM challenge_status 
                WHERE challenge_id = %s AND user_id = %s
            """, (challenge_id, user_id))
            
            existing = cursor.fetchone()
            if not existing:
                raise ValueError("You must start the challenge before submitting")
            if existing['status'] == 'completed':
                raise ValueError("Challenge already completed")

            # Validate submission
            if not isinstance(submission, dict):
                raise ValueError("Invalid submission format")
            if 'text' not in submission:
                raise ValueError("Submission must include text")
            if len(submission['text'].strip()) < 20:
                raise ValueError("Submission text must be at least 20 characters")

            proof_urls = submission.get('urls')
            if proof_urls:
                proof_urls = json.dumps(proof_urls)

            cursor.execute("""
                INSERT INTO challenge_submissions (
                    challenge_id, user_id, proof_text, proof_urls
                ) VALUES (%s, %s, %s, %s)
            """, (
                challenge_id,
                user_id,
                submission['text'],
                proof_urls
            ))
            
            cursor.execute("""
                UPDATE challenge_status 
                SET status = 'submitted'
                WHERE challenge_id = %s AND user_id = %s
            """, (challenge_id, user_id))
            
            conn.commit()

            cursor.execute("""
                SELECT 
                    cs.*,
                    c.title,
                    c.description,
                    c.category,
                    c.difficulty,
                    c.exp_reward
                FROM challenge_status cs
                JOIN challenges c ON cs.challenge_id = c.id
                WHERE cs.challenge_id = %s AND cs.user_id = %s
            """, (challenge_id, user_id))
            
            result = cursor.fetchone()
            return result

        except Exception as e:
            conn.rollback()
            print(f"Error in submit: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def review_submission(submission_id: int, is_approved: bool, feedback: str = None) -> bool:
        # Review a challenge submission and update both challenge_submissions and challenge_status tables.
        db = Database()
        conn = None
        cursor = None
        submission_data = None
        
        try:
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    cs.*, 
                    c.exp_reward, 
                    c.title as challenge_title, 
                    u.id as user_id,
                    u.username as username
                FROM challenge_submissions cs
                JOIN challenges c ON cs.challenge_id = c.id
                JOIN users u ON cs.user_id = u.id
                WHERE cs.id = %s AND cs.status = 'pending'
            """, (submission_id,))
            
            submission = cursor.fetchone()
            if not submission:
                print(f"No pending submission found with ID {submission_id}")
                return False

            submission_data = {
                'user_id': submission['user_id'],
                'username': submission['username'],
                'challenge_title': submission['challenge_title'],
                'exp_reward': submission['exp_reward'],
                'challenge_id': submission['challenge_id']
            }

            cursor.execute("""
                UPDATE challenge_submissions 
                SET status = %s,
                    feedback = %s,
                    reviewed_at = NOW()
                WHERE id = %s AND status = 'pending'
            """, ('approved' if is_approved else 'rejected', feedback, submission_id))

            if cursor.rowcount == 0:
                print(f"Submission {submission_id} was already reviewed")
                return False

            cursor.execute("""
                UPDATE challenge_status 
                SET status = %s,
                    feedback = %s,
                    completed_at = CASE WHEN %s THEN NOW() ELSE NULL END
                WHERE challenge_id = %s AND user_id = %s AND status = 'submitted'
            """, (
                'completed' if is_approved else 'in_progress',
                feedback,
                is_approved,
                submission_data['challenge_id'],
                submission_data['user_id']
            ))

            if is_approved:
                cursor.execute("""
                    UPDATE users 
                    SET exp = exp + %s 
                    WHERE id = %s
                """, (submission_data['exp_reward'], submission_data['user_id']))
                
                try:
                    from models.user_stats import UserStats
                    UserStats.update_stat_and_achievements(
                        submission_data['user_id'], 
                        'challenges_completed',
                        {
                            'challenge_id': submission_data['challenge_id'],
                            'challenge_title': submission_data['challenge_title']
                        }
                    )
                except Exception as e:
                    print(f"Error updating stats: {str(e)}")

            conn.commit()
            print(f"Successfully reviewed submission {submission_id}")

        except Exception as e:
            print(f"Error reviewing submission: {str(e)}")
            if conn:
                conn.rollback()
            return False

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        try:
            if submission_data:
                notification_title = f"Challenge Submission {'Approved' if is_approved else 'Rejected'}"
                notification_content = (
                    f"Your submission for '{submission_data['challenge_title']}' has been "
                    f"{'approved' if is_approved else 'rejected'}"
                )
                if feedback:
                    notification_content += f"\n\nFeedback: {feedback}"
                if is_approved:
                    notification_content += f"\n\nCongratulations! You earned {submission_data['exp_reward']} EXP!"

                notification = Notification.create(
                    user_id=submission_data['user_id'],
                    type='challenge_review',
                    title=notification_title,
                    content=notification_content,
                    link=f'/challenges/{submission_data["challenge_id"]}'
                )

                print(f"Created notification for user {submission_data['username']}")

        except Exception as e:
            print(f"Error creating notification: {str(e)}")
            pass

        return True

    @staticmethod
    def get_leaderboard():
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    u.id,
                    u.username,
                    COUNT(DISTINCT cs.challenge_id) as completed_challenges,
                    COALESCE(u.exp, 0) as total_exp
                FROM users u
                LEFT JOIN challenge_status cs ON u.id = cs.user_id AND cs.status = 'completed'
                GROUP BY u.id, u.username, u.exp
                ORDER BY u.exp DESC, completed_challenges DESC
                LIMIT 10
            """
            
            cursor.execute(query)
            leaderboard = cursor.fetchall()
            
            return leaderboard
        except Exception as e:
            print(f"Error in get_leaderboard: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_challenges(user_id):
        # Get challenges categorized by available, active, and completed for a specific user.
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            available_query = """
                SELECT 
                    c.id,
                    c.title,
                    c.description,
                    c.category,
                    c.difficulty as difficulty,
                    c.exp_reward,
                    c.requirements,
                    c.icon_name,
                    c.created_at,
                    c.updated_at
                FROM challenges c
                LEFT JOIN challenge_status cs ON c.id = cs.challenge_id AND cs.user_id = %s
                WHERE c.is_active = TRUE AND cs.id IS NULL
                ORDER BY c.difficulty ASC, c.title ASC
            """
            cursor.execute(available_query, (user_id,))
            available = cursor.fetchall()
            
            active_query = """
                SELECT 
                    c.id,
                    c.title,
                    c.description,
                    c.category,
                    c.difficulty as difficulty,
                    c.exp_reward,
                    c.requirements,
                    c.icon_name,
                    c.created_at,
                    c.updated_at,
                    cs.progress,
                    cs.started_at,
                    'in_progress' as status
                FROM challenges c
                JOIN challenge_status cs ON c.id = cs.challenge_id
                WHERE cs.user_id = %s AND cs.status = 'in_progress'
                ORDER BY cs.started_at DESC
            """
            cursor.execute(active_query, (user_id,))
            active = cursor.fetchall()
            
            completed_query = """
                SELECT 
                    c.id,
                    c.title,
                    c.description,
                    c.category,
                    c.difficulty as difficulty,
                    c.exp_reward,
                    c.requirements,
                    c.icon_name,
                    c.created_at,
                    c.updated_at,
                    cs.completed_at,
                    'completed' as status
                FROM challenges c
                JOIN challenge_status cs ON c.id = cs.challenge_id
                WHERE cs.user_id = %s AND cs.status = 'completed'
                ORDER BY cs.completed_at DESC
            """
            cursor.execute(completed_query, (user_id,))
            completed = cursor.fetchall()
            
            response_data = {
                'available': available,
                'active': active,
                'completed': completed
            }
            
            return response_data
        except Exception as e:
            print(f"Error in get_user_challenges: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

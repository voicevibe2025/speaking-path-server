"""
Django management command to seed user data for development
"""
import random
from datetime import datetime, timedelta, date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from apps.users.models import UserProfile, LearningPreference, UserAchievement
from apps.gamification.models import (
    UserLevel, Badge, UserBadge, DailyQuest, UserQuest,
    Leaderboard, LeaderboardEntry
)
from apps.speaking_sessions.models import (
    PracticeSession, AudioRecording, SessionFeedback
)
from apps.learning_paths.models import (
    LearningPath, LearningModule, ModuleActivity, UserProgress,
    Milestone, UserMilestone
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed user data for development purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='nuhyamin31@gmail.com',
            help='Email of user to seed data for'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options):
        email = options['email']
        clear_data = options['clear']

        self.stdout.write(f"Seeding data for user: {email}")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with email {email} not found!")
            )
            return

        with transaction.atomic():
            if clear_data:
                self.clear_user_data(user)

            self.create_system_badges()
            self.seed_user_profile(user)
            self.seed_learning_preference(user)
            self.seed_user_level(user)
            self.seed_user_badges(user)
            self.seed_practice_sessions(user)
            self.seed_learning_paths(user)
            self.seed_daily_quests(user)
            self.seed_leaderboard_entries(user)
            self.seed_user_achievements(user)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded data for {email}")
        )

    def clear_user_data(self, user):
        """Clear existing user data"""
        self.stdout.write("Clearing existing data...")

        # Clear all user-related data
        UserProfile.objects.filter(user=user).delete()
        LearningPreference.objects.filter(user=user).delete()
        UserLevel.objects.filter(user=user).delete()
        UserBadge.objects.filter(user=user).delete()
        PracticeSession.objects.filter(user=user).delete()
        LearningPath.objects.filter(user=user).delete()
        UserProgress.objects.filter(user=user).delete()
        UserQuest.objects.filter(user=user).delete()
        LeaderboardEntry.objects.filter(user=user).delete()
        UserAchievement.objects.filter(user=user).delete()
        UserMilestone.objects.filter(user=user).delete()

    def create_system_badges(self):
        """Create system badges if they don't exist"""
        badges_data = [
            {
                'name': 'First Steps', 'category': 'pronunciation',
                'batik_pattern': 'kawung', 'pattern_color': '#FF6B6B',
                'description': 'Complete your first pronunciation exercise',
                'requirements': {'sessions': 1}, 'tier': 1, 'icon': 'mic'
            },
            {
                'name': 'Grammar Guru', 'category': 'grammar',
                'batik_pattern': 'parang', 'pattern_color': '#4ECDC4',
                'description': 'Master basic grammar concepts',
                'requirements': {'grammar_score': 85}, 'tier': 2, 'icon': 'book'
            },
            {
                'name': 'Fluency Master', 'category': 'fluency',
                'batik_pattern': 'sido_mukti', 'pattern_color': '#45B7D1',
                'description': 'Achieve excellent fluency in conversations',
                'requirements': {'fluency_score': 90}, 'tier': 3, 'icon': 'message'
            },
            {
                'name': 'Streak Champion', 'category': 'streak',
                'batik_pattern': 'truntum', 'pattern_color': '#96CEB4',
                'description': 'Maintain a 7-day practice streak',
                'requirements': {'streak_days': 7}, 'tier': 2, 'icon': 'fire'
            },
            {
                'name': 'Cultural Explorer', 'category': 'cultural',
                'batik_pattern': 'sekar_jagad', 'pattern_color': '#FFEAA7',
                'description': 'Complete cultural scenario practices',
                'requirements': {'cultural_sessions': 5}, 'tier': 2, 'icon': 'globe'
            },
            {
                'name': 'Vocabulary Builder', 'category': 'vocabulary',
                'batik_pattern': 'ceplok', 'pattern_color': '#DDA0DD',
                'description': 'Learn 100 new vocabulary words',
                'requirements': {'vocabulary_learned': 100}, 'tier': 3, 'icon': 'book-open'
            }
        ]

        for badge_data in badges_data:
            badge, created = Badge.objects.get_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            if created:
                self.stdout.write(f"Created badge: {badge.name}")

    def seed_user_profile(self, user):
        """Create or update user profile"""
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'bio': 'Indonesian English learner passionate about improving communication skills',
                'native_language': 'id',
                'target_language': 'en',
                'current_proficiency': 'intermediate',
                'learning_goal': 'business',
                'daily_practice_goal': 30,  # 30 minutes daily
                'preferred_session_duration': 15,
                'total_practice_time': 450,  # 7.5 hours total
                'streak_days': 12,
                'last_practice_date': timezone.now().date(),
                'phone_number': '+62812345678',
                'date_of_birth': date(1995, 8, 15)
            }
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} user profile")

    def seed_learning_preference(self, user):
        """Create learning preferences"""
        preference, created = LearningPreference.objects.get_or_create(
            user=user,
            defaults={
                'preferred_scenarios': ['business', 'formal', 'cultural'],
                'avoided_topics': ['politics', 'religion'],
                'visual_learning': 7,
                'auditory_learning': 8,
                'kinesthetic_learning': 6,
                'immediate_correction': True,
                'detailed_feedback': True,
                'cultural_context': True,
                'ai_personality': 'encouraging',
                'difficulty_adaptation_speed': 0.6
            }
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} learning preferences")

    def seed_user_level(self, user):
        """Create user level and experience"""
        level, created = UserLevel.objects.get_or_create(
            user=user,
            defaults={
                'current_level': 8,
                'experience_points': 2450,
                'total_points_earned': 3200,
                'wayang_character': 'Petruk',  # The Eloquent Speaker
                'streak_days': 12,
                'longest_streak': 15,
                'last_activity_date': timezone.now().date()
            }
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} user level")

    def seed_user_badges(self, user):
        """Award badges to user"""
        badges_to_award = ['First Steps', 'Grammar Guru', 'Streak Champion', 'Cultural Explorer']

        for badge_name in badges_to_award:
            try:
                badge = Badge.objects.get(name=badge_name)
                user_badge, created = UserBadge.objects.get_or_create(
                    user=user,
                    badge=badge,
                    defaults={
                        'earned_at': timezone.now() - timedelta(days=random.randint(1, 10)),
                        'current_tier': badge.tier
                    }
                )
                if created:
                    self.stdout.write(f"Awarded badge: {badge_name}")
            except Badge.DoesNotExist:
                self.stdout.write(f"Badge {badge_name} not found")

    def seed_practice_sessions(self, user):
        """Create realistic practice sessions"""
        session_types = [
            'scenario_based', 'pronunciation', 'conversation',
            'vocabulary', 'grammar', 'free_practice'
        ]

        scenarios = [
            {
                'title': 'Business Meeting Introduction',
                'description': 'Practice introducing yourself in a formal business setting',
                'difficulty': 6
            },
            {
                'title': 'Restaurant Ordering',
                'description': 'Order food at an Indonesian-fusion restaurant in English',
                'difficulty': 4
            },
            {
                'title': 'Job Interview Preparation',
                'description': 'Practice answering common interview questions',
                'difficulty': 8
            },
            {
                'title': 'Cultural Exchange Discussion',
                'description': 'Discuss Indonesian culture with international friends',
                'difficulty': 7
            }
        ]

        # Create 15 recent practice sessions
        for i in range(15):
            session_date = timezone.now() - timedelta(days=random.randint(0, 30))
            scenario = random.choice(scenarios)
            session_type = random.choice(session_types)

            # Generate realistic scores based on user's intermediate level
            base_score = random.randint(70, 85)
            pronunciation_score = base_score + random.randint(-10, 10)
            fluency_score = base_score + random.randint(-8, 12)
            grammar_score = base_score + random.randint(-5, 15)
            vocabulary_score = base_score + random.randint(-8, 10)
            overall_score = (pronunciation_score + fluency_score + grammar_score + vocabulary_score) / 4

            session = PracticeSession.objects.create(
                user=user,
                session_type=session_type,
                session_status='completed',
                scenario_title=scenario['title'],
                scenario_description=scenario['description'],
                scenario_difficulty=scenario['difficulty'],
                target_language='en',
                target_proficiency='intermediate',
                duration_seconds=random.randint(300, 900),  # 5-15 minutes
                word_count=random.randint(50, 200),
                sentence_count=random.randint(8, 30),
                pronunciation_score=max(0, min(100, pronunciation_score)),
                fluency_score=max(0, min(100, fluency_score)),
                grammar_score=max(0, min(100, grammar_score)),
                vocabulary_score=max(0, min(100, vocabulary_score)),
                overall_score=max(0, min(100, overall_score)),
                ai_feedback={
                    'strengths': ['Good pronunciation clarity', 'Natural conversation flow'],
                    'improvements': ['Work on complex sentence structures', 'Expand business vocabulary'],
                    'cultural_notes': ['Great understanding of Indonesian business etiquette translation']
                },
                started_at=session_date,
                completed_at=session_date + timedelta(minutes=random.randint(5, 15))
            )

            # Add session feedback
            feedback_types = ['pronunciation', 'grammar', 'vocabulary', 'fluency']
            for feedback_type in random.sample(feedback_types, random.randint(1, 3)):
                SessionFeedback.objects.create(
                    session=session,
                    feedback_type=feedback_type,
                    feedback_text=f"Good progress in {feedback_type}. Keep practicing!",
                    severity='minor' if random.random() > 0.3 else 'moderate',
                    recommendation=f"Practice more {feedback_type} exercises",
                    cultural_note="Consider Indonesian cultural context in business communication"
                )

        self.stdout.write("Created practice sessions with feedback")

    def seed_learning_paths(self, user):
        """Create learning path with modules and progress"""
        # Create main learning path
        learning_path = LearningPath.objects.create(
            user=user,
            name="Business English Mastery",
            description="Comprehensive business English program for Indonesian professionals",
            path_type='business',
            difficulty_level='B1',
            learning_goal="Master business English communication for professional advancement",
            estimated_duration_weeks=12,
            target_proficiency='B2',
            progress_percentage=65.5,
            current_module_index=2,
            focus_areas=['pronunciation', 'business_vocabulary', 'formal_communication'],
            cultural_context={'origin': 'indonesia', 'business_culture': 'hierarchical'},
            started_at=timezone.now() - timedelta(days=45),
            last_accessed=timezone.now() - timedelta(hours=2)
        )

        # Create modules
        modules_data = [
            {
                'name': 'Business Introductions',
                'description': 'Learn to introduce yourself professionally',
                'module_type': 'scenario',
                'order_index': 0,
                'is_locked': False,
                'is_completed': True,
                'completion_percentage': 100,
                'estimated_duration_minutes': 120
            },
            {
                'name': 'Meeting Participation',
                'description': 'Participate effectively in business meetings',
                'module_type': 'pronunciation',
                'order_index': 1,
                'is_locked': False,
                'is_completed': True,
                'completion_percentage': 100,
                'estimated_duration_minutes': 180
            },
            {
                'name': 'Email Communication',
                'description': 'Write professional emails in English',
                'module_type': 'grammar',
                'order_index': 2,
                'is_locked': False,
                'is_completed': False,
                'completion_percentage': 60,
                'estimated_duration_minutes': 150
            },
            {
                'name': 'Presentation Skills',
                'description': 'Deliver compelling business presentations',
                'module_type': 'fluency',
                'order_index': 3,
                'is_locked': True,
                'is_completed': False,
                'completion_percentage': 0,
                'estimated_duration_minutes': 200
            }
        ]

        for module_data in modules_data:
            module = LearningModule.objects.create(
                learning_path=learning_path,
                **module_data,
                learning_objectives=[
                    f"Complete {module_data['name'].lower()} exercises",
                    "Achieve 80% accuracy score",
                    "Apply skills in real scenarios"
                ],
                content={'lessons': 5, 'exercises': 10, 'assessments': 2}
            )

            # Create user progress for each module
            status = 'completed' if module_data['is_completed'] else ('in_progress' if module_data['completion_percentage'] > 0 else 'not_started')
            score = random.randint(80, 95) if module_data['is_completed'] else (random.randint(70, 85) if status == 'in_progress' else None)

            UserProgress.objects.create(
                user=user,
                learning_path=learning_path,
                module=module,
                status=status,
                score=score,
                attempts=random.randint(1, 2) if score else 0,
                time_spent_minutes=random.randint(60, 150) if status != 'not_started' else 0,
                started_at=timezone.now() - timedelta(days=random.randint(5, 40)),
                completed_at=timezone.now() - timedelta(days=random.randint(1, 20)) if status == 'completed' else None
            )

        self.stdout.write("Created learning path with modules and progress")

    def seed_daily_quests(self, user):
        """Create daily quests for user"""
        quest_types = [
            ('speaking_practice', 'Complete 2 speaking sessions'),
            ('pronunciation', 'Practice pronunciation for 15 minutes'),
            ('vocabulary', 'Learn 10 new business terms'),
            ('cultural', 'Complete 1 cultural scenario')
        ]

        for i, (quest_type, description) in enumerate(quest_types):
            # Create quest for today
            daily_quest = DailyQuest.objects.create(
                name=f"Daily {quest_type.replace('_', ' ').title()} Challenge",
                description=description,
                quest_type=quest_type,
                requirements={'target': 2 if 'speaking' in quest_type else 1},
                target_value=2 if 'speaking' in quest_type else 1,
                experience_points=15,
                available_date=timezone.now().date()
            )

            # Create user quest progress
            is_completed = random.choice([True, False])
            progress = daily_quest.target_value if is_completed else random.randint(0, daily_quest.target_value - 1)

            UserQuest.objects.create(
                user=user,
                quest=daily_quest,
                current_progress=progress,
                is_completed=is_completed,
                completed_at=timezone.now() - timedelta(hours=random.randint(1, 8)) if is_completed else None,
                points_earned=daily_quest.experience_points if is_completed else 0,
                rewards_claimed=is_completed
            )

        self.stdout.write("Created daily quests")

    def seed_leaderboard_entries(self, user):
        """Create leaderboard entries"""
        # Create weekly leaderboard if it doesn't exist
        weekly_board, created = Leaderboard.objects.get_or_create(
            leaderboard_type='weekly',
            period_start=timezone.now() - timedelta(days=7),
            defaults={
                'period_end': timezone.now(),
                'rankings': []
            }
        )

        # Add user to leaderboard
        LeaderboardEntry.objects.create(
            leaderboard=weekly_board,
            user=user,
            rank=random.randint(15, 25),
            score=2450,
            sessions_completed=12,
            average_score=82.5,
            improvement_rate=15.3,
            wayang_character='Petruk',
            primary_badge=Badge.objects.filter(name='Grammar Guru').first()
        )

        self.stdout.write("Created leaderboard entries")

    def seed_user_achievements(self, user):
        """Create user achievements"""
        achievements_data = [
            {
                'achievement_type': 'first_session',
                'achievement_name': 'First Practice Session',
                'achievement_description': 'Completed your very first speaking practice session',
                'category': 'practice',
                'points_earned': 50,
                'is_completed': True
            },
            {
                'achievement_type': 'week_streak',
                'achievement_name': '7-Day Streak Master',
                'achievement_description': 'Maintained practice for 7 consecutive days',
                'category': 'streak',
                'points_earned': 100,
                'progress_current': 7,
                'progress_target': 7,
                'is_completed': True
            },
            {
                'achievement_type': 'grammar_score',
                'achievement_name': 'Grammar Excellence',
                'achievement_description': 'Achieved 90% or higher in grammar exercises',
                'category': 'proficiency',
                'points_earned': 75,
                'progress_current': 92,
                'progress_target': 90,
                'is_completed': True
            },
            {
                'achievement_type': 'cultural_scenarios',
                'achievement_name': 'Cultural Ambassador',
                'achievement_description': 'Completed 5 cultural exchange scenarios',
                'category': 'cultural',
                'points_earned': 80,
                'progress_current': 5,
                'progress_target': 5,
                'is_completed': True
            }
        ]

        for achievement_data in achievements_data:
            UserAchievement.objects.create(
                user=user,
                **achievement_data,
                earned_at=timezone.now() - timedelta(days=random.randint(1, 30)) if achievement_data['is_completed'] else None
            )

        self.stdout.write("Created user achievements")

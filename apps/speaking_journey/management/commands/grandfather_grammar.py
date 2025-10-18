from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.speaking_journey.models import (
    TopicProgress,
    Topic,
    PhraseProgress,
    VocabularyPracticeSession,
    GrammarPracticeSession,
)


class Command(BaseCommand):
    help = (
        "Grandfather grammar completion for legacy users who had already completed topics "
        "under the 3-practice rule. Sets grammar_completed=True and grammar_total_score "
        "to at least a threshold (default 75) for topics where Pronunciation, Fluency, "
        "and Vocabulary are effectively complete."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email', dest='email', type=str, required=True,
            help='Target user email (required)')
        parser.add_argument(
            '--min-score', dest='min_score', type=int, default=75,
            help='Minimum score to set for grammar_total_score when grandfathering (default: 75)')
        parser.add_argument(
            '--apply', action='store_true',
            help='Actually apply changes. Without this flag, performs a dry run (no writes).')
        parser.add_argument(
            '--grandfather-all-completed', action='store_true', dest='grandfather_all_completed',
            help='When set, target ALL topics with TopicProgress.completed=True for the user, and bump all four practices (pron, flu, vocab, grammar) to completed with total scores >= min-score. By default, only grammar is grandfathered when other three practices already meet threshold.'
        )
        parser.add_argument(
            '--create-sessions', action='store_true', dest='create_sessions',
            help='When used with --grandfather-all-completed, also create minimal completed VocabularyPracticeSession and GrammarPracticeSession records if missing to satisfy legacy completion checks.'
        )

    def handle(self, *args, **options):
        email = options.get('email')
        min_score = int(options.get('min_score') or 75)
        apply_changes = bool(options.get('apply'))
        grandfather_all_completed = bool(options.get('grandfather_all_completed'))
        create_sessions = bool(options.get('create_sessions'))

        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"User with email {email!r} not found")

        tps = TopicProgress.objects.filter(user=user).select_related('topic')
        candidates = []
        skipped = []

        if grandfather_all_completed:
            # Force mode: include all legacy-completed topics regardless of thresholds
            for tp in tps:
                topic = tp.topic
                if not topic:
                    continue
                if bool(tp.completed):
                    candidates.append(tp)
                else:
                    skipped.append((getattr(tp.topic, 'sequence', '?'), getattr(tp.topic, 'title', '?'), {'reason': 'not completed (legacy)'}))
        else:
            # Default mode: only fill grammar when other three practices are effectively complete
            for tp in tps:
                topic = tp.topic
                if not topic:
                    continue
                if tp.grammar_completed:
                    continue

                # Pronunciation effective completion: flag OR all phrases completed
                pron_eff = bool(tp.pronunciation_completed)
                if not pron_eff:
                    pp = PhraseProgress.objects.filter(user=user, topic=topic).first()
                    if pp and getattr(pp, 'is_all_phrases_completed', False):
                        pron_eff = True

                # Fluency effective completion: prompt score >= min_score OR total >= min_score
                scores = list(getattr(tp, 'fluency_prompt_scores', []) or [])
                flu_eff = False
                try:
                    if scores and isinstance(scores[0], int) and scores[0] >= min_score:
                        flu_eff = True
                    elif int(getattr(tp, 'fluency_total_score', 0) or 0) >= min_score:
                        flu_eff = True
                except Exception:
                    pass

                # Vocabulary effective completion: any completed session OR total >= min_score
                vocab_eff = False
                try:
                    if VocabularyPracticeSession.objects.filter(user=user, topic=topic, completed=True).exists():
                        vocab_eff = True
                    elif int(getattr(tp, 'vocabulary_total_score', 0) or 0) >= min_score:
                        vocab_eff = True
                except Exception:
                    pass

                if pron_eff and flu_eff and vocab_eff:
                    candidates.append(tp)
                else:
                    skipped.append((topic.sequence, topic.title, {
                        'pron_eff': pron_eff,
                        'flu_eff': flu_eff,
                        'vocab_eff': vocab_eff,
                        'flu_total': int(getattr(tp, 'fluency_total_score', 0) or 0),
                        'vocab_total': int(getattr(tp, 'vocabulary_total_score', 0) or 0),
                    }))

        self.stdout.write(self.style.NOTICE(f"User: {user.id} {getattr(user, 'username', '')} <{user.email}>") )
        self.stdout.write(self.style.NOTICE(f"Found {len(candidates)} topics eligible for grammar grandfathering; {len(skipped)} skipped."))
        if candidates:
            self.stdout.write("Eligible topics (sequence - title):")
            self.stdout.write(
                "\n".join([f"  {tp.topic.sequence} - {tp.topic.title}" for tp in candidates])
            )
        if skipped:
            self.stdout.write("Skipped topics (sequence - title - reasons):")
            for seq, title, info in skipped[:20]:  # cap output
                self.stdout.write(f"  {seq} - {title} :: {info}")
            if len(skipped) > 20:
                self.stdout.write(f"  ... and {len(skipped) - 20} more")

        if not apply_changes:
            self.stdout.write(self.style.WARNING("Dry run. No changes applied. Use --apply to persist updates."))
            return

        # Apply changes
        updated = 0
        created_vocab_sessions = 0
        created_grammar_sessions = 0
        for tp in candidates:
            if grandfather_all_completed:
                # Bump all four practices to completed and set scores to at least min_score
                tp.pronunciation_completed = True
                tp.fluency_completed = True
                tp.vocabulary_completed = True
                tp.grammar_completed = True
                tp.pronunciation_total_score = max(int(getattr(tp, 'pronunciation_total_score', 0) or 0), min_score)
                tp.fluency_total_score = max(int(getattr(tp, 'fluency_total_score', 0) or 0), min_score)
                tp.vocabulary_total_score = max(int(getattr(tp, 'vocabulary_total_score', 0) or 0), min_score)
                tp.grammar_total_score = max(int(getattr(tp, 'grammar_total_score', 0) or 0), min_score)

                # Ensure fluency_prompt_scores has at least one score >= min_score
                try:
                    scores = list(getattr(tp, 'fluency_prompt_scores', []) or [])
                except Exception:
                    scores = []
                if not scores:
                    scores = [min_score]
                elif not isinstance(scores[0], int) or scores[0] < min_score:
                    scores[0] = min_score
                tp.fluency_prompt_scores = scores
                # Ensure completed flag/time
                tp.completed = True
                if not tp.completed_at:
                    tp.completed_at = timezone.now()
                tp.save(update_fields=[
                    'pronunciation_completed', 'fluency_completed', 'vocabulary_completed', 'grammar_completed',
                    'pronunciation_total_score', 'fluency_total_score', 'vocabulary_total_score', 'grammar_total_score', 'fluency_prompt_scores',
                    'completed', 'completed_at'
                ])

                # Optionally create minimal completed sessions to satisfy effective checks
                if create_sessions:
                    # Vocabulary session
                    try:
                        has_vocab = VocabularyPracticeSession.objects.filter(user=tp.user, topic=tp.topic, completed=True).exists()
                    except Exception:
                        has_vocab = False
                    if not has_vocab:
                        if apply_changes:
                            VocabularyPracticeSession.objects.create(
                                user=tp.user,
                                topic=tp.topic,
                                questions=[],
                                total_questions=0,
                                current_index=0,
                                correct_count=0,
                                total_score=min_score,
                                completed=True,
                            )
                            created_vocab_sessions += 1
                        else:
                            self.stdout.write(self.style.NOTICE(f"Would create VocabularyPracticeSession for topic {tp.topic.sequence} - {tp.topic.title}"))

                    # Grammar session
                    try:
                        has_grammar = GrammarPracticeSession.objects.filter(user=tp.user, topic=tp.topic, completed=True).exists()
                    except Exception:
                        has_grammar = False
                    if not has_grammar:
                        if apply_changes:
                            GrammarPracticeSession.objects.create(
                                user=tp.user,
                                topic=tp.topic,
                                questions=[],
                                total_questions=0,
                                current_index=0,
                                correct_count=0,
                                total_score=min_score,
                                completed=True,
                            )
                            created_grammar_sessions += 1
                        else:
                            self.stdout.write(self.style.NOTICE(f"Would create GrammarPracticeSession for topic {tp.topic.sequence} - {tp.topic.title}"))
            else:
                # Set grammar fields only
                new_grammar_score = max(int(getattr(tp, 'grammar_total_score', 0) or 0), min_score)
                tp.grammar_total_score = new_grammar_score
                tp.grammar_completed = True

                # If now all modes are completed, set completed flag and timestamp
                if not tp.completed and (
                    tp.pronunciation_completed and tp.fluency_completed and tp.vocabulary_completed and True  # grammar just set
                ):
                    tp.completed = True
                    if not tp.completed_at:
                        tp.completed_at = timezone.now()

                tp.save(update_fields=['grammar_total_score', 'grammar_completed', 'completed', 'completed_at'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Applied grammar grandfathering to {updated} topics."))
        if grandfather_all_completed and create_sessions:
            self.stdout.write(self.style.SUCCESS(f"Created {created_vocab_sessions} VocabularyPracticeSession(s) and {created_grammar_sessions} GrammarPracticeSession(s)."))

        # Show new unlocks snapshot
        try:
            from apps.speaking_journey.views import _compute_unlocks
            topics, completed_sequences, unlocked_sequences = _compute_unlocks(user)
            self.stdout.write(self.style.SUCCESS(
                f"Now completed sequences: {sorted(list(completed_sequences))}\n"
                f"Now unlocked sequences: {sorted(list(unlocked_sequences))}"
            ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not compute unlocks summary: {e}"))

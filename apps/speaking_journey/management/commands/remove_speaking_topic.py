from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F

from apps.speaking_journey.models import (
    Topic,
    TopicProgress,
    PhraseProgress,
    UserPhraseRecording,
    UserConversationRecording,
    VocabularyPracticeSession,
    ListeningPracticeSession,
    GrammarPracticeSession,
    EnglishLevel,
)


class Command(BaseCommand):
    help = (
        "Remove a Speaking Journey topic by id/title/sequence.\n"
        "Default action deactivates the topic (is_active=False).\n"
        "Use --delete to permanently delete it (cascades to related progress/recordings).\n"
    )

    def add_arguments(self, parser):
        ident = parser.add_argument_group("Topic selector (provide at least one)")
        ident.add_argument("--id", dest="id", help="Topic UUID")
        ident.add_argument("--title", dest="title", help="Topic title (exact match)")
        ident.add_argument("--sequence", dest="sequence", type=int, help="Topic sequence number")
        ident.add_argument(
            "--difficulty",
            choices=[c for c, _ in EnglishLevel.choices],
            help="Optional: filter by difficulty to disambiguate title",
        )

        mode = parser.add_argument_group("Action")
        mode.add_argument(
            "--delete",
            action="store_true",
            help="Permanently delete the topic (instead of deactivating)",
        )
        mode.add_argument(
            "--reflow",
            action="store_true",
            help=(
                "After delete, shift down sequences of topics that come after the deleted one "
                "(sequence > deleted.sequence) so there is no gap. Only valid with --delete."
            ),
        )

        safety = parser.add_argument_group("Safety")
        safety.add_argument("--dry-run", action="store_true", help="Show what would happen, without changes")
        safety.add_argument("-y", "--yes", action="store_true", help="Proceed without interactive confirmation")

    def _find_topic(self, opts):
        qs = Topic.objects.all()
        provided = 0
        if opts.get("id"):
            qs = qs.filter(id=opts["id"])  # UUID exact match
            provided += 1
        if opts.get("title"):
            qs = qs.filter(title=opts["title"].strip())
            provided += 1
        if opts.get("sequence") is not None:
            qs = qs.filter(sequence=int(opts["sequence"]))
            provided += 1
        if opts.get("difficulty"):
            qs = qs.filter(difficulty=opts["difficulty"])

        if provided == 0:
            raise CommandError("Provide at least one selector: --id or --title or --sequence")

        count = qs.count()
        if count == 0:
            raise CommandError("No matching Topic found for the given selector(s)")
        if count > 1:
            # Should not happen due to unique fields, but guard anyway
            raise CommandError("Selector(s) matched multiple topics; please use a unique identifier")

        return qs.first()

    def _count_related(self, topic: Topic):
        return {
            "TopicProgress": TopicProgress.objects.filter(topic=topic).count(),
            "PhraseProgress": PhraseProgress.objects.filter(topic=topic).count(),
            "UserPhraseRecording": UserPhraseRecording.objects.filter(topic=topic).count(),
            "UserConversationRecording": UserConversationRecording.objects.filter(topic=topic).count(),
            "VocabularyPracticeSession": VocabularyPracticeSession.objects.filter(topic=topic).count(),
            "ListeningPracticeSession": ListeningPracticeSession.objects.filter(topic=topic).count(),
            "GrammarPracticeSession": GrammarPracticeSession.objects.filter(topic=topic).count(),
        }

    def handle(self, *args, **options):
        topic = self._find_topic(options)
        delete_mode = bool(options.get("delete"))
        reflow = bool(options.get("reflow"))
        dry_run = bool(options.get("dry_run"))
        assume_yes = bool(options.get("yes"))

        if reflow and not delete_mode:
            raise CommandError("--reflow is only valid together with --delete")

        rel_counts = self._count_related(topic)

        # Summary
        self.stdout.write(self.style.MIGRATE_HEADING("Topic selected:"))
        self.stdout.write(f" - id:        {topic.id}")
        self.stdout.write(f" - title:     {topic.title}")
        self.stdout.write(f" - sequence:  {topic.sequence}")
        self.stdout.write(f" - difficulty:{getattr(topic, 'difficulty', '')}")
        self.stdout.write(f" - is_active: {topic.is_active}")
        self.stdout.write("")

        action = "DELETE" if delete_mode else "DEACTIVATE (set is_active=False)"
        self.stdout.write(self.style.MIGRATE_HEADING(f"Planned action: {action}"))
        if delete_mode and reflow:
            self.stdout.write(" - Reflow: shift down subsequent topic sequences by 1")
        self.stdout.write(" - Related objects (will be deleted by cascade only if --delete):")
        for k, v in rel_counts.items():
            self.stdout.write(f"   - {k}: {v}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDry-run: no changes were made."))
            return

        if not assume_yes:
            confirm = input(f"\nProceed with {action}? Type 'yes' to continue: ")
            if confirm.strip().lower() != "yes":
                self.stdout.write(self.style.WARNING("Aborted by user."))
                return

        with transaction.atomic():
            if delete_mode:
                deleted_seq = topic.sequence
                topic.delete()
                if reflow:
                    # Two-step reflow to avoid unique constraint collisions on 'sequence'
                    bump = 1_000_000
                    # Step 1: move all sequences above the deleted one far away
                    Topic.objects.filter(sequence__gt=deleted_seq).update(sequence=F("sequence") + bump)
                    # Step 2: bring them back down by (bump + 1) -> net effect: old_sequence - 1
                    Topic.objects.filter(sequence__gt=deleted_seq + bump).update(
                        sequence=F("sequence") - (bump + 1)
                    )
                self.stdout.write(self.style.SUCCESS("Topic deleted successfully."))
                if reflow:
                    self.stdout.write(self.style.SUCCESS("Sequence reflow completed."))
            else:
                if not topic.is_active:
                    self.stdout.write(self.style.WARNING("Topic is already inactive."))
                else:
                    topic.is_active = False
                    topic.save(update_fields=["is_active"])
                    self.stdout.write(self.style.SUCCESS("Topic deactivated (is_active=False)."))

        self.stdout.write(self.style.SUCCESS("Done."))

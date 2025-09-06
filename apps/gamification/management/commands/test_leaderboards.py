from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.gamification.models import PointsTransaction, UserLevel
from apps.gamification.views import LeaderboardViewSet


class Command(BaseCommand):
    help = "Create sample PointsTransactions and print leaderboard snapshots for daily/weekly/monthly/all_time."

    def handle(self, *args, **options):
        User = get_user_model()
        u1, _ = User.objects.get_or_create(username='lb_tester1', defaults={'email': 'lb_tester1@example.com'})
        u2, _ = User.objects.get_or_create(username='lb_tester2', defaults={'email': 'lb_tester2@example.com'})

        # Ensure UserLevel exists
        for u in [u1, u2]:
            UserLevel.objects.get_or_create(user=u)

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        two_months_ago = (first_of_month - timedelta(days=60)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        def mk_tx(u, amount, dt, src):
            tx = PointsTransaction.objects.create(user=u, amount=amount, source=src, context={'test': True})
            # Backdate the created_at for controlled testing
            PointsTransaction.objects.filter(pk=tx.pk).update(created_at=dt)

        # Clear existing test tx for these users to avoid noise
        PointsTransaction.objects.filter(user__in=[u1, u2], context__test=True).delete()

        # Create transactions for u1
        mk_tx(u1, 50, today_start + timedelta(hours=1), 'test_daily')
        mk_tx(u1, 40, start_of_week + timedelta(days=1, hours=2), 'test_weekly')
        mk_tx(u1, 30, first_of_month + timedelta(days=10, hours=3), 'test_monthly')
        mk_tx(u1, 20, two_months_ago + timedelta(days=3, hours=4), 'test_old')

        # Create transactions for u2
        mk_tx(u2, 10, today_start + timedelta(hours=2), 'test_daily')
        mk_tx(u2, 100, start_of_week + timedelta(hours=5), 'test_weekly')
        mk_tx(u2, 300, first_of_month + timedelta(hours=6), 'test_monthly')

        factory = APIRequestFactory()

        def call(action):
            view = LeaderboardViewSet.as_view({'get': action})
            req = factory.get(f'/api/gamification/leaderboards/{action}')
            force_authenticate(req, user=u1)
            resp = view(req)
            entries = resp.data.get('entries', [])
            top = [(e.get('username'), e.get('score')) for e in entries[:5]]
            self.stdout.write(f"{action.upper()} top: {top}")

        call('daily')
        call('weekly')
        call('monthly')
        call('all_time')

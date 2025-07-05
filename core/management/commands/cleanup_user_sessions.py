from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from core.models import UserSession
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Clean up orphaned and old UserSession objects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete UserSessions older than this many days (default: 7)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find orphaned UserSession objects (sessions that don't exist in Django's session table)
        orphaned_sessions = []
        all_user_sessions = UserSession.objects.all()
        valid_session_keys = set(Session.objects.values_list('session_key', flat=True))
        
        for user_session in all_user_sessions:
            # If the Django session doesn't exist, this UserSession is orphaned
            if user_session.session_key not in valid_session_keys:
                orphaned_sessions.append(user_session)
        
        # Find old UserSession objects
        old_sessions = UserSession.objects.filter(login_timestamp__lt=cutoff_date)
        
        # Find duplicate active sessions for the same user
        duplicate_sessions = []
        from django.db.models import Count
        users_with_multiple_active = UserSession.objects.filter(
            is_active=True
        ).values('user').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        for user_data in users_with_multiple_active:
            user_id = user_data['user']
            # Keep only the most recent session, mark others as inactive
            user_sessions = UserSession.objects.filter(
                user_id=user_id, 
                is_active=True
            ).order_by('-login_timestamp')
            
            # All but the first (most recent) should be marked inactive
            for session in user_sessions[1:]:
                duplicate_sessions.append(session)
        
        # Report what will be done
        self.stdout.write(f"\n📊 UserSession Cleanup Report:")
        self.stdout.write(f"  🗑️  Orphaned sessions (no Django session): {len(orphaned_sessions)}")
        self.stdout.write(f"  ⏰ Old sessions (>{days} days): {old_sessions.count()}")
        self.stdout.write(f"  👥 Duplicate active sessions: {len(duplicate_sessions)}")
        
        if not dry_run:
            # Delete orphaned sessions
            if orphaned_sessions:
                orphaned_ids = [s.id for s in orphaned_sessions]
                deleted_orphaned = UserSession.objects.filter(id__in=orphaned_ids).delete()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Deleted {deleted_orphaned[0]} orphaned UserSessions")
                )
            
            # Delete old sessions
            if old_sessions.exists():
                deleted_old = old_sessions.delete()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Deleted {deleted_old[0]} old UserSessions")
                )
            
            # Mark duplicate sessions as inactive
            if duplicate_sessions:
                duplicate_ids = [s.id for s in duplicate_sessions]
                updated_duplicates = UserSession.objects.filter(
                    id__in=duplicate_ids
                ).update(is_active=False)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Marked {updated_duplicates} duplicate sessions as inactive")
                )
            
            if not orphaned_sessions and not old_sessions.exists() and not duplicate_sessions:
                self.stdout.write(self.style.SUCCESS("✅ No cleanup needed - all UserSessions are clean!"))
                
        else:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN - No changes made. Use without --dry-run to apply changes."))
        
        # Show current state
        total_sessions = UserSession.objects.count()
        active_sessions = UserSession.objects.filter(is_active=True).count()
        self.stdout.write(f"\n📈 Current UserSession Stats:")
        self.stdout.write(f"  Total UserSessions: {total_sessions}")
        self.stdout.write(f"  Active UserSessions: {active_sessions}")
        self.stdout.write(f"  Inactive UserSessions: {total_sessions - active_sessions}") 
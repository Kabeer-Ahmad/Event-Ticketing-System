from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import TicketHold

class Command(BaseCommand):
    help = 'Clean up expired ticket holds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display detailed output',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        # Find expired holds
        expired_holds = TicketHold.objects.filter(expires_at__lt=timezone.now())
        count = expired_holds.count()
        
        if verbose:
            self.stdout.write(f"Found {count} expired holds to clean up:")
            for hold in expired_holds:
                self.stdout.write(f"  - {hold.user.username} for {hold.event.name} (expired: {hold.expires_at})")
        
        # Delete expired holds
        expired_holds.delete()
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleaned up {count} expired holds')
            )
        else:
            self.stdout.write(f'Cleaned up {count} expired holds')
        
        # Also clean up inactive user sessions older than 24 hours
        from core.models import UserSession
        from datetime import timedelta
        
        old_sessions = UserSession.objects.filter(
            login_timestamp__lt=timezone.now() - timedelta(hours=24),
            is_active=False
        )
        session_count = old_sessions.count()
        old_sessions.delete()
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS(f'Also cleaned up {session_count} old user sessions')
            ) 
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Event, TicketHold, UserSession
from datetime import timedelta

class TicketHoldMiddleware:
    """Middleware to manage ticket holds and cleanup expired holds"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Clean up expired holds before processing request
        self.cleanup_expired_holds()
        
        response = self.get_response(request)
        return response
    
    def cleanup_expired_holds(self):
        """Remove expired ticket holds"""
        expired_holds = TicketHold.objects.filter(expires_at__lt=timezone.now())
        expired_holds.delete()

@receiver(user_logged_in)
def create_ticket_holds_on_login(sender, request, user, **kwargs):
    """Automatically create ticket holds for available events when user logs in"""
    login_time = timezone.now()
    
    # Record the user session for FIFO tracking
    UserSession.objects.update_or_create(
        user=user,
        session_key=request.session.session_key,
        defaults={
            'login_timestamp': login_time,
            'is_active': True
        }
    )
    
    # Get all events that have available capacity
    available_events = []
    for event in Event.objects.all():
        can_hold, reason = event.can_hold_ticket(user)
        if can_hold:
            available_events.append(event)
    
    # Create holds for available events (FIFO based on login time)
    for event in available_events:
        # Create hold with 10-minute expiration
        TicketHold.objects.get_or_create(
            event=event,
            user=user,
            defaults={
                'login_timestamp': login_time,
                'expires_at': login_time + timedelta(minutes=10)
            }
        ) 
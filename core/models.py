from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid

class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    venue = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} @ {self.date.strftime('%Y-%m-%d')}"
    
    def get_booked_count(self):
        """Get number of confirmed bookings"""
        return self.ticket_set.count()
    
    def get_held_count(self):
        """Get number of active holds (not expired)"""
        return self.tickethold_set.filter(
            expires_at__gt=timezone.now()
        ).count()
    
    def get_available_count(self):
        """Get number of truly available tickets"""
        return max(0, self.capacity - self.get_booked_count() - self.get_held_count())
    
    def get_ticket_stats(self):
        """Get complete ticket statistics"""
        booked = self.get_booked_count()
        held = self.get_held_count()
        available = self.get_available_count()
        percentage_sold = (booked / self.capacity * 100) if self.capacity > 0 else 0
        
        # Calculate progress ring values (for SVG circle with radius 25)
        radius = 25
        circumference = 2 * 3.14159 * radius  # 2πr
        dash_offset = circumference - (percentage_sold / 100 * circumference)
        
        return {
            'capacity': self.capacity,
            'booked': booked,
            'held': held,
            'available': available,
            'percentage_sold': percentage_sold,
            'circumference': round(circumference, 2),
            'dash_offset': round(dash_offset, 2)
        }
    
    def can_book_ticket(self, user):
        """Check if a user can book a ticket for this event"""
        # Check if user already has a ticket
        if self.ticket_set.filter(user=user).exists():
            return False, "You already have a ticket for this event"
        
        # Check if tickets are available
        if self.get_available_count() <= 0:
            return False, "No tickets available"
        
        return True, "Available"
    
    def can_hold_ticket(self, user):
        """Check if a user can hold a ticket for this event"""
        # Check if user already has a ticket or hold
        if self.ticket_set.filter(user=user).exists():
            return False, "You already have a ticket for this event"
        
        if self.tickethold_set.filter(user=user, expires_at__gt=timezone.now()).exists():
            return False, "You already have a hold for this event"
        
        # Check if there's capacity (including held tickets)
        total_reserved = self.get_booked_count() + self.get_held_count()
        if total_reserved >= self.capacity:
            return False, "No tickets available"
        
        return True, "Available"

class TicketHold(models.Model):
    """Temporary reservation of a ticket slot for logged-in users"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    login_timestamp = models.DateTimeField()  # When user logged in (for FIFO)
    
    class Meta:
        unique_together = ['event', 'user']
        ordering = ['login_timestamp']  # FIFO order
    
    def __str__(self):
        return f"Hold: {self.user.username} - {self.event.name}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Default hold time: 10 minutes
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)
    unique_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    is_checked_in = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.event.name}"

class UserSession(models.Model):
    """Track user login sessions for ticket holding priority"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_timestamp = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['login_timestamp']  # FIFO order
    
    def __str__(self):
        return f"{self.user.username} - {self.login_timestamp}"

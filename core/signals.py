import qrcode
from io import BytesIO
from django.core.files import File
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from .models import Ticket, Event, TicketHold, UserSession
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import os
from django.utils import timezone

# WebSocket channel layer
channel_layer = get_channel_layer()

def send_events_update():
    """Send events update to all connected clients"""
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            'events',
            {
                'type': 'events_update',
                'message': 'Events updated'
            }
        )

def send_dashboard_update(user_id, update_type='dashboard_update', data=None):
    """Send dashboard update to specific user"""
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'dashboard_{user_id}',
            {
                'type': update_type,
                'data': data or {},
                'message': f'{update_type.replace("_", " ").title()}'
            }
        )

@receiver(post_save, sender=Ticket)
def ticket_saved(sender, instance, created, **kwargs):
    """Handle ticket creation/update"""
    # Generate QR code if not exists
    if not instance.qr_code:
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"Ticket:{instance.id}:Event:{instance.event.name}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Save to model
        filename = f"qr_{instance.id}.png"
        instance.qr_code.save(filename, File(buffer), save=False)
        buffer.close()
        
        # Update instance without triggering signal again
        Ticket.objects.filter(id=instance.id).update(qr_code=instance.qr_code.name)
    
    # Send WebSocket updates
    send_events_update()
    send_dashboard_update(instance.user.id, 'ticket_update', {
        'ticket_id': instance.id,
        'event_title': instance.event.name,
        'created': created
    })

@receiver(post_save, sender=TicketHold)
def ticket_hold_saved(sender, instance, created, **kwargs):
    """Handle ticket hold creation/update"""
    send_events_update()
    send_dashboard_update(instance.user.id, 'hold_update', {
        'hold_id': instance.id,
        'event_title': instance.event.name,
        'created': created
    })

@receiver(post_delete, sender=TicketHold)
def ticket_hold_deleted(sender, instance, **kwargs):
    """Handle ticket hold deletion"""
    send_events_update()
    send_dashboard_update(instance.user.id, 'hold_update', {
        'hold_id': instance.id,
        'event_title': instance.event.name,
        'deleted': True
    })

@receiver(post_save, sender=Event)
@receiver(post_delete, sender=Event)
def event_changed(sender, instance, **kwargs):
    """Handle event changes"""
    send_events_update()

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """Handle user login to create new session"""
    # Generate a unique session key for each login
    import uuid
    unique_session_key = f"{user.id}_{uuid.uuid4().hex[:20]}_{int(timezone.now().timestamp())}"
    
    # Create a new UserSession for each login (this is correct for FIFO ordering)
    UserSession.objects.create(
        user=user,
        session_key=unique_session_key,
        is_active=True
    )
    
    # Create ticket hold for the earliest event they can book
    available_events = Event.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date')
    
    for event in available_events:
        can_hold, _ = event.can_hold_ticket(user)
        if can_hold:
            TicketHold.objects.create(
                user=user,
                event=event,
                login_timestamp=timezone.now(),
                expires_at=timezone.now() + timezone.timedelta(minutes=10)
            )
            break

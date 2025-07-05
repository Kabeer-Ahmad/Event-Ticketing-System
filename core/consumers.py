import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import asyncio
from datetime import datetime, timezone

class EventConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'events'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        events_data = await self.get_events_data()
        await self.send(text_data=json.dumps({
            'type': 'events_update',
            'events': events_data
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def get_events_data(self):
        from .models import Event
        events = []
        for event in Event.objects.all():
            stats = event.get_ticket_stats()
            events.append({
                'id': event.id,
                'title': event.name,
                'date': event.date.isoformat(),
                'venue': event.venue,
                'capacity': event.capacity,
                'booked_count': stats['booked'],
                'held_count': stats['held'],
                'available_count': stats['available'],
                'booked_percentage': stats['percentage_sold'],
                'held_percentage': 0,  # Not calculated separately in stats
                'available_percentage': 100 - stats['percentage_sold'],
            })
        return events

    # Receive message from room group
    async def events_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        self.room_group_name = f'dashboard_{self.user.id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Start countdown timer for holds
        self.countdown_task = asyncio.create_task(self.send_countdown_updates())

    async def disconnect(self, close_code):
        # Cancel countdown task
        if hasattr(self, 'countdown_task'):
            self.countdown_task.cancel()
            
        # Leave room group (only if room_group_name was set)
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def send_countdown_updates(self):
        """Send real-time countdown updates for ticket holds"""
        try:
            while True:
                holds_data = await self.get_user_holds()
                if holds_data:
                    await self.send(text_data=json.dumps({
                        'type': 'holds_countdown',
                        'holds': holds_data
                    }))
                await asyncio.sleep(1)  # Update every second
        except asyncio.CancelledError:
            pass

    @database_sync_to_async
    def get_user_holds(self):
        """Get current user's active holds with countdown data"""
        from .models import TicketHold
        holds = []
        for hold in TicketHold.objects.filter(user=self.user, expires_at__gt=datetime.now(timezone.utc)):
            time_left = (hold.expires_at - datetime.now(timezone.utc)).total_seconds()
            holds.append({
                'id': hold.id,
                'event_title': hold.event.name,
                'event_id': hold.event.id,
                'time_left_seconds': max(0, int(time_left)),
                'expires_at': hold.expires_at.isoformat(),
            })
        return holds

    @database_sync_to_async
    def get_dashboard_data(self):
        """Get complete dashboard data for the user"""
        from .models import Ticket, Event, TicketHold
        # Active tickets
        tickets = []
        for ticket in Ticket.objects.filter(user=self.user):
            tickets.append({
                'id': ticket.id,
                'event_title': ticket.event.name,
                'event_date': ticket.event.date.isoformat(),
                'event_venue': ticket.event.venue,
                'purchased_at': ticket.booked_at.isoformat(),
                'is_checked_in': ticket.is_checked_in,
                'qr_code_url': ticket.qr_code.url if ticket.qr_code else None,
            })
        
        # Active holds - get the data directly here to avoid calling async method
        holds = []
        for hold in TicketHold.objects.filter(user=self.user, expires_at__gt=datetime.now(timezone.utc)):
            time_left = (hold.expires_at - datetime.now(timezone.utc)).total_seconds()
            holds.append({
                'id': hold.id,
                'event_title': hold.event.name,
                'event_id': hold.event.id,
                'time_left_seconds': max(0, int(time_left)),
                'expires_at': hold.expires_at.isoformat(),
            })
        
        # Available events
        events = []
        for event in Event.objects.all():
            can_book, _ = event.can_book_ticket(self.user)
            can_hold, _ = event.can_hold_ticket(self.user)
            if can_book or can_hold:
                stats = event.get_ticket_stats()
                events.append({
                    'id': event.id,
                    'title': event.name,
                    'date': event.date.isoformat(),
                    'venue': event.venue,
                    'capacity': event.capacity,
                    'available_count': stats['available'],
                    'can_book': can_book,
                    'can_hold': can_hold,
                })
        
        return {
            'tickets': tickets,
            'holds': holds,
            'events': events
        }

    # Receive message from room group
    async def dashboard_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))

    async def ticket_update(self, event):
        # Send ticket update to WebSocket
        await self.send(text_data=json.dumps(event))

    async def hold_update(self, event):
        # Send hold update to WebSocket
        await self.send(text_data=json.dumps(event)) 
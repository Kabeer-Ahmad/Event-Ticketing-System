from django.contrib import admin
from .models import Event, Ticket, TicketHold, UserSession

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'venue', 'capacity', 'get_booked_count', 'get_held_count', 'get_available_count', 'created_by')
    list_filter = ('date', 'venue', 'created_by')
    search_fields = ('name', 'venue', 'description')
    readonly_fields = ('get_booked_count', 'get_held_count', 'get_available_count')
    
    def get_booked_count(self, obj):
        return obj.get_booked_count()
    get_booked_count.short_description = 'Booked'
    
    def get_held_count(self, obj):
        return obj.get_held_count()
    get_held_count.short_description = 'Held'
    
    def get_available_count(self, obj):
        return obj.get_available_count()
    get_available_count.short_description = 'Available'

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'booked_at', 'unique_code', 'is_checked_in')
    list_filter = ('event', 'is_checked_in', 'booked_at')
    search_fields = ('user__username', 'user__email', 'event__name', 'unique_code')
    readonly_fields = ('unique_code', 'qr_code')

@admin.register(TicketHold)
class TicketHoldAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'created_at', 'expires_at', 'login_timestamp', 'is_expired')
    list_filter = ('event', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'event__name')
    readonly_fields = ('created_at', 'is_expired')
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_timestamp', 'session_key', 'is_active')
    list_filter = ('is_active', 'login_timestamp')
    search_fields = ('user__username', 'user__email', 'session_key')
    readonly_fields = ('login_timestamp',)

# urls.py

from django.urls import path, include
from .views import (
    event_list, book_ticket, user_dashboard, custom_logout, 
    ticket_already_booked, checkin_ticket, download_ticket_pdf,
    calendar_view, release_hold, ticket_stats_api, about,
    privacy_policy, terms_of_service, contact_us, websocket_test
)
# No need to import SignupView or your custom signup_view here

urlpatterns = [
    path('', event_list, name='event_list'),
    path('about/', about, name='about'),
    path('privacy/', privacy_policy, name='privacy_policy'),
    path('terms/', terms_of_service, name='terms_of_service'),
    path('contact/', contact_us, name='contact_us'),
    path('book/<int:event_id>/', book_ticket, name='book_ticket'),
    path('already-booked/', ticket_already_booked, name='ticket_already_booked'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
    path('logout/', custom_logout, name='logout'),
    path('checkin/<int:ticket_id>/', checkin_ticket, name='checkin_ticket'),
    path('ticket/<int:ticket_id>/download/', download_ticket_pdf, name='download_ticket_pdf'),
    path('calendar/', calendar_view, name='calendar_view'),
    path('release-hold/<int:event_id>/', release_hold, name='release_hold'),
    path('api/ticket-stats/<int:event_id>/', ticket_stats_api, name='ticket_stats_api'),
    path('websocket-test/', websocket_test, name='websocket_test'),
    
    # This single line handles login, logout, signup, etc.
    path('accounts/', include('allauth.urls')), 
]
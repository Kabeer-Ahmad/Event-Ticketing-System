from django.shortcuts import render, get_object_or_404, redirect
from .models import Event, Ticket, TicketHold, UserSession
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from weasyprint import HTML
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.template.loader import render_to_string
import weasyprint
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
import json


def event_list(request):
    if request.user.is_authenticated:
        logout(request)
    
    events = Event.objects.all().order_by('date')
    events_with_stats = []
    
    for event in events:
        stats = event.get_ticket_stats()
        events_with_stats.append({
            'event': event,
            'stats': stats
        })
    
    return render(request, 'core/event_list.html', {
        'events_with_stats': events_with_stats
    })

@login_required
def book_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    with transaction.atomic():
        # Check if user can book this ticket
        can_book, reason = event.can_book_ticket(request.user)
        if not can_book:
            messages.error(request, reason)
            return redirect('user_dashboard')
        
        # Check if user has an active hold for this event
        try:
            hold = TicketHold.objects.get(
                event=event,
                user=request.user,
                expires_at__gt=timezone.now()
            )
            # Convert hold to actual ticket
            ticket = Ticket.objects.create(event=event, user=request.user)
            
            # Trigger QR code generation if it doesn't exist
            if not ticket.qr_code:
                from .signals import generate_qr_code
                generate_qr_code(Ticket, ticket, True)
            
            hold.delete()  # Remove the hold
            messages.success(request, f'Ticket booked successfully for {event.name}!')
            
        except TicketHold.DoesNotExist:
            # No hold exists, check if there's still capacity
            if event.get_available_count() <= 0:
                messages.error(request, 'Sorry, no tickets available for this event.')
                return redirect('user_dashboard')
            
            # Create ticket directly
            ticket = Ticket.objects.create(event=event, user=request.user)
            
            # Trigger QR code generation if it doesn't exist
            if not ticket.qr_code:
                from .signals import generate_qr_code
                generate_qr_code(Ticket, ticket, True)
            
            messages.success(request, f'Ticket booked successfully for {event.name}!')
    
    return render(request, 'core/ticket_success.html', {'ticket': ticket})

def ticket_already_booked(request):
    return render(request, 'core/ticket_already_booked.html')

@login_required
def user_dashboard(request):
    # Clean up expired holds first
    TicketHold.objects.filter(expires_at__lt=timezone.now()).delete()
    
    active_tickets = (
        Ticket.objects
              .filter(user=request.user, is_checked_in=False)
              .select_related('event')
    )
    used_tickets = (
        Ticket.objects
              .filter(user=request.user, is_checked_in=True)
              .select_related('event')
    )
    
    # Get user's active holds
    user_holds = (
        TicketHold.objects
                  .filter(user=request.user, expires_at__gt=timezone.now())
                  .select_related('event')
    )

    booked_event_ids = set(active_tickets.values_list('event_id', flat=True)) | \
                       set(used_tickets.values_list('event_id', flat=True))
    
    held_event_ids = set(user_holds.values_list('event_id', flat=True))

    all_events = Event.objects.all().order_by('date')
    
    # Prepare events with enhanced data
    events_with_data = []
    for event in all_events:
        stats = event.get_ticket_stats()
        
        # Determine event status for this user
        status = 'available'
        hold_expires_at = None
        
        if event.id in booked_event_ids:
            status = 'booked'
        elif event.id in held_event_ids:
            status = 'held'
            hold = user_holds.filter(event=event).first()
            hold_expires_at = hold.expires_at if hold else None
        elif stats['available'] <= 0:
            status = 'sold_out'
        
        events_with_data.append({
            'event': event,
            'stats': stats,
            'status': status,
            'hold_expires_at': hold_expires_at
        })

    return render(
        request,
        "core/dashboard.html",
        {
            "active_tickets": active_tickets,
            "used_tickets": used_tickets,
            "user_holds": user_holds,
            "events_with_data": events_with_data,
            "booked_event_ids": list(booked_event_ids),
        },
    )

@login_required
@require_POST 
def release_hold(request, event_id):
    """Allow user to manually release their hold on an event"""
    event = get_object_or_404(Event, id=event_id)
    
    try:
        hold = TicketHold.objects.get(
            event=event,
            user=request.user,
            expires_at__gt=timezone.now()
        )
        hold.delete()
        messages.success(request, f'Released your hold on {event.name}')
    except TicketHold.DoesNotExist:
        messages.error(request, 'No active hold found for this event')
    
    return redirect('user_dashboard')

def custom_logout(request):
    # Clear user's active holds when they logout
    if request.user.is_authenticated:
        TicketHold.objects.filter(user=request.user).delete()
        # Set ALL user sessions to inactive (handles multiple logins)
        UserSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
    
    logout(request)
    return redirect('event_list')

@login_required
@require_POST
def checkin_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)

    if ticket.is_checked_in:
        return JsonResponse({'status': 'already'})

    ticket.is_checked_in = True
    ticket.save()
    return JsonResponse({'status': 'ok'})

@login_required
def download_ticket_pdf(request, ticket_id):
    ticket = Ticket.objects.select_related('event').filter(id=ticket_id, user=request.user).first()
    if not ticket:
        raise Http404("Ticket not found")

    qr_absolute_url = request.build_absolute_uri(ticket.qr_code.url)
    template = get_template("core/ticket_pdf.html")
    html = template.render({"ticket": ticket, "qr_url": qr_absolute_url})
    pdf_file = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()

    resp = HttpResponse(pdf_file, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="ticket_{ticket.id}.pdf"'
    return resp

@login_required
def calendar_view(request):
    active_tickets = (
        Ticket.objects
              .filter(user=request.user, is_checked_in=False)
              .select_related('event')
    )
    used_tickets = (
        Ticket.objects
              .filter(user=request.user, is_checked_in=True)
              .select_related('event')
    )

    calendar_events = []

    for ticket in active_tickets:
        calendar_events.append({
            'title': ticket.event.name,
            'start': ticket.event.date.isoformat(),
            'color': '#20c997',
            'venue': ticket.event.venue,
            'status': 'Upcoming',
        })

    for ticket in used_tickets:
        calendar_events.append({
            'title': f"{ticket.event.name} (Checked-In)",
            'start': ticket.event.date.isoformat(),
            'color': '#adb5bd',
            'venue': ticket.event.venue,
            'status': 'Checked-In',
        })

    calendar_events_json = mark_safe(json.dumps(calendar_events))

    return render(request, 'core/calendar_view.html', {
        'calendar_events_json': calendar_events_json,
    })

@login_required
def ticket_stats_api(request, event_id):
    """API endpoint for real-time ticket statistics"""
    event = get_object_or_404(Event, id=event_id)
    stats = event.get_ticket_stats()
    
    # Add user-specific information
    user_has_ticket = event.ticket_set.filter(user=request.user).exists()
    user_has_hold = event.tickethold_set.filter(
        user=request.user,
        expires_at__gt=timezone.now()
    ).exists()
    
    stats.update({
        'user_has_ticket': user_has_ticket,
        'user_has_hold': user_has_hold,
    })
    
    return JsonResponse(stats)

def about(request):
    """Render the about page"""
    return render(request, 'core/about.html')

def privacy_policy(request):
    """Privacy Policy page view"""
    if request.user.is_authenticated:
        logout(request)
    return render(request, 'core/privacy_policy.html')

def terms_of_service(request):
    """Terms of Service page view"""
    if request.user.is_authenticated:
        logout(request)
    return render(request, 'core/terms_of_service.html')

def contact_us(request):
    """Contact Us page view"""
    if request.user.is_authenticated:
        logout(request)
    return render(request, 'core/contact_us.html')

def websocket_test(request):
    """Test page for WebSocket connections"""
    return render(request, 'core/websocket_test.html')
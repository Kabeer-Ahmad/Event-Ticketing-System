from django.core.management.base import BaseCommand
from core.models import Ticket
from core.signals import generate_qr_code

class Command(BaseCommand):
    help = 'Generate QR codes for tickets that are missing them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display detailed output',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        # Find tickets without QR codes
        tickets_without_qr = Ticket.objects.filter(qr_code='')
        count = tickets_without_qr.count()
        
        if verbose:
            self.stdout.write(f"Found {count} tickets without QR codes:")
        
        generated = 0
        for ticket in tickets_without_qr:
            try:
                if verbose:
                    self.stdout.write(f"  Generating QR for ticket {ticket.id} - {ticket.user.username} for {ticket.event.name}")
                
                # Generate QR code using the signal function
                generate_qr_code(Ticket, ticket, True)
                generated += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to generate QR for ticket {ticket.id}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated {generated} QR codes out of {count} tickets')
        ) 
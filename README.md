# 🎟️ Event Ticketing System

A modern, real-time event ticketing platform built with Django, Django Channels, and WebSockets. This system enables fair ticket distribution, live availability updates, and a seamless user experience for both attendees and administrators.

## 🚀 Features

### For Users
- **Smart Ticket Holding:** Automatically holds tickets for 10 minutes upon login (FIFO, fair access)
- **Real-Time Updates:** Live event availability and countdown timers via WebSockets
- **Modern Dashboard:** Glassmorphism UI, responsive design, and live status badges
- **Easy Booking:** Book tickets directly from holds or available pool
- **Session Management:** Secure login, session tracking, and instant feedback
- **QR Code Tickets:** Unique QR codes for each ticket with check-in functionality

### For Administrators
- **Comprehensive Admin Panel:** View/manage events, tickets, holds, and user sessions
- **Live Statistics:** Visual progress bars and real-time stats for each event
- **Session & Hold Cleanup:** Automated and manual management commands for expired data
- **Event Management:** Create, edit, and manage events with capacity tracking

## 🛠️ Tech Stack

- **Backend:** Django 5.2.3, Django Channels (ASGI), SQLite (default, easy to switch)
- **Frontend:** Django Templates, modern CSS, responsive design
- **Real-Time:** WebSockets (via Channels, Daphne ASGI server)
- **Authentication:** Django Allauth (with Google OAuth support)
- **QR Codes:** Unique ticket QR generation
- **Session Tracking:** Custom `UserSession` model for FIFO and security

## ⚡ Real-Time Architecture

- **WebSockets:** Persistent two-way connections for instant updates (event stats, dashboard timers)
- **Channels/ASGI:** Scalable, production-ready async server (Daphne recommended)
- **Signal Handlers:** Automatic broadcasting of ticket/hold changes to all connected clients
- **Live Countdowns:** Real-time countdown timers for ticket holds

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/event-ticketing-system.git
   cd event-ticketing-system
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install django==5.2.3
   pip install channels
   pip install daphne
   pip install django-allauth
   pip install django-widget-tweaks
   pip install qrcode
   pip install pillow
   pip install weasyprint
   pip install psycopg2-binary
   ```

4. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the ASGI server (for WebSockets):**
   ```bash
   daphne event_ticketing.asgi:application
   ```
   
   Or for development:
   ```bash
   python manage.py runserver
   ```

## 🧩 Configuration

### Key Settings
- **Hold Duration:** 10 minutes (configurable in `TicketHold` model)
- **Session Cleanup:** 24 hours for inactive sessions
- **WebSocket Layer:** In-memory by default, switch to Redis for production
- **Authentication:** Google OAuth enabled (requires setup in Google Console)

### Environment Variables
Create a `.env` file for production:
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=your-database-url
```

## 🧹 Management Commands

### Clean up expired holds and sessions:
```bash
python manage.py cleanup_expired_holds --verbose
```

### Automate cleanup (cron):
```bash
# Add to crontab for every 5 minutes
*/5 * * * * /path/to/venv/bin/python /path/to/project/manage.py cleanup_expired_holds
```

## 📁 Project Structure

```
event-ticketing-system/
├── core/                          # Main Django app
│   ├── models.py                  # Event, Ticket, TicketHold, UserSession models
│   ├── views.py                   # View logic and business logic
│   ├── consumers.py               # WebSocket consumers for real-time updates
│   ├── signals.py                 # Signal handlers for broadcasting updates
│   ├── middleware.py              # Ticket holding middleware
│   ├── admin.py                   # Django admin configuration
│   ├── urls.py                    # URL routing
│   ├── routing.py                 # WebSocket routing
│   ├── templates/core/            # HTML templates
│   ├── static/core/               # CSS, JS, images
│   └── management/                # Custom management commands
├── event_ticketing/               # Django project settings
│   ├── settings.py                # Django settings
│   ├── urls.py                    # Main URL configuration
│   └── asgi.py                    # ASGI configuration for WebSockets
├── media/                         # User uploaded files (QR codes)
├── manage.py                      # Django management script
└── README.md                      # This file
```

## 🎯 How It Works

### Ticket Holding System
1. **User Login:** System records login timestamp and creates holds on available events
2. **FIFO Ordering:** First-come-first-served based on login timestamp ensures fairness
3. **Hold Management:** 10-minute temporary reservations with real-time countdown
4. **Booking Process:** Convert holds to confirmed tickets or book directly if capacity allows

### Real-Time Features
1. **WebSocket Connections:** Persistent connections for instant updates
2. **Event Updates:** Live availability, booking counts, and capacity tracking
3. **Dashboard Timers:** Real-time countdown for ticket holds
4. **Status Indicators:** Connection status and live event status badges

### Capacity Management
- **Smart Tracking:** `booked + held ≤ capacity` prevents overselling
- **Real-time Calculation:** Live availability updates across all connected clients
- **Conflict Prevention:** Temporary holds reduce booking conflicts

## 🔧 Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### WebSocket Testing
Visit `/websocket-test/` to test WebSocket connections and real-time updates.

## 🚀 Deployment

### Production Setup
1. **Database:** Switch to PostgreSQL for production
2. **Static Files:** Configure static file serving
3. **Media Files:** Set up media file storage
4. **WebSocket Layer:** Use Redis for channel layers
5. **ASGI Server:** Use Daphne or Uvicorn with Gunicorn

### Example Production Settings
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

# Use Redis for channel layers
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Django](https://www.djangoproject.com/) - The web framework
- [Django Channels](https://channels.readthedocs.io/) - WebSocket support
- [Daphne ASGI Server](https://github.com/django/daphne) - ASGI server
- [django-allauth](https://github.com/pennersr/django-allauth) - Authentication
- [django-widget-tweaks](https://github.com/jazzband/django-widget-tweaks) - Form rendering

## 📞 Support

If you encounter any issues or have questions, please:
1. Check the [Issues](https://github.com/yourusername/event-ticketing-system/issues) page
2. Create a new issue with detailed information
3. Contact the maintainers

---

**Made with ❤️ for the event management community** 

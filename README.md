# 🎟️ Event Ticketing System

A modern, real-time web application for seamless event ticket booking, built with **Django**, **Django Allauth**, and **WebSockets**. Users can browse events, book tickets, view bookings on a dashboard, and enjoy instant updates without page refreshes.

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🚀 Features

✅ **User Authentication**  
- Traditional sign-up/login with email & password  
- Google OAuth sign-up and login (via Django Allauth)  

✅ **Event Browsing**  
- View upcoming events  
- See event details and capacity  

✅ **Ticket Booking**  
- Book tickets instantly  
- Download tickets as PDF with QR code  
- Prevent duplicate ticket bookings  

✅ **User Dashboard**  
- View active and past tickets  
- Real-time updates of booking status  

✅ **WebSocket Integration**  
- Live updates for event capacity  
- Dashboard notifications in real-time  
- Smooth countdown timers without page reloads  

✅ **Responsive UI**  
- Clean, modern design  
- Mobile-friendly layouts with Bootstrap and animations  

---

## 💻 Tech Stack

- Python 3.12  
- Django 5.2  
- Django Channels  
- Django Allauth  
- SQLite (default; easily replaceable with Postgres/MySQL)  
- Bootstrap 5  
- WeasyPrint (PDF generation)  
- JavaScript & WebSockets  

---

## 🛠️ Installation

1. **Clone the Repo**
    ```bash
    git clone https://github.com/Kabeer-Ahmad/Event-Ticketing-System.git
    cd Event-Ticketing-System
    ```

2. **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    venv\Scripts\activate     # Windows
    ```

3. **Install Requirements**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up Environment Variables**  
   Create a `.env` file or add these to your environment:
    ```env
    GOOGLE_CLIENT_ID=your-google-client-id
    GOOGLE_CLIENT_SECRET=your-google-client-secret
    SECRET_KEY=your-django-secret-key
    DEBUG=True
    ```

5. **Apply Migrations**
    ```bash
    python manage.py migrate
    ```

6. **Run the Server**
    ```bash
    python manage.py runserver
    ```
   Open your browser at: `http://127.0.0.1:8000`

---

### ⚙️ Google OAuth Setup

1. Go to Google Cloud Console.  
2. Create OAuth credentials.  
3. Add the authorized redirect URI:
    ```txt
    http://127.0.0.1:8000/accounts/google/login/callback/
    ```
4. Copy the Client ID and Secret into your environment variables.  
5. Add the social app in Django Admin:
   - **Provider:** Google  
   - **Client ID:** your client id  
   - **Secret Key:** your client secret  
   - **Sites:** 127.0.0.1  

---

## 📝 Development Notes

- **Templates** are located in:
  - `core/templates/core/` → core app views  
  - `core/templates/registration/` → custom login/signup  
  - `account/templates/account/` → allauth views  

- **WebSockets** configured in:
  - `asgi.py`  
  - `consumers.py`  

Real-time updates broadcast via Django signals.

---

## 🤝 Contributions

PRs welcome! Please fork the repo and submit a pull request.

---

## 📄 License

MIT License © Kabeer Ahmad

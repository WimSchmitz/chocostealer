"""
Pukkelpop Ticket Monitor with Flask Web Interface
Run with: python app.py
"""

import sqlite3
import threading
import time
import re
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash
import dotenv
import logging

# Load environment variables
dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Email configuration
EMAIL_ADDRESS = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# Constants
URL_TEMPLATE = "https://tickets.pukkelpop.be/nl/meetup/demand/?type={day}&camping={camping}&price=all"
MAIL_SUBJECT_TEMPLATE = "Pukkelpop Ticket Alert - {day} - {camping} - {price}"
MAIL_BODY_TEMPLATE = "A new ticket is available for {day} with {camping}. Price: {price}. \n\n Check it out here: {url}"

DATABASE_NAME = 'stealers.db'

# Logger setup
logger = logging.getLogger("chocostealer")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

days = {
    "day1": "Day 1",
    "day2": "Day 2", 
    "day3": "Day 3",
    "combi": "Combi"
}

campings = {
    "n": "No Camping",
    "a": "Camping Chill",
    "b": "Camping Relax"
}

# Database setup
def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Create subscribers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            day TEXT NOT NULL,
            camping TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    ''')

    # Create notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            subscriber_id INTEGER NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create tickets table for current availability
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            day TEXT NOT NULL,
            camping TEXT NOT NULL,
            price INTEGER NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def get_subscribers(day=None, camping=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    if day and camping:
        cursor.execute('''
            SELECT email FROM subscribers 
            WHERE day = ? AND camping = ? AND active = 1
        ''', (day, camping))
    else:
        cursor.execute('SELECT * FROM subscribers WHERE active = 1')
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_subscribers_to_notify(day, camping, ticket_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT subscribers.id, subscribers.email FROM subscribers
        LEFT JOIN notifications n ON subscribers.id = n.subscriber_id AND n.ticket_id = ?
        WHERE subscribers.day = ? AND subscribers.camping = ? AND subscribers.active = 1 AND n.ticket_id IS NULL
        GROUP BY subscribers.id, subscribers.email
    ''', (ticket_id, day, camping))
    
    results = cursor.fetchall()
    conn.close()
    return results

def add_subscriber(email, day, camping):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO subscribers (email, day, camping) 
            VALUES (?, ?, ?)
        ''', (email, day, camping))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Email already exists

def remove_subscriber(email):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE subscribers SET active = 0 WHERE email = ?', (email,))
    conn.commit()
    conn.close()

def log_notification(ticket_id, subscriber_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notifications (ticket_id, subscriber_id)
        VALUES (?, ?)
    ''', (ticket_id, subscriber_id))
    conn.commit()
    conn.close()

def get_notified_tickets():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT ticket_id FROM notifications')
    results = {row[0] for row in cursor.fetchall()}
    conn.close()
    return results

def reset_tickets():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tickets')
    conn.commit()
    conn.close()

def add_ticket(ticket_id, day, camping, price):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tickets (ticket_id, day, camping, price) 
        VALUES (?, ?, ?, ?)
    ''', (ticket_id, day, camping, price))

def get_current_tickets_overview():
    """Get a list of currently available tickets, grouped by day and camping, showing count and lowest price."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT day, camping, COUNT(*) as count, MIN(price) as lowest_price, MAX(url) as url
        FROM tickets
        GROUP BY day, camping
    ''')
    results = cursor.fetchall()
    conn.close()
    return results

# Email notification function
def notify_contacts(ticket_id, url, day, camping, price):
    logger.debug(f"Sending notifications for ID: {ticket_id}")
    
    subscribers = get_subscribers_to_notify(day, camping, ticket_id)
    if not subscribers:
        logger.debug(f"No subscribers to notify for {day} + {camping}")
        return
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            
            for (subscriber_id, email,) in subscribers:
                msg = EmailMessage()
                msg['Subject'] = MAIL_SUBJECT_TEMPLATE.format(
                    day=days[day], camping=campings[camping], price=price
                )
                msg['From'] = EMAIL_ADDRESS
                msg['To'] = email
                msg.set_content(MAIL_BODY_TEMPLATE.format(
                    day=days[day], camping=campings[camping], 
                    price=price, url=url
                ))
                
                smtp.send_message(msg)
                logger.debug(f"Email sent to {email}")
        
        log_notification(ticket_id, subscriber_id)
        return True
        
    except Exception as e:
        print(f"Email error: {e}")
        return False

# Background monitoring function
def monitor_tickets():
    logger.info("Starting ticket monitoring...")
    
    while True:
        try:
            logger.info(f"Checking tickets at {datetime.now()}")
            
            for day in days.keys():
                for camping in campings.keys():
                    url = URL_TEMPLATE.format(day=day, camping=camping)
                    
                    response = requests.get(url)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, "html.parser")
                    link_elements = soup.find_all('a', href=re.compile(r"^https://tickets\.pukkelpop\.be/nl/meetup/buy/"))
                    
                    ticket_count = len(link_elements)
                    lowest_price = None
                    
                    logger.info(f"Found {ticket_count} links for {day} + {camping}")
                    
                    if ticket_count > 0:
                        # Extract all prices and find the lowest
                        prices = []
                        for link_element in link_elements:
                            price_text = link_element.get_text(strip=True)
                            # Try to extract numeric value from price for comparison
                            price_match = re.search(r'€?\s*(\d+(?:\.\d{2})?)', price_text)
                            if price_match:
                                prices.append((float(price_match.group(1)), price_text))
                        
                        if prices:
                            lowest_price = min(prices, key=lambda x: x[0])[1]
                        
                        # Send notifications for each ticket
                        for link_element in link_elements:
                            price = link_element.get_text(strip=True)
                            link_url = link_element.get("href")
                            ticket_id = link_url.split("/")[-3]
                            
                            notify_contacts(ticket_id, url, day, camping, price)
                    
                    # Update ticket availability in database
                    update_ticket_availability(day, camping, ticket_count, lowest_price, url)
            
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(60)

# Flask routes
@app.route('/')
def index():
    current_tickets = get_current_tickets()
    return render_template_string(INDEX_TEMPLATE, 
                                days=days, 
                                campings=campings,
                                current_tickets=current_tickets)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    day = request.form.get('day')
    camping = request.form.get('camping')
    
    if not email or not day or not camping:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('index'))
    
    if camping == "all":
        if all(add_subscriber(email, day, c) for c in campings.keys()):
            flash(f'Successfully subscribed {email} for {days[day]} with all campings!', 'success')
    else:
        if add_subscriber(email, day, camping):
            flash(f'Successfully subscribed {email} for {days[day]} with {campings[camping]}!', 'success')
    
    return redirect(url_for('index'))

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.form.get('email')
    
    if not email:
        flash('Please enter your email', 'error')
        return redirect(url_for('index'))
    
    remove_subscriber(email)
    flash(f'Successfully unsubscribed {email}', 'success')
    return redirect(url_for('index'))

@app.route('/stats')
def stats():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Get subscriber stats
    cursor.execute('''
        SELECT day, COUNT(DISTINCT email) as count
        FROM subscribers 
        WHERE active = 1 
        GROUP BY day
    ''')
    subscriber_stats = cursor.fetchall()
    
    # Get recent notifications
    cursor.execute('''
        SELECT ticket_id, subscriber_id, sent_at 
        FROM notifications 
        ORDER BY sent_at DESC 
        LIMIT 10
    ''')
    recent_notifications = cursor.fetchall()
    
    conn.close()
    
    return render_template_string(STATS_TEMPLATE, 
                                stats=subscriber_stats, 
                                notifications=recent_notifications,
                                days=days, 
                                campings=campings)

# HTML Templates
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Pukkelpop Ticket Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .success { color: green; font-weight: bold; }
        .error { color: red; font-weight: bold; }
        .section { margin: 30px 0; padding: 20px; border: 1px solid #eee; border-radius: 8px; }
        h1 { color: #333; text-align: center; }
        h2 { color: #666; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .available { color: #28a745; font-weight: bold; }
        .no-tickets { color: #6c757d; font-style: italic; }
        .ticket-link { color: #007bff; text-decoration: none; }
        .ticket-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>🎪 Pukkelpop Ticket Monitor</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <div class="section">
        <h2>Currently Available Tickets</h2>
        {% if current_tickets %}
        <table>
            <thead>
                <tr>
                    <th>Day</th>
                    <th>Camping</th>
                    <th>Available</th>
                    <th>Lowest Price</th>
                    <th>Link</th>
                    <th>Last Updated</th>
                </tr>
            </thead>
            <tbody>
                {% for day, camping, count, lowest_price, url, last_updated in current_tickets %}
                <tr>
                    <td>{{ days[day] }}</td>
                    <td>{{ campings[camping] }}</td>
                    <td class="available">{{ count }} tickets</td>
                    <td>{{ lowest_price or 'N/A' }}</td>
                    <td><a href="{{ url }}" target="_blank" class="ticket-link">View Tickets</a></td>
                    <td>{{ last_updated }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p class="no-tickets">No tickets currently available. Subscribe below to get notified when they become available!</p>
        {% endif %}
    </div>
    
    <div class="section">
        <h2>Subscribe for Ticket Alerts</h2>
        <form method="POST" action="/subscribe">
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="day">Day:</label>
                <select name="day" required>
                    <option value="">Select Day</option>
                    {% for key, value in days.items() %}
                        <option value="{{ key }}">{{ value }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="form-group">
                <label for="camping">Camping:</label>
                <select name="camping" required>
                    <option value="">Select Camping</option>
                    {% for key, value in campings.items() %}
                        <option value="{{ key }}">{{ value }}</option>
                    {% endfor %}
                    <option value="all">All</option>
                </select>
            </div>
            
            <button type="submit">Subscribe</button>
        </form>
    </div>
    
    <div class="section">
        <h2>Unsubscribe</h2>
        <form method="POST" action="/unsubscribe">
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" name="email" required>
            </div>
            <button type="submit">Unsubscribe</button>
        </form>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="/stats">View Statistics</a>
    </div>
</body>
</html>
'''

STATS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Pukkelpop Monitor - Stats</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        h1 { color: #333; text-align: center; }
        h2 { color: #666; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        .back-link { text-align: center; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>📊 Pukkelpop Monitor Statistics</h1>
    
    <h2>Active Subscribers</h2>
    <table>
        <thead>
            <tr>
                <th>Day</th>
                <th>Subscribers</th>
            </tr>
        </thead>
        <tbody>
            {% for day, count in stats %}
            <tr>
                <td>{{ days[day] }}</td>
                <td>{{ count }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <h2>Recent Notifications</h2>
    <table>
        <thead>
            <tr>
                <th>Ticket ID</th>
                <th>Subscriber ID</th>
                <th>Sent At</th>
            </tr>
        </thead>
        <tbody>
            {% for ticket_id, subscriber_id, sent_at in notifications %}
            <tr>
                <td>{{ ticket_id }}</td>
                <td>{{ subscriber_id }}</td>
                <td>{{ sent_at }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="back-link">
        <a href="/">← Back to Home</a>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start background monitoring thread
    monitor_thread = threading.Thread(target=monitor_tickets, daemon=True)
    monitor_thread.start()
    
    # Start Flask app
    print("Starting Pukkelpop Ticket Monitor...")
    print("Web interface: http://localhost:5000")
    print("Statistics: http://localhost:5000/stats")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
import logging
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import smtplib
from email.message import EmailMessage
import dotenv
import sqlite3

from . import config

# Load environment variables from .env file
dotenv.load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)


# Database setup
def init_db():
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()

    # Create subscribers table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            day TEXT NOT NULL,
            camping TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    """
    )

    # Create notifications table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            subscriber_id INTEGER NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create tickets table for current availability
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            day TEXT NOT NULL,
            camping TEXT NOT NULL,
            price INTEGER NOT NULL,
            url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()


def get_notifications_to_send():
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 
            t.ticket_id,
            t.day,
            t.camping,
            t.price,
            t.url,
            s.id,
            s.email
        FROM 
            tickets t
        JOIN 
            subscribers s 
            ON t.day = s.day AND t.camping = s.camping
        LEFT JOIN 
            notifications n 
            ON n.ticket_id = t.ticket_id AND n.subscriber_id = s.id
        WHERE 
            n.id IS NULL
            AND s.active = 1;
    """
    )

    results = cursor.fetchall()
    conn.close()
    return results


def reset_tickets():
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets")
    conn.commit()
    conn.close()


def add_ticket(ticket_id, day, camping, price, url):
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tickets (ticket_id, day, camping, price, url) 
        VALUES (?, ?, ?, ?, ?)
    """,
        (ticket_id, day, camping, price, url),
    )

    conn.commit()
    conn.close()


def add_tickets(tickets):
    """
    Inserts multiple tickets into the database.

    :param tickets: List of tuples, each tuple containing
                    (ticket_id, day, camping, price, url)
    """
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT INTO tickets (ticket_id, day, camping, price, url) 
        VALUES (?, ?, ?, ?, ?)
        """,
        tickets,
    )

    conn.commit()
    conn.close()


def log_notification(ticket_id, subscriber_id):
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO notifications (ticket_id, subscriber_id)
        VALUES (?, ?)
    """,
        (ticket_id, subscriber_id),
    )
    conn.commit()
    conn.close()


def notify_subscribers():
    notifications = get_notifications_to_send()
    if notifications:
        logger.info(f"Subscribers to notify: {len(notifications)}")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
            for (
                ticket_id,
                day,
                camping,
                price,
                url,
                subscriber_id,
                subscriber_email,
            ) in notifications:
                try:
                    msg = EmailMessage()
                    msg["Subject"] = config.MAIL_SUBJECT_TEMPLATE.format(
                        day=config.DAYS[day],
                        camping=config.CAMPINGS[camping],
                        price=price,
                    )
                    msg["From"] = config.EMAIL_ADDRESS
                    msg["To"] = subscriber_email
                    msg.set_content(
                        config.MAIL_BODY_TEMPLATE.format(
                            day=config.DAYS[day],
                            camping=config.CAMPINGS[camping],
                            price=price,
                            url=url,
                        )
                    )
                    smtp.send_message(msg)
                    logger.info(f"Email sent to {subscriber_email}")
                    log_notification(ticket_id, subscriber_id)

                except Exception as e:
                    print(f"Email error: {e}")
                    return False


# Background monitoring function
def monitor_tickets():
    logger.info("Starting ticket monitoring...")

    while True:
        try:
            logger.info(f"Checking tickets at {datetime.now()}")
            tickets = []
            for day in config.DAYS.keys():
                for camping in config.CAMPINGS.keys():
                    url = config.URL_TEMPLATE.format(day=day, camping=camping)

                    response = requests.get(url)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, "html.parser")
                    link_elements = soup.find_all(
                        "a",
                        href=re.compile(
                            r"^https://tickets\.pukkelpop\.be/nl/meetup/buy/"
                        ),
                    )

                    ticket_count = len(link_elements)
                    logger.info(f"Found {ticket_count} links for {day} + {camping}")

                    if ticket_count > 0:
                        # Send notifications for each ticket & add to database
                        for link_element in link_elements:
                            price = link_element.get_text(strip=True)
                            link_url = config.URL_TEMPLATE.format(day=day, camping=camping)
                            ticket_id = link_element.get("href").split("/")[-3]
                            tickets.append((ticket_id, day, camping, price, link_url))

            reset_tickets()  # Clear tickets database
            add_tickets(tickets) # Add new tickets to the database
            notify_subscribers() # Notify subscribers of new tickets
            time.sleep(10)  # Check every 10 seconds

        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    print("Starting ticket monitoring service...")
    init_db()  # Initialize database
    monitor_tickets()  # This will run the monitoring loop

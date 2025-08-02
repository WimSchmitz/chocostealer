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


def get_subscribers_to_notify(day, camping, ticket_id):
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT subscribers.id, subscribers.email FROM subscribers
        LEFT JOIN notifications n ON subscribers.id = n.subscriber_id AND n.ticket_id = ?
        WHERE subscribers.day = ? AND subscribers.camping = ? AND subscribers.active = 1 AND n.ticket_id IS NULL
        GROUP BY subscribers.id, subscribers.email
    """,
        (ticket_id, day, camping),
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


# Email notification function
def notify_contacts(ticket_id, url, day, camping, price):
    logger.debug(f"Sending notifications for ID: {ticket_id}")

    subscribers = get_subscribers_to_notify(day, camping, ticket_id)
    if not subscribers:
        logger.debug(f"No subscribers to notify for {day} + {camping}")
        return

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)

            for (
                subscriber_id,
                email,
            ) in subscribers:
                msg = EmailMessage()
                msg["Subject"] = config.MAIL_SUBJECT_TEMPLATE.format(
                    day=config.DAYS[day], camping=config.CAMPINGS[camping], price=price
                )
                msg["From"] = config.EMAIL_ADDRESS
                msg["To"] = email
                msg.set_content(
                    config.MAIL_BODY_TEMPLATE.format(
                        day=config.DAYS[day],
                        camping=config.CAMPINGS[camping],
                        price=price,
                        url=url,
                    )
                )

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
            reset_tickets()  # Clear previous tickets
            logger.info(f"Checking tickets at {datetime.now()}")

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
                        # Extract all prices and find the lowest
                        prices = []
                        for link_element in link_elements:
                            price_text = link_element.get_text(strip=True)
                            # Try to extract numeric value from price for comparison
                            price_match = re.search(
                                r"€?\s*(\d+(?:\.\d{2})?)", price_text
                            )
                            if price_match:
                                prices.append((float(price_match.group(1)), price_text))

                        # Send notifications for each ticket
                        for link_element in link_elements:
                            price = link_element.get_text(strip=True)
                            link_url = link_element.get("href")
                            ticket_id = link_url.split("/")[-3]

                            add_ticket(ticket_id, day, camping, price, url)
                            notify_contacts(ticket_id, url, day, camping, price)

            time.sleep(30)  # Check every 30 seconds

        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(60)
            
if __name__ == '__main__':
    print("Starting ticket monitoring service...")
    init_db()  # Initialize database
    monitor_tickets()  # This will run the monitoring loop
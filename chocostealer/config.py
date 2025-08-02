import os
import dotenv

# Load environment variables
dotenv.load_dotenv()
if os.path.exists("/etc/chocostealer/.env"):
    dotenv.load_dotenv("/etc/chocostealer/.env")

APP_SECRET_KEY = os.environ.get('SECRET_KEY')

# Simple password protection
APP_PASSWORD = os.environ.get('APP_PASSWORD')

# Email configuration
EMAIL_ADDRESS = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# Constants
URL_TEMPLATE = "https://tickets.pukkelpop.be/nl/meetup/demand/?type={day}&camping={camping}&price=all"
MAIL_SUBJECT_TEMPLATE = "Pukkelpop Ticket Alert - {day} - {camping} - {price}"
MAIL_BODY_TEMPLATE = """
A new ticket is available for {day} with {camping}! Price: {price}. 

Check it out here: {url} \n\n 

To unsubscribe, visit https://www.pkpchecker.eu/ again and scroll down to the bottom.
"""

DATABASE_NAME = 'stealers.db'

DAYS = {
    "day1": "Friday",
    "day2": "Saturday", 
    "day3": "Sunday",
    "combi": "Combi"
}

CAMPINGS = {
    "n": "No Camping",
    "a": "Camping Chill",
    "b": "Camping Relax"
}
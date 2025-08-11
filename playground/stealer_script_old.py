import re
import time
import requests
from bs4 import BeautifulSoup

import os
import smtplib
from email.message import EmailMessage
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

EMAIL_ADDRESS = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    URL_TEMPLATE = "https://tickets.pukkelpop.be/nl/meetup/demand/?type={day}&camping={camping}&price=all"
    MAIL_SUBJECT_TEMPLATE = "Pukkelpop Ticket Alert - {day} - {camping} - {price}"
    MAIL_BODY_TEMPLATE = "A new ticket is available for {day} with {camping}. Price: {price}. \n\n Check it out here: {url}"

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

    contacts = [
        {
            "mail": "wim@schmitz.cc",
            "day": "day3",
            "camping": "b",
        }
    ]

    already_notified = set()

    def notify_contacts(id, url, day, camping, price):
        print(f"Sending notifications for ID: {id}, URL: {url}, Day: {day}, Camping: {camping}, Price: {price}")
        matching_contacts = [contact for contact in contacts if contact['day'] == day and contact['camping'] == camping]
        
        msg = EmailMessage()
        msg['Subject'] = MAIL_SUBJECT_TEMPLATE.format(day=days[day], camping=campings[camping], price=price)
        msg['From'] = EMAIL_ADDRESS

        msg.set_content(MAIL_BODY_TEMPLATE.format(day=days[day], camping=campings[camping], price=price, url=url))

        for contact in matching_contacts:
            msg['To'] = contact["mail"]
            print(f"Sending email to {contact}")
            smtp.send_message(msg)
        return True

    while True:
        try:
            print("Checking...")
            for day in days.keys():
                for camping in campings.keys():
                    url = URL_TEMPLATE.format(day=day, camping=camping)
                    print(f"Checking URL: {url}")
                    # Send a GET request to the URL
                    response = requests.get(url)
                    response.raise_for_status()

                    # Parse the HTML content
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Find all links with text that matches the pattern
                    link_elements = soup.find_all('a', href=re.compile(r"^https://tickets\.pukkelpop\.be/nl/meetup/buy/"))

                    for link_element in link_elements:
                        # Extract the text content from the tag
                        price = link_element.get_text(strip=True)
                        link_url = link_element.get("href")

                        ## Extract the id from https://tickets.pukkelpop.be/nl/meetup/buy/2494/d22c28bfc01e95f0362e750952eb4b21e5b1c351/
                        id = link_url.split("/")[-3]

                        # Submit the form with the filled data
                        if id not in already_notified:
                            response = notify_contacts(id, url, day, camping, price=price)
                            already_notified.update([id])
                        else:
                            print(f"Already contacted for ID: {id}, skipping.")

            # Wait for 10 seconds before checking again
            time.sleep(5)

        except requests.exceptions.RequestException as e:
            print("Error:", e)
            time.sleep(5)
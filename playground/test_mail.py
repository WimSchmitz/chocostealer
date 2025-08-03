from email.message import EmailMessage
import smtplib
from chocostealer import config


with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)

    msg = EmailMessage()
    msg["Subject"] = config.MAIL_SUBJECT_TEMPLATE.format(
        day="test", camping="camping", price="0"
    )
    msg["From"] = config.EMAIL_ADDRESS
    msg["To"] = "pkpchecker@gmail.com"
    msg.set_content(
        config.MAIL_BODY_TEMPLATE.format(
            day="test",
            camping="test",
            price="0",
            url="www.example.com/test",
        )
    )

    smtp.send_message(msg)
                
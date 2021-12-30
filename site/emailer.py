# Emailer
import json
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from email.utils import *

# Constants
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_DATA_FILENAME = "/share/aps/site/data.json"
with open(EMAIL_DATA_FILENAME) as jsonfile:
    emails = json.load(jsonfile)


class Emailer:
    def sendmail(self, recipient, subject, content):

        # Create Headers
        headers = [
            "From: " + emails["FromAddress"],
            "Subject: " + subject,
            "To: " + recipient,
            "MIME-Version: 1.0",
            "Content-Type: text/html",
        ]
        headers = "\r\n".join(headers)

        # Connect to Gmail Server
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls()
        session.ehlo()

        # Login to Gmail
        session.login(emails["FromAddress"], emails["FromPassword"])

        # Send Email & Exit
        session.sendmail(
            emails["FromAddress"], recipient, headers + "\r\n\r\n" + content
        )
        session.quit()

    def sendmail_attachment(self, recipient, subject, content, filename):
        msg = MIMEMultipart()
        msg["From"] = emails["FromAddress"]
        msg["To"] = recipient
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject
        msg.attach(MIMEText(content, "plain"))

        # Open file in binary mode
        with open(filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode attachment in ASCII
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header("Content-Disposition", "attachment", filename=filename)

        # Add attachment to msg and convert msg to string
        msg.attach(part)
        text = msg.as_string()

        # Log into server and send email
        email_context = ssl.create_default_context()

        # Connect to Gmail Server
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls(context=email_context)
        session.ehlo()

        # Login to Gmail
        session.login(emails["FromAddress"], emails["FromPassword"])

        # Send Email & Exit
        session.sendmail(emails["FromAddress"], recipient, text)
        session.quit

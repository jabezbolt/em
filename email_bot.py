import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import email.utils
import time

# Email credentials
IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ACCOUNT = 'intrust2021@gmail.com'
EMAIL_PASSWORD = 'cwqk izxj fjqu ecfb'
FORWARD_TO_EMAIL = 'info@intrustconsultancy.in'

# Keywords to identify important emails
KEYWORDS = ['urgent']

def is_important(subject, body):
    for keyword in KEYWORDS:
        if keyword in subject.lower() or keyword in body.lower():
            return True
    return False

def process_emails():
    # Calculate the date and time 10 minutes ago
    date_10_minutes_ago = datetime.now() - timedelta(minutes=10)

    # Connect to the server and login to the email account
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("inbox")

    # Search for emails received since the date 10 minutes ago
    status, messages = mail.search(None, f'SINCE {date_10_minutes_ago.strftime("%d-%b-%Y")}')
    email_ids = messages[0].split()

    # Iterate through each email
    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                from_ = msg.get("From")

                # Get the email date
                email_date = email.utils.parsedate_to_datetime(msg.get("Date"))

                # Convert email_date to naive if it's aware
                if email_date.tzinfo is not None:
                    email_date = email_date.replace(tzinfo=None)

                # Check if the email is within the last 10 minutes
                if datetime.now() - email_date <= timedelta(minutes=10):
                    # If the email message is multipart
                    if msg.is_multipart():
                        body = ""
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                try:
                                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                                except UnicodeDecodeError as e:
                                    print(f"Error decoding email body: {e}")
                                break
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                        except UnicodeDecodeError as e:
                            print(f"Error decoding email body: {e}")

                    # Check if the email is important
                    if is_important(subject, body):
                        # Forward the email
                        forward = MIMEMultipart()
                        forward["From"] = EMAIL_ACCOUNT
                        forward["To"] = FORWARD_TO_EMAIL
                        forward["Subject"] = "FWD: " + subject

                        forward.attach(MIMEText(body, "plain"))

                        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                            server.starttls()
                            server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
                            server.sendmail(EMAIL_ACCOUNT, FORWARD_TO_EMAIL, forward.as_string())

    # Logout and close the connection
    mail.logout()

# Main loop to run the script continuously
while True:
    process_emails()
    time.sleep(30)  # Sleep for 10 minutes

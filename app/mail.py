import smtplib, ssl
from ConfigReader import Configuration

config = Configuration.load_json('./app/config.json')

port = 465  # For SSL
smtp_server = config.gmail.smtp_server
sender_email = config.gmail.sender_email
receiver_email = config.gmail.receiver_email
password = config.gmail.password

def SendMail(subject, text):
    message = f"Subject: {subject}\n\n{text}"

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)



import smtplib
import ssl
from email.message import EmailMessage
from email.mime.text import MIMEText
import string
import random
from datetime import datetime
import os


def send_email(recipient):
    #generate an 8 digit code with letters and numbers
    letters=string.ascii_letters
    letters_without_Il=letters.replace("I","").replace("l","")
    numbers=string.digits
    letters_numbers=letters_without_Il+numbers
    code=random.choices(letters_numbers,k=8)
    confirmation_code=''.join(code)

    host="smtp.gmail.com"
    port=465


    user=os.getenv('SENDER_EMAIL')
    password=os.getenv('EMAIL_PASSWORD')

    recipient=recipient

    #msg=EmailMessage()

    message=f"""
    <html>
    <head></head>
    <body>
        <p>Hello</p>
        <p>the confirmation code is: <b>{confirmation_code}</b></p>
        <p></p>
        <p>Thank you for joining</p>
    </body>
    </html>
    """
    msg=MIMEText(message,'html')
    msg['From']=user
    msg['To']=recipient
    msg['Subject']='Confirmation code'


    context=ssl.create_default_context()

    with smtplib.SMTP_SSL(host=host,port=port,context=context) as server:
        server.login(user,password)
        server.send_message(msg)
    return confirmation_code


#creates a timestamp when the code was generated
def create_timestamp():
    date_time_now=datetime.now()
    return date_time_now


#generate confirmation code when email sending disabled
def code_generator():
    #generate an 8 digit code with letters and numbers
    letters=string.ascii_letters
    letters_without_Il=letters.replace("I","").replace("l","")
    numbers=string.digits
    letters_numbers=letters_without_Il+numbers
    code=random.choices(letters_numbers,k=8)
    confirmation_code=''.join(code)
    return confirmation_code
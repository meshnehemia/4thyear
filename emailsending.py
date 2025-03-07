import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def sendEmail(email,subject,message):

    # Gmail login credentials
    gmail_user = "meshnehemia7@gmail.com"
    gmail_password = "vlhl vwzs zbsc vquk"  # Make sure to use environment variables or secure storage for passwords

    # Email content
    recipient_email = email
    subject = subject
    body = message
    # Create the email
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Set up the Gmail SMTP server connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        server.login(gmail_user, gmail_password)

        # Send the email
        text = msg.as_string()
        server.sendmail(gmail_user, recipient_email, text)
        print("Email sent successfully!")

    except Exception as e:
        print(f"Error sending email: {e}")

    finally:
        # Terminate the SMTP session and close the connection
        server.quit()

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def sendEmail(email, subject,body):
    # Fetch Gmail login credentials from environment variables
    gmail_user = "meshnehemia7@gmail.com"
    gmail_password = "vlhl vwzs zbsc vquk"

    if not gmail_user or not gmail_password:
        print("Error: Gmail credentials not set in environment variables.")
        return

    # Email content
    recipient_email = email
    subject = subject

    # # HTML content for the receipt email
    # body = """
    # <html>
    # <head>
    #     <style>
    #         body {
    #             font-family: Arial, sans-serif;
    #         }
    #         .header {
    #             background-color: #4CAF50;
    #             color: white;
    #             padding: 10px;
    #             text-align: center;
    #             font-size: 24px;
    #             font-weight: bold;
    #         }
    #         .receipt-table {
    #             width: 100%;
    #             border-collapse: collapse;
    #             margin-top: 20px;
    #         }
    #         .receipt-table, .receipt-table th, .receipt-table td {
    #             border: 1px solid black;
    #         }
    #         .receipt-table th, .receipt-table td {
    #             padding: 10px;
    #             text-align: left;
    #         }
    #         .footer {
    #             margin-top: 20px;
    #             text-align: center;
    #             font-size: 12px;
    #             color: #777;
    #         }
    #     </style>
    # </head>
    # <body>
    #     <div class="header">Intelligent Supermarket Management System</div>
    #     <h2>Account Verification Receipt</h2>
    #     <p>Thank you for purchasing data from our system. Below is your transaction receipt:</p>
        
    #     <table class="receipt-table">
    #         <tr>
    #             <th>Description</th>
    #             <th>Amount</th>
    #         </tr>
    #         <tr>
    #             <td>Data Purchase</td>
    #             <td>$50.00</td>
    #         </tr>
    #         <tr>
    #             <td>Transaction Fee</td>
    #             <td>$2.00</td>
    #         </tr>
    #         <tr>
    #             <td><strong>Total</strong></td>
    #             <td><strong>$52.00</strong></td>
    #         </tr>
    #     </table>

    #     <p>Please click the link below to verify your account and complete your purchase:</p>
    #     <a href="https://www.intelligent-supermarket.com/verify-account?token=your-verification-token">Verify Account</a>

    #     <div class="footer">
    #         Intelligent Supermarket Management System | &copy; 2025 All rights reserved
    #     </div>
    # </body>
    # </html>
    # """

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = "intelligence management system"
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))  # Attach HTML body

    try:
        # Set up the Gmail SMTP server connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        server.login(gmail_user, gmail_password)

        # Send the email
        server.sendmail(gmail_user, recipient_email, msg.as_string())
        print("Email sent successfully!")

    except Exception as e:
        print(f"Error sending email: {e}")

    finally:
        # Terminate the SMTP session and close the connection
        server.quit()

# Example usage:
# Set environment variables in your system or before running the script
# export GMAIL_USER="your-email@gmail.com"
# export GMAIL_PASSWORD="your-app-password"
# sendEmail("recipient@example.com", "Account Verification Receipt")

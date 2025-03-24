import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, request, jsonify
# Function to get MPesa access token
def get_mpesa_access_token():
    auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    consumer_key = 'Fdb1nVPWja3hIvxmIM8GOAe4Y8gnzKwStca7WxD7ngCWyCn9'  # Your consumer key
    consumer_secret = 'VcR6HvnBM2ONXxQd0CBKGhCz7W8SGNTIgwUxWEzyIGnAev7hMiJ8SJfbtPe3iLNI'  # Your consumer secret

    # Request the access token with proper authorization headers
    response = requests.get(auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))

    print(f"Response Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Body: {response.text}")

    if response.status_code == 200:
        access_token = response.json().get('access_token')
        return access_token
    else:
        raise Exception("Could not get access token from MPesa API")
def send_mpesa_payment(phone,order_id,amount):
    try:
        access_token = get_mpesa_access_token()

        # Headers for the API request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        # Payload for sending the SSD to the phone number
        payload = {
            "BusinessShortCode": 174379,  # Replace with your valid shortcode
            "Password": "MTc0Mzc5YmZiMjc5ZjlhYTliZGJjZjE1OGU5N2RkNzFhNDY3Y2QyZTBjODkzMDU5YjEwZjc4ZTZiNzJhZGExZWQyYzkxOTIwMjUwMTEzMTQ0OTUz",  # Replace with your valid password
            "Timestamp": "20250113144953",  # Ensure the timestamp is correctly generated
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,  # Amount to send (1 shilling in this case)
            "PartyA":phone,  # Replace with the sender's phone number in international format
            "PartyB": 174379,  # Replace with your business shortcode
            "PhoneNumber": 254757316903,  # Phone number to send the money to
            "CallBackURL": f"https://pensive-forest-24613.pktriot.net/mpesa/callback/{order_id}",
            "AccountReference": "Intelligent management system ",  # Reference for the payment
            "TransactionDesc": "payment for the purchases "  # Description of the payment
        }

        # Send the request to the MPesa API
        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            headers=headers,
            json=payload  # Use json=payload to send the request in JSON format
        )

        # Print the response from the API
        print(response.text.encode('utf8'))

        print(f"Processing Mpesa payment for phone number: {phone}")
        return {"status": "success", "message": 'wait for mpesa code'}  # Ensure this function returns a dictionary
    except Exception as e:
        print(phone)
        print(f"Error during payment processing: {e}")
        return {"status": "failure", "message": str(e)}
    

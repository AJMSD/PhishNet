from twilio.rest import Client
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()  # Load environment variables from .env file

account_sid = os.getenv('ACCOUNT_SID')  # Retrieve account SID from .env
auth_token = os.getenv('AUTH_TOKEN')  # Retrieve auth token from .env
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')  # Retrieve Twilio from number
TWILIO_TO_NUMBER = os.getenv('TWILIO_TO_NUMBER')  # Retrieve Twilio to number
alert_message = "Fraud alert: Suspicious activity detected!"  # Example alert message
transaction_id = "12345"  # Example transaction ID
TRANSACTION_MAP_TABLE = {}  # Example placeholder for transaction map table

client = Client(account_sid, auth_token)

# Send SMS via Twilio
try:
    sms_message = client.messages.create(
        body=alert_message,
        from_=TWILIO_FROM_NUMBER,
        to=TWILIO_TO_NUMBER
    )
    print(f"📲 Fraud alert SMS sent via Twilio (SID: {sms_message.sid})")
except Exception as e:
    print(f"❌ Error sending SMS via Twilio: {e}")

# Store mapping in UserFraudTransactionsMap
try:
    TRANSACTION_MAP_TABLE['Item'] = {
        'PhoneNumber': TWILIO_TO_NUMBER,
        'TransactionID': transaction_id,
        'Timestamp': datetime.utcnow().isoformat(),
        'Status': 'Pending'
    }
    print(f"✅ Stored mapping for {TWILIO_TO_NUMBER} → {transaction_id}")
except Exception as e:
    print(f"❌ Error storing transaction mapping: {e}")


# This code snippet is simplified version of what is placed in the AWS lambda to showcase my work
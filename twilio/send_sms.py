from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

account_sid = os.getenv('ACCOUNT_SID')  # Retrieve account SID from .env
auth_token = os.getenv('AUTH_TOKEN')  # Retrieve auth token from .env
client = Client(account_sid, auth_token)

message = client.messages.create(
  from_='+18887583189',
  body='Hello from Twilio',
  to='+18777804236'
)

print(message.sid)
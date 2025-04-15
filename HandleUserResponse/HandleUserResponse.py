import boto3
import base64
import urllib.parse
from boto3.dynamodb.conditions import Key

# DynamoDB Tables
map_table = boto3.resource('dynamodb').Table("UserFraudTransactionsMap")
txn_table = boto3.resource('dynamodb').Table("Transactions")
user_table = boto3.resource('dynamodb').Table("Users")

def lambda_handler(event, context):
    print(f"Received event: {event}")

    # Decode body if base64-encoded
    raw_body = event['body']
    if event.get('isBase64Encoded'):
        raw_body = base64.b64decode(raw_body).decode('utf-8')

    # Parse x-www-form-urlencoded content
    body = urllib.parse.parse_qs(raw_body)
    sms_body = body.get('Body', [''])[0].strip().lower()
    sender = body.get('From', [''])[0]

    print(f"SMS received from {sender}: '{sms_body}'")

    # Handle "travel - {location}" to enable travel mode
    if sms_body.startswith('travel -'):
        try:
            location = sms_body.split('travel -')[1].strip().title()
            user_table.update_item(
                Key={'User_ID': sender},
                UpdateExpression="SET TravelMode = :val, TravelLocation = :loc",
                ExpressionAttributeValues={
                    ":val": True,
                    ":loc": location
                }
            )
            print(f"Enabled travel mode for {sender} to {location}")
            return respond(f"Travel mode enabled for {location}. Reply 'stop travel' to disable it anytime.")
        except Exception as e:
            print(f"Error enabling travel mode: {e}")
            return respond("Something went wrong while enabling travel mode. Please try again.")

    # Handle "stop travel" to disable travel mode
    if sms_body.strip() == 'stop travel':
        try:
            user_table.update_item(
                Key={'User_ID': sender},
                UpdateExpression="SET TravelMode = :val REMOVE TravelLocation",
                ExpressionAttributeValues={
                    ":val": False
                }
            )
            print(f"Disabled travel mode for {sender}")
            return respond("Travel mode disabled. Fraud detection is now back to normal sensitivity.")
        except Exception as e:
            print(f"Error disabling travel mode: {e}")
            return respond("Something went wrong while disabling travel mode. Please try again.")

    # Handle fraud confirmation responses
    transaction_id = get_latest_pending_transaction(sender)
    if not transaction_id:
        print(f"No pending transaction found for {sender}")
        return respond("No recent fraud alert found for your number.")

    # Interpret user response
    if sms_body in ['yes', 'fraud']:
        print(f"User {sender} confirmed transaction {transaction_id} as FRAUD")
        new_status = "FRAUD"
    elif sms_body in ['no', 'not fraud']:
        print(f"User {sender} confirmed transaction {transaction_id} as NOT FRAUD")
        new_status = "Not Fraud"
    else:
        return respond("Please reply YES or NO to verify the transaction. To enable travel mode, reply 'travel - your location'.")

    try:
        # Update the Transactions table
        txn_table.update_item(
            Key={'TransactionID': transaction_id},
            UpdateExpression="SET #s = :val",
            ExpressionAttributeNames={"#s": "Status"},
            ExpressionAttributeValues={":val": new_status}
        )
        print(f"Updated transaction {transaction_id} to '{new_status}'")

        # Remove the mapping
        map_table.delete_item(
            Key={'PhoneNumber': sender, 'TransactionID': transaction_id}
        )
        print(f"Deleted mapping for {transaction_id}")

        return respond(f"Thanks! Transaction {transaction_id} marked as {new_status}.")
    except Exception as e:
        print(f"Error updating records: {e}")
        return respond("Something went wrong. Please try again later.")

def get_latest_pending_transaction(phone_number):
    try:
        result = map_table.query(
            KeyConditionExpression=Key('PhoneNumber').eq(phone_number),
            ScanIndexForward=False,
            Limit=5
        )
        for item in result.get('Items', []):
            if item.get("Status") == "Pending":
                return item['TransactionID']
    except Exception as e:
        print(f"Error querying mapping table: {e}")
    return None

def respond(message):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/plain"},
        "body": message
    }

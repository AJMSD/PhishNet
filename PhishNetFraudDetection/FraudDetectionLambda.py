import json
import boto3
import os

# AWS Clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Set DynamoDB Table and SNS Topic ARN
DYNAMODB_TABLE = dynamodb.Table("Transactions")
SNS_TOPIC_ARN = "arn:aws:sns:us-east-2:842675989308:PhishNetAlerts"

# Email recipient for fraud alerts
EMAIL_RECIPIENT1 = "aman.jain030704@gmail.com"
EMAIL_RECIPIENT2 = "koegel.summit78@gmail.com"
EMAIL_RECIPIENT3 = "goseh30123@cybtric.com"

def lambda_handler(event, context):
    print("*** STARTING LAMBDA EXECUTION ***")
    print("Received event from SQS:", json.dumps(event))

    for record in event['Records']:
        # Read message from SQS
        print("Raw message body:", record['body'])
        
        try:
            message = json.loads(record['body'])
            if isinstance(message, str):  # Handle double-encoded JSON
                message = json.loads(message)
        except json.JSONDecodeError:
            print("ERROR: Failed to decode JSON message:", record['body'])
            return {"statusCode": 400, "body": "Invalid JSON"}
        
        transaction_id = message.get('TransactionID')

        if not transaction_id:
            print("ERROR: TransactionID is missing from message!")
            continue

        print(f"Processing Transaction: {transaction_id}")

        # Fetch transaction details from DynamoDB
        response = DYNAMODB_TABLE.get_item(Key={'TransactionID': transaction_id})

        if 'Item' not in response:
            print(f"Transaction {transaction_id} not found in DynamoDB")
            continue

        transaction = response['Item']
        amount = float(transaction['Amount'])  # Convert from Decimal
        fraud_risk = float(transaction.get('RiskScore', 0))
        location = transaction.get('Location', 'Unknown')
        user_id = transaction.get('UserID', 'Unknown')
        flagged_as_fraud = False

        location_risk_score = check_location_risk(location)
        amount_risk_score = check_amount_risk(amount)

        fraud_score = (fraud_risk * 100) + amount_risk_score + location_risk_score
        print(f"Transaction {transaction_id} fraud score: {fraud_score}")

        fraud_threshold = 50

        if fraud_score > fraud_threshold:
            flagged_as_fraud = True

        # If fraudulent, update status & send alert
        if flagged_as_fraud:
            print(f"Fraud detected: Transaction ID {transaction_id}, Amount: ${amount}, Location: {location}")

            # Update the transaction status in DynamoDB
            update_transaction_status(transaction_id, "Sent to User")

            # Send an email notification via SNS
            send_fraud_alert(transaction_id, amount, user_id)

    return {"statusCode": 200, "body": "Processing complete"}

def check_location_risk(location):
    high_risk_locations = ["Dubai", "Tokyo", "London"]
    if location in high_risk_locations:
        return 30
    return 0

def check_amount_risk(amount):
    if amount > 3000:
        return 40
    elif amount > 1000:
        return 20
    else:
        return 0

def update_transaction_status(transaction_id, status):
    """Update the transaction status in DynamoDB"""
    try:
        DYNAMODB_TABLE.update_item(
            Key={'TransactionID': transaction_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "Status"},
            ExpressionAttributeValues={":status": status}
        )
        print(f"Transaction {transaction_id} status updated to '{status}'")
    except Exception as e:
        print(f"Error updating transaction {transaction_id}: {e}")

def send_fraud_alert(transaction_id, amount, user_id):
    """Send an SNS email alert when fraud is detected"""
    alert_message = (
        f"Fraud Alert Detected \n"
        f"- Transaction ID: {transaction_id}\n"
        f"- Amount: ${amount}\n"
        f"- User: {user_id}\n\n"
        f"Action is required to verify this transaction."
    )

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=alert_message,
            Subject="Fraud Alert Notification",
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': "EMAIL_RECIPIENT1"
                }
            }
        )
        print(f"Fraud alert email sent to {EMAIL_RECIPIENT1}")
    except Exception as e:
        print(f"Error sending SNS email: {e}")

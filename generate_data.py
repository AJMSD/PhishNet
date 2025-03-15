import json
import random
import uuid
import datetime
import pandas as pd
from faker import Faker
import boto3
from decimal import Decimal

# Initialize faker
fake = Faker()

# AWS setup (uncomment when ready to upload to DynamoDB)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Connect to your DynamoDB table
transactions_table = dynamodb.Table('Transactions')

def generate_users(num_users=100):
    """Generate a list of fake users"""
    users = []
    for _ in range(num_users):
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        user = {
            'UserID': user_id,
            'Name': fake.name(),
            'Email': fake.email(),
            'Phone': fake.phone_number(),
            'Address': fake.address(),
            'AccountCreated': fake.date_time_this_year().isoformat(),
            'CreditScore': random.randint(300, 850),
            'TypicalSpendingPattern': random.choice(['Low', 'Medium', 'High']),
            'AverageTransactionAmount': round(random.uniform(10, 500), 2)
        }
        users.append(user)
    return users

def generate_transactions(users, num_transactions=1000):
    """Generate fake transactions for users"""
    transactions = []
    merchants = [
        "Amazon", "Walmart", "Target", "Starbucks", "McDonald's", 
        "Best Buy", "Apple Store", "Gas Station", "Grocery Store",
        "Restaurant", "Hotel", "Airline", "Online Service"
    ]
    
    for _ in range(num_transactions):
        user = random.choice(users)
        user_id = user.get('UserID', None)  # Ensure valid user_id is extracted
        
        # Ensure user_id is always valid, and handle missing or invalid user_id
        if not user_id:
            print(f"Skipping transaction because 'user_id' is missing in user: {user}")
            continue
        
        is_potential_fraud = random.random() < 0.1
        
        if is_potential_fraud:
            amount = round(random.uniform(1000, 5000), 2)
            fraud_status = "Fraudulent"
            risk_score = random.randint(70, 100)  # Higher risk for fraud
        else:
            base_amount = user.get('AverageTransactionAmount', 150.0)  # Default value if missing
            amount = round(random.uniform(0.5 * base_amount, 2 * base_amount), 2)
            fraud_status = "Legitimate"
            risk_score = random.randint(0, 69)  # Lower risk for legitimate transactions
        
        timestamp = fake.date_time_this_month().isoformat()
        
        # Handle location generation based on fraud status
        if is_potential_fraud and random.random() < 0.7:
            location = fake.city() + ", " + fake.state_abbr()
        else:
            address_parts = user.get('Address', '').split('\n')
            location = address_parts[1] if len(address_parts) > 1 else fake.city() + ", " + fake.state_abbr()
        
        # Ensure valid transaction_id using UUID
        transaction_id = f"txn_{uuid.uuid4().hex[:10]}"
        
        # Construct the transaction dictionary
        transaction = {
            'transaction_id': transaction_id,  # Ensure valid transaction ID
            'user_id': user_id,  # Ensure valid user ID
            'Amount': Decimal(str(amount)),  # Ensure Amount is in Decimal format
            'Timestamp': timestamp,
            'FraudStatus': fraud_status,
            'RiskScore': risk_score,
            'Location': location
        }

        # Debugging: Check if the transaction ID and user ID are correctly generated
        if not transaction['transaction_id'] or not transaction['user_id']:
            print(f"Error: Missing primary key attributes in transaction: {transaction}")
        
        transactions.append(transaction)
    
    return transactions


def save_to_files(users, transactions):
    """Save generated data to JSON and CSV files"""
    
    # Convert Decimal objects in transactions to float for JSON serialization
    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert Decimal to float
        raise TypeError("Type not serializable")

    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)
    
    with open('transactions.json', 'w') as f:
        json.dump(transactions, f, indent=2, default=decimal_default)
    
    pd.DataFrame(users).to_csv('users.csv', index=False)
    pd.DataFrame(transactions).to_csv('transactions.csv', index=False)
    
    print(f"Generated {len(users)} users and {len(transactions)} transactions")
    print("Data saved to users.json, transactions.json, users.csv, and transactions.csv")

def upload_to_dynamodb(transactions):
    # Create a batch writer for batch uploads
    with transactions_table.batch_writer() as batch:
        for transaction in transactions:
            # Print the transaction data for debugging
            #print(f"Transaction Data: {transaction}")

            # Ensure the correct primary key attribute names
            transaction['transaction_id'] = transaction.get('transaction_id', None)
            transaction['user_id'] = transaction.get('user_id', None)

            # Check if both primary key attributes are present
            
            if transaction['transaction_id'] is None or transaction['user_id'] is None:
                print(f"Error: Missing primary key attributes in transaction: {transaction}")
                continue  # Skip this transaction and move to the next
            
            

            try:
                # Use batch writer to put items in the table
                batch.put_item(Item=transaction)
                #print(f"Successfully uploaded transaction {transaction['transaction_id']}")
            except Exception as e:
                print(f"Failed to upload transaction {transaction['transaction_id']}: {e}")




if __name__ == "__main__":
    users = generate_users(100)
    transactions = generate_transactions(users, 1000)
    
    save_to_files(users, transactions)
    
    upload_to_dynamodb(transactions)

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
# dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
# transactions_table = dynamodb.Table('Transactions')
# users_table = dynamodb.Table('Users')  # If you have a Users table

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
        # Randomly select a user
        user = random.choice(users)
        user_id = user['UserID']
        
        # Determine if this should be a fraudulent transaction (10% chance)
        is_potential_fraud = random.random() < 0.1
        
        # Generate transaction amount based on user's typical spending pattern
        if is_potential_fraud:
            # Fraudulent transactions have higher amounts
            amount = round(random.uniform(1000, 5000), 2)
        else:
            # Normal transactions based on user's average
            base_amount = user['AverageTransactionAmount']
            amount = round(random.uniform(0.5 * base_amount, 2 * base_amount), 2)
        
        # Generate transaction timestamp
        timestamp = fake.date_time_this_month().isoformat()
        
        # Generate location (sometimes different for fraudulent transactions)
        if is_potential_fraud and random.random() < 0.7:
            # Location different from user's address
            location = fake.city() + ", " + fake.state_abbr()
        else:
            # Extract city and state from user's address
            address_parts = user['Address'].split('\n')
            if len(address_parts) > 1:
                location = address_parts[1]
            else:
                location = fake.city() + ", " + fake.state_abbr()
        
        transaction = {
            'TransactionID': f"txn_{uuid.uuid4().hex[:10]}",
            'UserID': user_id,
            'Amount': amount,
            'Timestamp': timestamp,
            'Merchant': random.choice(merchants),
            'Location': location,
            'Category': random.choice(["Shopping", "Food", "Travel", "Entertainment", "Utilities", "Other"]),
            'PaymentMethod': random.choice(["Credit Card", "Debit Card", "Mobile Payment", "Online"]),
            'Status': "Pending"  # Initial status, would be updated by fraud detection system
        }
        
        transactions.append(transaction)
    
    return transactions

def save_to_files(users, transactions):
    """Save generated data to JSON files"""
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)
    
    with open('transactions.json', 'w') as f:
        json.dump(transactions, f, indent=2)
    
    # Also save as CSV for easy viewing
    pd.DataFrame(users).to_csv('users.csv', index=False)
    pd.DataFrame(transactions).to_csv('transactions.csv', index=False)
    
    print(f"Generated {len(users)} users and {len(transactions)} transactions")
    print("Data saved to users.json, transactions.json, users.csv, and transactions.csv")

def upload_to_dynamodb(transactions):
    """Upload transactions to DynamoDB"""
    # Convert float amounts to Decimal for DynamoDB
    for transaction in transactions:
        transaction['Amount'] = Decimal(str(transaction['Amount']))
    
    with transactions_table.batch_writer() as batch:
        for transaction in transactions:
            batch.put_item(Item=transaction)
    
    print(f"Uploaded {len(transactions)} transactions to DynamoDB")

if __name__ == "__main__":
    # Generate fake data
    users = generate_users(100)  # 100 users
    transactions = generate_transactions(users, 1000)  # 1000 transactions
    
    # Save to files
    save_to_files(users, transactions)
    
    # Uncomment to upload to DynamoDB when ready
    # upload_to_dynamodb(transactions)
import json
import boto3
import random
import uuid
from decimal import Decimal
import datetime

# Connect to your DynamoDB tables
dynamodb = boto3.resource('dynamodb')
TEST_TRANSACTIONS_TABLE = dynamodb.Table("TestTransactions")
TEST_RESULTS_TABLE = dynamodb.Table("TestResults")  # New table to store test results

def lambda_handler(event, context):
    # Generate test data with known fraud status (100 test transactions)
    test_data = generate_test_data(100)
    
    # Test results using your rule-based fraud detection algorithm
    rule_based_results = test_rule_based_algorithm(test_data)
    
    # Store results in DynamoDB for analysis
    store_test_results(rule_based_results)
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "rule_based_accuracy": rule_based_results["accuracy"],
            "total_transactions": len(test_data),
            "fraud_transactions": sum(1 for t in test_data if t["IsActualFraud"])
        })
    }

def store_test_transaction(transaction):
    """Store a single transaction in the TestTransactions table"""
    try:
        TEST_TRANSACTIONS_TABLE.put_item(Item=transaction)
        print(f"Stored transaction {transaction['TransactionID']} in TestTransactions")
    except Exception as e:
        print(f"Error storing transaction {transaction['TransactionID']}: {e}")

def generate_test_data(num_transactions):
    """Generate test transactions with known fraud status"""
    test_data = []
    
    # Merchant risk weights from your actual system
    merchant_fraud_weights = {
        "Amazon": 0.2,
        "Walmart": 0.15,
        "Target": 0.2,
        "Starbucks": 0.1,
        "McDonald's": 0.1,
        "Best Buy": 0.3,
        "Apple Store": 0.25,
        "Gas Station": 0.25,
        "Grocery Store": 0.3,
        "Restaurant": 0.3,
        "Hotel": 0.5,
        "Airline": 0.7,
        "Online Service": 0.55
    }
    
    locations = ["New York", "Los Angeles", "Chicago", "Miami", "London", "Tokyo", "Dubai"]
    
    # Generate both fraudulent and legitimate transactions
    for i in range(num_transactions):
        # Decide if this will be fraudulent (20% chance)
        is_fraud = random.random() < 0.2
        
        # Select merchant based on fraud likelihood
        if is_fraud:
            # For fraudulent transactions, bias toward high-risk merchants
            weighted_merchants = [(m, w) for m, w in merchant_fraud_weights.items()]
            weighted_merchants.sort(key=lambda x: x[1], reverse=True)
            merchant = random.choice(weighted_merchants[:5])[0]
        else:
            # For legitimate transactions, bias toward low-risk merchants
            weighted_merchants = [(m, w) for m, w in merchant_fraud_weights.items()]
            weighted_merchants.sort(key=lambda x: x[1])
            merchant = random.choice(weighted_merchants[:5])[0]
        
        # Generate appropriate amount and convert to Decimal
        if is_fraud:
            amount = Decimal(str(round(random.uniform(800, 5000), 2)))
        else:
            amount = Decimal(str(round(random.uniform(10, 700), 2)))
        
        # Select appropriate location
        if is_fraud and random.random() < 0.7:
            location = random.choice(["London", "Tokyo", "Dubai"])  # High-risk locations
        else:
            location = random.choice(["New York", "Los Angeles", "Chicago", "Miami"])
        
        # Create the transaction (convert numeric values to Decimal as needed)
        transaction = {
            'TransactionID': f"test_txn_{uuid.uuid4().hex[:10]}",
            'UserID': f"test_user_{i}",
            'Amount': amount,
            'Timestamp': datetime.datetime.now().isoformat(),
            'Merchant': merchant,
            'Category': random.choice(["Shopping", "Food", "Travel", "Entertainment", "Utilities", "Other"]),
            'PaymentMethod': random.choice(["Credit Card", "Debit Card", "Mobile Payment", "Online"]),
            'Location': location,
            'RiskScore': Decimal(str(merchant_fraud_weights[merchant])),
            'Status': "Pending",
            'IsActualFraud': is_fraud  # Ground truth for testing
        }
        
        # Store the synthetic transaction in the TestTransactions table
        store_test_transaction(transaction)
        
        test_data.append(transaction)
    
    return test_data

def test_rule_based_algorithm(test_data):
    """Test rule-based fraud detection algorithm"""
    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0
    
    for transaction in test_data:
        # Use your rule-based algorithm
        amount = transaction['Amount']
        location = transaction['Location']
        risk_score = float(transaction['RiskScore'])  # Convert Decimal to float for calculation
        
        # Calculate fraud score using your rule-based approach
        location_risk = 30 if location in ["Dubai", "Tokyo", "London"] else 0
        
        # Convert Decimal amount to float for comparisons
        amount_float = float(amount)
        amount_risk = 40 if amount_float > 3000 else (20 if amount_float > 1000 else 0)
        fraud_score = (risk_score * 100) + amount_risk + location_risk
        
        # Determine if transaction is flagged as fraud
        is_flagged_fraud = fraud_score > 0  # Using your threshold
        is_actual_fraud = transaction['IsActualFraud']
        
        # Update counters
        if is_flagged_fraud and is_actual_fraud:
            true_positives += 1
        elif is_flagged_fraud and not is_actual_fraud:
            false_positives += 1
        elif not is_flagged_fraud and not is_actual_fraud:
            true_negatives += 1
        elif not is_flagged_fraud and is_actual_fraud:
            false_negatives += 1
    
    # Calculate performance metrics
    total = len(test_data)
    accuracy = (true_positives + true_negatives) / total if total > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "algorithm": "rule_based",
        "accuracy": accuracy * 100,
        "precision": precision * 100,
        "recall": recall * 100,
        "f1_score": f1_score * 100,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "true_negatives": true_negatives,
        "false_negatives": false_negatives,
        "timestamp": datetime.datetime.now().isoformat()
    }

def store_test_results(results):
    """Store test results in DynamoDB"""
    try:
        TEST_RESULTS_TABLE.put_item(Item={
            'TestID': f"test_{uuid.uuid4().hex[:8]}",
            'Timestamp': results['timestamp'],
            'Algorithm': results['algorithm'],
            'Accuracy': Decimal(str(results['accuracy'])),
            'Precision': Decimal(str(results['precision'])),
            'Recall': Decimal(str(results['recall'])),
            'F1Score': Decimal(str(results['f1_score'])),
            'TruePositives': results['true_positives'],
            'FalsePositives': results['false_positives'],
            'TrueNegatives': results['true_negatives'],
            'FalseNegatives': results['false_negatives']
        })
        print("Test results stored in DynamoDB")
    except Exception as e:
        print(f"Error storing test results: {e}")
a
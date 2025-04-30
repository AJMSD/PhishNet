# PhishNet — Real-Time Fraud Detection System

## Repository  
[PhishNet](https://github.com/AJMSD/PhishNet)

## Set-Up Instructions

1. **Provision Resources on AWS**:
   - Create IAM Roles, Lambdas, DynamoDB tables (`Transactions`, `Users`, `UserFraudTransactionsMap`), and an SQS queue.
   - Set up API Gateway with a POST route for `/sms-response`.

2. **Configure Lambda Functions**:
   - Attach SQS trigger to `FraudDetectionLambda`.
   - Add EventBridge rule to invoke `ProcessTransactionLambda` periodically.
   - For `HandleUserResponseLambda`, connect it with API Gateway and provide Twilio credentials as environment variables.
   - Package and upload the Twilio Python library and any ML dependencies (e.g., `joblib`) as Lambda Layers especially for `FraudDetectionLambda`.

3. **Twilio Configuration**:
   - Set up a Twilio number for sending/receiving SMS.
   - Enable Twilio to POST responses to your API Gateway URL.
   - Ensure phone numbers used in testing are registered with your Twilio account (due to free-tier limits).

4. **Initialize Data**:
   - Use `PhishNetAddUser` to create five test users (phone-number-based).

---

## How It Works

1. **ProcessTransactionLambda**:
   - Simulates a fake transaction from a random user in the `Users` table.
   - Stores the transaction in DynamoDB and sends the transaction ID to SQS.

2. **FraudDetectionLambda**:
   - Triggered by SQS. Uses the transaction ID to fetch details.
   - Calculates a risk score using merchant, location, and amount heuristics.
   - Travel mode and user habits are factored in to reduce false positives.
   - If flagged as fraud, sends SMS using Twilio and stores a mapping in `UserFraudTransactionsMap`.

3. **HandleUserResponseLambda**:
   - Triggered when users respond to the fraud alert via SMS.
   - Can enable/disable travel mode via specific commands (e.g., `"travel - Tokyo"`, `"stop travel"`).
   - If replying to a fraud alert (`YES`/`NO`), updates the transaction and deletes the mapping.

4. **FraudTesterLambda (Optional)**:
   - A testing utility that allows you to run sample fraud transactions and validate your detection logic.

---

## What Works & What Doesn’t

- **What Works:**
  - Real-time fraud detection with rule-based scoring.
  - SMS-based fraud alert and response system.
  - Travel mode implementation with location-based sensitivity.
  - Mapping table (`UserFraudTransactionsMap`) tracks open fraud investigations.
  - User-triggered travel mode toggles via text messages.

- **What Doesn’t (Yet):**
  - The machine learning fraud detection logic exists in the code, but it’s not functional — the models and encoders (`.pkl` files) are referenced but not uploaded to Lambda.
  - `joblib` is required for loading models, but not currently packaged via Lambda Layers.
  - Twilio is restricted to verified numbers on the free tier.
  - UserID must be a phone number since DynamoDB cannot enforce uniqueness on non-key attributes.

---

## What Would We Work on Next

- Integrate and test the ML-based detection by:
  - Training models on realistic datasets.
  - Uploading them using Lambda Layers.
- Migrate user data to an RDS/SQL database for better integrity and relational access. 
  - This would allow enforcing unique constraints on fields like phone numbers without making them the primary key.
- Use NLP to parse user responses more flexibly (e.g., typos, slang).
- Add fuzzy matching for travel mode locations (e.g., "Tokoyo" still maps to "Tokyo").
- Build a lightweight frontend or dashboard where users can review alerts, toggle travel mode, and view history and also get more details on the transactions to verify if it is fraud or not.
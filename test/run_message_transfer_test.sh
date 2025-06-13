#!/bin/bash

# Script to test end-to-end message transfer through the connector
# Sends 100 messages from network1 to network3 and verifies receipt

# Default number of messages to send
NUM_MESSAGES=100
if [ ! -z "$1" ]; then
  NUM_MESSAGES=$1
fi

echo "================================================="
echo "Starting Message Transfer Test with $NUM_MESSAGES messages"
echo "================================================="

# Check if docker compose is running
if ! docker compose ps | grep -q "connector"; then
    echo "Error: Docker services not running. Please start with docker compose up -d"
    exit 1
fi

# Ensure schema directory exists
if [ ! -d "./backend/avro" ]; then
    echo "Creating Avro schema directory..."
    mkdir -p ./backend/avro
fi

# Check if schema exists, if not, create a sample one
if [ ! -f "./backend/avro/schema.avsc" ]; then
    echo "Creating sample Avro schema..."
    cat > ./backend/avro/schema.avsc << EOF
{
    "namespace": "com.example",
    "type": "record",
    "name": "Event",
    "fields": [
        {"name": "eventId", "type": "string"},
        {"name": "eventType", "type": "string"},
        {"name": "timestamp", "type": "long"},
        {
            "name": "payload", 
            "type": {
                "type": "record",
                "name": "Payload",
                "fields": [
                    {"name": "messageNumber", "type": "int"},
                    {"name": "testRunId", "type": "string"},
                    {"name": "content", "type": "string"}
                ]
            }
        }
    ]
}
EOF
fi

# Make test scripts executable
chmod +x ./test/message_transfer_test.py
chmod +x ./test/verify_message_transfer.py

echo "Step 1: Sending $NUM_MESSAGES messages to source Kafka..."
docker compose exec -T source-test python /app/message_transfer_test.py $NUM_MESSAGES || { echo "Error running message transfer test"; exit 1; }

echo "Step 2: Waiting for connector to process messages (15 seconds)..."
sleep 15

echo "Step 3: Verifying messages received at target Kafka..."
docker compose exec -T target-test python /app/verify_message_transfer.py $NUM_MESSAGES || { echo "Error running verification script"; exit 1; }

echo "================================================="
echo "Message transfer test complete!"
echo "================================================="

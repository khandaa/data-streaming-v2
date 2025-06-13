#!/usr/bin/env python
import json
import time
import sys
from confluent_kafka import Consumer, KafkaError
import io
from fastavro import schemaless_reader

# Configuration
TARGET_TOPIC = 'target-topic'
TIMEOUT_SECONDS = 60
BOOTSTRAP_SERVER = 'target-kafka:9094'
GROUP_ID = 'message-transfer-test-consumer'
EXPECTED_MESSAGES = 100
if len(sys.argv) > 1:
    EXPECTED_MESSAGES = int(sys.argv[1])

# Load Avro schema
schema_paths = ['./backend/avro/schema.avsc', '/app/backend/avro/schema.avsc', '/avro/schema.avsc']
schema = None

for path in schema_paths:
    try:
        with open(path, 'r') as f:
            schema = json.load(f)
            print(f"Loaded schema from {path}")
            break
    except FileNotFoundError:
        continue

if schema is None:
    raise FileNotFoundError(f"Schema file not found in any of these paths: {schema_paths}")

# Configure the Kafka consumer
consumer_config = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'group.id': GROUP_ID,
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}

def avro_deserialize(binary_data, schema):
    """Deserialize Avro binary data"""
    reader = io.BytesIO(binary_data)
    return schemaless_reader(reader, schema)

def main():
    """Main function to verify messages on the target topic"""
    consumer = Consumer(consumer_config)
    consumer.subscribe([TARGET_TOPIC])
    
    print(f"Starting to consume messages from {TARGET_TOPIC}")
    print(f"Expecting {EXPECTED_MESSAGES} messages")
    print(f"Will time out after {TIMEOUT_SECONDS} seconds")
    
    received_messages = {}
    start_time = time.time()
    
    try:
        while len(received_messages) < EXPECTED_MESSAGES:
            if time.time() - start_time > TIMEOUT_SECONDS:
                print(f"Timed out after {TIMEOUT_SECONDS} seconds")
                print(f"Received {len(received_messages)} out of {EXPECTED_MESSAGES} expected messages")
                break
                
            msg = consumer.poll(1.0)
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"Reached end of partition")
                else:
                    print(f"Error: {msg.error()}")
            else:
                try:
                    # Deserialize the message
                    event = avro_deserialize(msg.value(), schema)
                    msg_id = event['eventId']
                    
                    # Only add each unique message once
                    if msg_id not in received_messages:
                        received_messages[msg_id] = event
                        print(f"Received message {len(received_messages)}/{EXPECTED_MESSAGES}: Event ID {msg_id}")
                    
                except Exception as e:
                    print(f"Error processing message: {e}")
        
        # Print summary
        print("\nMessage Transfer Test Results")
        print("============================")
        print(f"Expected messages: {EXPECTED_MESSAGES}")
        print(f"Received messages: {len(received_messages)}")
        
        if len(received_messages) == EXPECTED_MESSAGES:
            print("SUCCESS: All expected messages received!")
        else:
            print(f"WARNING: Only received {len(received_messages)} out of {EXPECTED_MESSAGES} expected messages")
            
    except KeyboardInterrupt:
        print("Consumer interrupted.")
    finally:
        consumer.close()
        print("Consumer closed.")

if __name__ == "__main__":
    main()

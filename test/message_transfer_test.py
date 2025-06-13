#!/usr/bin/env python
import json
import time
import uuid
import sys
from confluent_kafka import Producer
import io
from fastavro import schemaless_writer

# Configuration
SOURCE_TOPIC = 'source-topic'
NUM_MESSAGES = 100
if len(sys.argv) > 1:
    NUM_MESSAGES = int(sys.argv[1])
BOOTSTRAP_SERVER = 'source-kafka:9092'

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

# Configure the Kafka producer
producer_config = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'client.id': 'message-transfer-test'
}

def delivery_callback(err, msg):
    """Callback invoked when message delivery succeeds or fails"""
    if err:
        print(f'ERROR: Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

def avro_serialize(record, schema):
    """Serialize using Avro"""
    buf = io.BytesIO()
    schemaless_writer(buf, schema, record)
    return buf.getvalue()

def create_test_message(msg_id):
    """Create a test message with a unique ID"""
    timestamp = int(time.time() * 1000)
    return {
        'eventId': str(msg_id),
        'eventType': 'TEST_MESSAGE',
        'timestamp': timestamp,
        'payload': {
            'messageNumber': msg_id,
            'testRunId': str(uuid.uuid4()),
            'content': f'Test message {msg_id} of {NUM_MESSAGES}'
        }
    }

def main():
    """Main function to send test messages to source topic"""
    producer = Producer(producer_config)
    
    print(f"Starting to produce {NUM_MESSAGES} messages to {SOURCE_TOPIC}")
    
    # Send messages
    for i in range(1, NUM_MESSAGES + 1):
        event = create_test_message(i)
        
        # Serialize the event
        avro_data = avro_serialize(event, schema)
        
        # Send to source topic
        producer.produce(SOURCE_TOPIC, value=avro_data, callback=delivery_callback)
        
        # Flush every 10 messages
        if i % 10 == 0:
            producer.flush()
            print(f"Sent {i} messages...")
    
    # Final flush
    producer.flush()
    print(f"Successfully produced {NUM_MESSAGES} messages to {SOURCE_TOPIC}")

if __name__ == "__main__":
    main()

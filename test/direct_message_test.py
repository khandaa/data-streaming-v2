#!/usr/bin/env python
"""
End-to-end message transfer test across isolated network topology
This script handles both producing messages to source Kafka and consuming from target Kafka
to verify complete message transfer through the connector.
"""

import json
import time
import uuid
import sys
import threading
import argparse
from collections import defaultdict
from confluent_kafka import Producer, Consumer, KafkaError
import io
import os
from fastavro import schemaless_writer, schemaless_reader

# Default configuration
NUM_MESSAGES = 100
SOURCE_BOOTSTRAP_SERVER = 'localhost:9092'
TARGET_BOOTSTRAP_SERVER = 'localhost:9094'
SOURCE_TOPIC = 'source-topic'
TARGET_TOPIC = 'target-topic'
TIMEOUT_SECONDS = 60

# Stats and locks
received_messages = defaultdict(dict)
messages_lock = threading.Lock()
running = True

def load_schema():
    """Load Avro schema from file"""
    schema_path = './backend/avro/schema.avsc'
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading schema: {e}")
        sys.exit(1)

def delivery_callback(err, msg):
    """Callback for producer delivery reports"""
    if err:
        print(f'ERROR: Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

def avro_serialize(record, schema):
    """Serialize using Avro"""
    buf = io.BytesIO()
    schemaless_writer(buf, schema, record)
    return buf.getvalue()

def avro_deserialize(binary_data, schema):
    """Deserialize Avro binary data"""
    reader = io.BytesIO(binary_data)
    return schemaless_reader(reader, schema)

def create_test_message(msg_id, num_messages):
    """Create a test message with a unique ID"""
    timestamp = int(time.time() * 1000)
    test_run_id = str(uuid.uuid4())
    return {
        'eventId': str(msg_id),
        'eventType': 'TEST_MESSAGE',
        'timestamp': timestamp,
        'payload': {
            'messageNumber': msg_id,
            'testRunId': test_run_id,
            'content': f'Test message {msg_id} of {num_messages}'
        }
    }

def produce_messages(bootstrap_servers, topic, num_messages, schema):
    """Produce test messages to source Kafka"""
    print(f"Producing {num_messages} messages to {topic} via {bootstrap_servers}")
    
    producer_config = {
        'bootstrap.servers': bootstrap_servers,
        'client.id': 'message-transfer-test'
    }
    
    producer = Producer(producer_config)
    
    for i in range(1, num_messages + 1):
        event = create_test_message(i, num_messages)
        # Serialize the event
        avro_data = avro_serialize(event, schema)
        
        # Send to source topic
        producer.produce(topic, value=avro_data, callback=delivery_callback)
        
        # Flush every 10 messages
        if i % 10 == 0:
            producer.flush()
            print(f"Sent {i} messages...")
    
    # Final flush
    producer.flush()
    print(f"Successfully produced {num_messages} messages to {topic}")

def consume_messages(bootstrap_servers, topic, expected_messages, schema, timeout_seconds):
    """Consume and verify messages from target Kafka"""
    global running, received_messages
    
    print(f"Starting to consume messages from {topic} via {bootstrap_servers}")
    print(f"Expecting {expected_messages} messages")
    print(f"Will time out after {timeout_seconds} seconds")
    
    consumer_config = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': f'message-transfer-test-{int(time.time())}',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True
    }
    
    consumer = Consumer(consumer_config)
    consumer.subscribe([topic])
    
    start_time = time.time()
    
    try:
        while running and len(received_messages) < expected_messages:
            if time.time() - start_time > timeout_seconds:
                print(f"Timed out after {timeout_seconds} seconds")
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
                    with messages_lock:
                        if msg_id not in received_messages:
                            received_messages[msg_id] = event
                            print(f"Received message {len(received_messages)}/{expected_messages}: Event ID {msg_id}")
                        
                        if len(received_messages) >= expected_messages:
                            print("\nAll expected messages received!")
                            break
                    
                except Exception as e:
                    print(f"Error processing message: {e}")
    
    finally:
        consumer.close()
        print("Consumer closed.")

def run_test(args):
    """Run the end-to-end test"""
    schema = load_schema()
    
    # Start consumer thread
    consumer_thread = threading.Thread(
        target=consume_messages,
        args=(args.target_bootstrap, args.target_topic, args.num_messages, schema, args.timeout)
    )
    consumer_thread.daemon = True
    consumer_thread.start()
    
    # Wait a moment for consumer to start
    time.sleep(2)
    
    # Produce messages
    produce_messages(args.source_bootstrap, args.source_topic, args.num_messages, schema)
    
    # Wait for consumer to finish or timeout
    print(f"\nWaiting up to {args.timeout} seconds for messages to be transferred...")
    start_wait = time.time()
    while consumer_thread.is_alive() and time.time() - start_wait < args.timeout:
        time.sleep(1)
        with messages_lock:
            if len(received_messages) >= args.num_messages:
                break
    
    # Stop consumer and print results
    global running
    running = False
    consumer_thread.join(5)
    
    print("\n\nMessage Transfer Test Results")
    print("============================")
    print(f"Expected messages: {args.num_messages}")
    print(f"Received messages: {len(received_messages)}")
    
    if len(received_messages) == args.num_messages:
        print("SUCCESS: All expected messages received!")
        return True
    else:
        print(f"WARNING: Only received {len(received_messages)} out of {args.num_messages} expected messages")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run end-to-end Kafka message transfer test')
    parser.add_argument('--num-messages', '-n', type=int, default=NUM_MESSAGES,
                        help=f'Number of messages to send (default: {NUM_MESSAGES})')
    parser.add_argument('--source-bootstrap', '-sb', type=str, default=SOURCE_BOOTSTRAP_SERVER,
                        help=f'Source Kafka bootstrap server (default: {SOURCE_BOOTSTRAP_SERVER})')
    parser.add_argument('--target-bootstrap', '-tb', type=str, default=TARGET_BOOTSTRAP_SERVER,
                        help=f'Target Kafka bootstrap server (default: {TARGET_BOOTSTRAP_SERVER})')
    parser.add_argument('--source-topic', '-st', type=str, default=SOURCE_TOPIC,
                        help=f'Source Kafka topic (default: {SOURCE_TOPIC})')
    parser.add_argument('--target-topic', '-tt', type=str, default=TARGET_TOPIC,
                        help=f'Target Kafka topic (default: {TARGET_TOPIC})')
    parser.add_argument('--timeout', '-t', type=int, default=TIMEOUT_SECONDS,
                        help=f'Timeout in seconds (default: {TIMEOUT_SECONDS})')
    
    args = parser.parse_args()
    
    success = run_test(args)
    sys.exit(0 if success else 1)

#!/usr/bin/env python
import json
import time
from confluent_kafka import Consumer, KafkaError
import io
from fastavro import schemaless_reader

# Configuration
TOPIC = 'target-topic'
BOOTSTRAP_SERVER = 'localhost:29092'
GROUP_ID = 'test-consumer-group-fixed'  # Using a different group ID

# Load Avro schema
with open('./backend/avro/schema.avsc', 'r') as f:
    schema = json.load(f)

# Configure the Kafka consumer with more explicit settings
consumer_config = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'group.id': GROUP_ID,
    'auto.offset.reset': 'earliest',  # Always start from the beginning
    'session.timeout.ms': 6000,
    'enable.auto.commit': True,
    'auto.commit.interval.ms': 500
}
consumer = Consumer(consumer_config)

def avro_deserialize(binary_data, schema):
    """Deserialize Avro binary data"""
    reader = io.BytesIO(binary_data)
    return schemaless_reader(reader, schema)

def main():
    """Main function to consume messages"""
    consumer.subscribe([TOPIC])
    print(f"Starting consumer for topic: {TOPIC}")
    print(f"Press Ctrl+C to exit\n")
    
    # First get metadata to verify connection
    try:
        md = consumer.list_topics(timeout=10)
        print(f"Connected to Kafka cluster: {md.orig_broker_name}")
        print(f"Available topics: {list(md.topics.keys())}")
        
        if TOPIC not in md.topics:
            print(f"WARNING: Topic '{TOPIC}' not found in available topics")
    except Exception as e:
        print(f"Error getting metadata: {e}")
    
    try:
        message_count = 0
        # Set a timeout for how long to run
        end_time = time.time() + 30  # Run for 30 seconds
        
        while time.time() < end_time:
            msg = consumer.poll(1.0)
            
            if msg is None:
                print("Waiting for messages...")
                time.sleep(1)
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"Reached end of partition {msg.partition()}")
                else:
                    print(f"Error: {msg.error()}")
            else:
                try:
                    # Deserialize the message
                    event = avro_deserialize(msg.value(), schema)
                    message_count += 1
                    
                    print(f"\nReceived message {message_count}:")
                    print(f"  Event ID: {event['eventId']}")
                    print(f"  Timestamp: {event['timestamp']}")
                    print(f"  Payload: {event['payload']}")
                    print("----------------------------")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
        print(f"\nConsumer finished after reading {message_count} messages")
            
    except KeyboardInterrupt:
        print("Consumer interrupted.")
    finally:
        consumer.close()
        print("Consumer closed.")

if __name__ == "__main__":
    main()

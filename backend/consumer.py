#!/usr/bin/env python
import json
import time
from confluent_kafka import Consumer, KafkaError
import io
from fastavro import schemaless_reader

# Configuration
TOPIC = 'target-topic'
BOOTSTRAP_SERVER = 'localhost:29092'
GROUP_ID = 'test-consumer-group'

# Load Avro schema
with open('./backend/avro/schema.avsc', 'r') as f:
    schema = json.load(f)

# Configure the Kafka consumer
consumer_config = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'group.id': GROUP_ID,
    'auto.offset.reset': 'earliest'
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
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    print(f"Reached end of partition {msg.partition()}")
                else:
                    print(f"Error: {msg.error()}")
            else:
                try:
                    # Deserialize the message
                    event = avro_deserialize(msg.value(), schema)
                    print(f"Received event: {event}")
                    print(f"  Event ID: {event['eventId']}")
                    print(f"  Timestamp: {event['timestamp']}")
                    print(f"  Payload: {event['payload']}")
                    print("----------------------------")
                except Exception as e:
                    print(f"Error processing message: {e}")
            
    except KeyboardInterrupt:
        print("Consumer interrupted.")
    finally:
        consumer.close()
        print("Consumer closed.")

if __name__ == "__main__":
    main()

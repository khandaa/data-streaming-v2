#!/usr/bin/env python
import time
import uuid
import json
from confluent_kafka import Producer
import io
from fastavro import schemaless_writer

# Configuration
TOPIC = 'source-topic'
BOOTSTRAP_SERVER = 'localhost:29092'

# Load Avro schema
with open('./backend/avro/schema.avsc', 'r') as f:
    schema = json.load(f)

# Configure the Kafka producer
producer_config = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'client.id': 'test-producer'
}
producer = Producer(producer_config)

def delivery_callback(err, msg):
    """Callback invoked when message delivery succeeds or fails"""
    if err:
        print(f'ERROR: Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

def generate_event():
    """Generate a sample event with random ID"""
    return {
        'eventId': str(uuid.uuid4()),
        'timestamp': int(time.time() * 1000),
        'payload': f'Test message created at {time.strftime("%Y-%m-%d %H:%M:%S")}'
    }

def avro_serialize(record, schema):
    """Serialize using Avro"""
    buf = io.BytesIO()
    schemaless_writer(buf, schema, record)
    return buf.getvalue()

def produce_message():
    """Produce a message to the topic"""
    event = generate_event()
    print(f"Producing event: {event}")
    
    # Serialize the event using Avro
    avro_data = avro_serialize(event, schema)
    
    # Send to Kafka
    producer.produce(TOPIC, value=avro_data, callback=delivery_callback)
    producer.poll(0)

def main():
    """Main function to produce messages"""
    print(f"Starting producer for topic: {TOPIC}")
    try:
        # Produce 10 messages
        for i in range(10):
            print(f"\nProducing message {i+1}/10")
            produce_message()
            time.sleep(1)
            
        # Wait for any outstanding messages to be delivered and delivery reports received
        print("\nFlushing pending messages...")
        producer.flush()
        print("All messages delivered!")
            
    except KeyboardInterrupt:
        print("Producer interrupted.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

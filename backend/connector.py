#!/usr/bin/env python
import json
import time
from confluent_kafka import Consumer, Producer, KafkaError
import io
from fastavro import schemaless_reader, schemaless_writer

# Configuration
SOURCE_TOPIC = 'source-topic'
TARGET_TOPIC = 'target-topic'
BOOTSTRAP_SERVER = 'localhost:29092'
GROUP_ID = 'connector-group'

# Load Avro schema
with open('./backend/avro/schema.avsc', 'r') as f:
    schema = json.load(f)

# Configure the Kafka consumer
consumer_config = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'group.id': GROUP_ID,
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
}
consumer = Consumer(consumer_config)

# Configure the Kafka producer
producer_config = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'client.id': 'connector-producer'
}
producer = Producer(producer_config)

def delivery_callback(err, msg):
    """Callback invoked when message delivery succeeds or fails"""
    if err:
        print(f'ERROR: Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

def avro_deserialize(binary_data, schema):
    """Deserialize Avro binary data"""
    reader = io.BytesIO(binary_data)
    return schemaless_reader(reader, schema)

def avro_serialize(record, schema):
    """Serialize using Avro"""
    buf = io.BytesIO()
    schemaless_writer(buf, schema, record)
    return buf.getvalue()

def main():
    """Main function to connect source topic to target topic"""
    consumer.subscribe([SOURCE_TOPIC])
    print(f"Starting connector from {SOURCE_TOPIC} to {TARGET_TOPIC}")
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
                    print(f"Received event from source topic: {event['eventId']}")
                    
                    # Serialize the event again
                    avro_data = avro_serialize(event, schema)
                    
                    # Send to target topic
                    producer.produce(TARGET_TOPIC, value=avro_data, callback=delivery_callback)
                    producer.poll(0)
                    
                    # Commit the offset manually
                    consumer.commit(msg)
                    
                except Exception as e:
                    print(f"Error processing message: {e}")
            
    except KeyboardInterrupt:
        print("Connector interrupted.")
    finally:
        consumer.close()
        print("Connector closed.")

if __name__ == "__main__":
    main()

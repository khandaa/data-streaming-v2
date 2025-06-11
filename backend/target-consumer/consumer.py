import os
import time
from confluent_kafka import Consumer
from fastavro import schemaless_reader
import io
import json

# Load environment variables
BROKER = os.getenv('KAFKA_TARGET_BROKER', 'target-kafka:9095')
TOPIC = os.getenv('KAFKA_TARGET_TOPIC', 'target-topic')
SCHEMA_PATH = os.getenv('SCHEMA_PATH', '/avro/schema.avsc')

# TLS configs
SSL_CONFIG = {
    'security.protocol': 'SSL',
    'ssl.keystore.location': os.getenv('KAFKA_SSL_KEYSTORE_LOCATION'),
    'ssl.keystore.password': os.getenv('KAFKA_SSL_KEYSTORE_PASSWORD'),
    'ssl.key.password': os.getenv('KAFKA_SSL_KEY_PASSWORD'),
    'ssl.truststore.location': os.getenv('KAFKA_SSL_TRUSTSTORE_LOCATION'),
    'ssl.truststore.password': os.getenv('KAFKA_SSL_TRUSTSTORE_PASSWORD'),
}

conf = {
    'bootstrap.servers': BROKER,
    'group.id': 'target-consumer-group',
    'auto.offset.reset': 'earliest',
    **SSL_CONFIG
}
consumer = Consumer(conf)
consumer.subscribe([TOPIC])

# Load Avro schema
with open(SCHEMA_PATH, 'r') as f:
    schema = json.load(f)

def avro_deserialize(binary_data, schema):
    reader = io.BytesIO(binary_data)
    return schemaless_reader(reader, schema)

if __name__ == "__main__":
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            
            event = avro_deserialize(msg.value(), schema)
            print(f"Received event: {event}")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
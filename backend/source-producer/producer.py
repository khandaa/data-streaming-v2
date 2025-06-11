import os
import time
import uuid
from confluent_kafka import Producer
from fastavro import schemaless_writer
import io
import json

# Load environment variables
BROKER = os.getenv('KAFKA_SOURCE_BROKER', 'source-kafka:9093')
TOPIC = os.getenv('KAFKA_SOURCE_TOPIC', 'source-topic')
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

conf = {'bootstrap.servers': BROKER, **SSL_CONFIG}
producer = Producer(conf)

# Load Avro schema
with open(SCHEMA_PATH, 'r') as f:
    schema = json.load(f)

def generate_event():
    return {
        'eventId': str(uuid.uuid4()),
        'timestamp': int(time.time() * 1000),
        'payload': 'sample payload'
    }

def avro_serialize(record, schema):
    buf = io.BytesIO()
    schemaless_writer(buf, schema, record)
    return buf.getvalue()

def delivery_report(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

if __name__ == "__main__":
    for _ in range(10):
        event = generate_event()
        avro_bytes = avro_serialize(event, schema)
        producer.produce(TOPIC, value=avro_bytes, callback=delivery_report)
        producer.poll(0)
        time.sleep(1)
    producer.flush()

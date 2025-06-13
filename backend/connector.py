#!/usr/bin/env python
import json
import time
import os
import logging
from confluent_kafka import Consumer, Producer, KafkaError
import io
from fastavro import schemaless_reader, schemaless_writer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class KafkaConnector:
    def __init__(self):
        # Configuration
        self.source_topic = os.environ.get('SOURCE_TOPIC', 'source-topic')
        self.target_topic = os.environ.get('TARGET_TOPIC', 'target-topic')
        self.source_bootstrap_server = os.environ.get('SOURCE_BOOTSTRAP_SERVER', 'source-kafka:9092')
        self.target_bootstrap_server = os.environ.get('TARGET_BOOTSTRAP_SERVER', 'target-kafka:9094')
        self.group_id = os.environ.get('GROUP_ID', 'connector-group')
        
        # For plaintext connections, used during development
        self.use_plaintext = os.environ.get('USE_PLAINTEXT', 'true').lower() == 'true'
        
        # Load schema
        try:
            schema_paths = ['/avro/schema.avsc', './backend/avro/schema.avsc', '/etc/kafka/avro/schema.avsc']
            for path in schema_paths:
                try:
                    with open(path, 'r') as f:
                        self.schema = json.load(f)
                        logger.info(f"Loaded schema from {path}")
                        break
                except FileNotFoundError:
                    continue
            if not hasattr(self, 'schema'):
                raise FileNotFoundError(f"Schema file not found in any of these paths: {schema_paths}")
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            raise
            
        # Set up consumer and producer
        self.setup_consumer()
        self.setup_producer()
    
    def setup_consumer(self):
        """Configure and create Kafka consumer"""
        # Consumer configuration
        consumer_conf = {
            'bootstrap.servers': self.source_bootstrap_server,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        
        # Add SSL/TLS config if not using plaintext
        if not self.use_plaintext:
            consumer_conf.update({
                'security.protocol': 'SSL',
                'ssl.ca.location': '/etc/kafka/secrets/source-ca.pem',
                'ssl.certificate.location': '/etc/kafka/secrets/source-client.pem',
                'ssl.key.location': '/etc/kafka/secrets/source-client.key',
                'ssl.key.password': 'keypass'
            })
            
        self.consumer = Consumer(consumer_conf)
        logger.info(f"Consumer configured to connect to {self.source_bootstrap_server}")
    
    def setup_producer(self):
        """Configure and create Kafka producer"""
        # Producer configuration
        producer_conf = {
            'bootstrap.servers': self.target_bootstrap_server,
            'client.id': 'connector-producer'
        }
        
        # Add SSL/TLS config if not using plaintext
        if not self.use_plaintext:
            producer_conf.update({
                'security.protocol': 'SSL',
                'ssl.ca.location': '/etc/kafka/secrets/target-ca.pem',
                'ssl.certificate.location': '/etc/kafka/secrets/target-client.pem',
                'ssl.key.location': '/etc/kafka/secrets/target-client.key',
                'ssl.key.password': 'keypass'
            })
            
        self.producer = Producer(producer_conf)
        logger.info(f"Producer configured to connect to {self.target_bootstrap_server}")

    def delivery_callback(self, err, msg):
        """Callback invoked when message delivery succeeds or fails"""
        if err:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

    def avro_deserialize(self, binary_data):
        """Deserialize Avro binary data"""
        reader = io.BytesIO(binary_data)
        return schemaless_reader(reader, self.schema)

    def avro_serialize(self, record):
        """Serialize using Avro"""
        buf = io.BytesIO()
        schemaless_writer(buf, self.schema, record)
        return buf.getvalue()

    def process_messages(self):
        """Main processing loop to connect source topic to target topic"""
        # Subscribe to source topic
        self.consumer.subscribe([self.source_topic])
        logger.info(f"Starting connector from {self.source_topic} to {self.target_topic}")
        
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        logger.info(f"Reached end of partition {msg.partition()}")
                    else:
                        logger.error(f"Error: {msg.error()}")
                else:
                    try:
                        # Deserialize the message
                        event = self.avro_deserialize(msg.value())
                        logger.info(f"Received event from source topic: {event['eventId']}")
                        
                        # Serialize the event again
                        avro_data = self.avro_serialize(event)
                        
                        # Send to target topic
                        self.producer.produce(
                            self.target_topic, 
                            value=avro_data, 
                            callback=lambda err, msg: self.delivery_callback(err, msg)
                        )
                        self.producer.poll(0)
                        
                        # Commit the offset manually
                        self.consumer.commit(msg)
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                
        except KeyboardInterrupt:
            logger.info("Connector interrupted")
        finally:
            self.consumer.close()
            logger.info("Connector closed")

def main():
    """Main entry point"""
    try:
        logger.info("Starting Kafka connector...")
        connector = KafkaConnector()
        connector.process_messages()
    except Exception as e:
        logger.error(f"Failed to start connector: {e}")
        raise

if __name__ == "__main__":
    main()

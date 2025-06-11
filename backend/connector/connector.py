import os
import time
import logging
from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
import io
import json
from fastavro import schemaless_writer, schemaless_reader

# Configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
SOURCE_BROKER = os.getenv('KAFKA_SOURCE_BROKER', 'source-kafka:9093')
TARGET_BROKER = os.getenv('KAFKA_TARGET_BROKER', 'target-kafka:9095')
SOURCE_TOPIC = os.getenv('KAFKA_SOURCE_TOPIC', 'source-topic')
TARGET_TOPIC = os.getenv('KAFKA_TARGET_TOPIC', 'target-topic')
CONSUMER_GROUP = os.getenv('CONSUMER_GROUP', 'connector-group')
SCHEMA_PATH = os.getenv('SCHEMA_PATH', '/avro/schema.avsc')

# TLS configs for source Kafka
SOURCE_SSL_CONFIG = {
    'security.protocol': 'SSL',
    'ssl.keystore.location': os.getenv('KAFKA_SSL_KEYSTORE_LOCATION'),
    'ssl.keystore.password': os.getenv('KAFKA_SSL_KEYSTORE_PASSWORD'),
    'ssl.key.password': os.getenv('KAFKA_SSL_KEY_PASSWORD'),
    'ssl.truststore.location': os.getenv('KAFKA_SSL_TRUSTSTORE_LOCATION'),
    'ssl.truststore.password': os.getenv('KAFKA_SSL_TRUSTSTORE_PASSWORD'),
}

# TLS configs for target Kafka
TARGET_SSL_CONFIG = {
    'security.protocol': 'SSL',
    'ssl.keystore.location': os.getenv('KAFKA_SSL_KEYSTORE_LOCATION'),
    'ssl.keystore.password': os.getenv('KAFKA_SSL_KEYSTORE_PASSWORD'),
    'ssl.key.password': os.getenv('KAFKA_SSL_KEY_PASSWORD'),
    'ssl.truststore.location': os.getenv('KAFKA_SSL_TRUSTSTORE_LOCATION'),
    'ssl.truststore.password': os.getenv('KAFKA_SSL_TRUSTSTORE_PASSWORD'),
}

class KafkaConnector:
    def __init__(self):
        self.running = True
        self.load_schema()
        self.setup_consumer()
        self.setup_producer()
        self.setup_target_topic()

    def load_schema(self):
        try:
            with open(SCHEMA_PATH, 'r') as f:
                self.schema = json.load(f)
                logger.info(f"Loaded schema from {SCHEMA_PATH}")
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            raise

    def setup_consumer(self):
        consumer_conf = {
            'bootstrap.servers': SOURCE_BROKER,
            'group.id': CONSUMER_GROUP,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
            **SOURCE_SSL_CONFIG
        }
        self.consumer = Consumer(consumer_conf)
        self.consumer.subscribe([SOURCE_TOPIC])
        logger.info(f"Consumer subscribed to {SOURCE_TOPIC}")

    def setup_producer(self):
        # For exactly-once semantics
        producer_conf = {
            'bootstrap.servers': TARGET_BROKER,
            'transactional.id': 'connector-transaction',
            **TARGET_SSL_CONFIG
        }
        self.producer = Producer(producer_conf)
        self.producer.init_transactions()
        logger.info("Producer initialized with transactional capabilities")

    def setup_target_topic(self):
        # Make sure target topic exists before we start
        admin_conf = {
            'bootstrap.servers': TARGET_BROKER,
            **TARGET_SSL_CONFIG
        }
        admin = AdminClient(admin_conf)
        
        try:
            # Create topic if it doesn't exist
            topics = [NewTopic(TARGET_TOPIC, num_partitions=3, replication_factor=1)]
            admin.create_topics(topics)
            logger.info(f"Target topic {TARGET_TOPIC} created")
        except KafkaException as e:
            if "already exists" in str(e):
                logger.info(f"Topic {TARGET_TOPIC} already exists")
            else:
                logger.warning(f"Failed to create topic: {e}")

    def avro_deserialize(self, binary_data):
        reader = io.BytesIO(binary_data)
        return schemaless_reader(reader, self.schema)

    def avro_serialize(self, record):
        buf = io.BytesIO()
        schemaless_writer(buf, self.schema, record)
        return buf.getvalue()

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def start(self):
        try:
            while self.running:
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition {msg.partition()}")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue
                
                try:
                    # Deserialize the message from source
                    event = self.avro_deserialize(msg.value())
                    logger.info(f"Processing event ID: {event.get('eventId')}")
                    
                    # Begin transaction for exactly-once semantics
                    self.producer.begin_transaction()
                    
                    # Serialize and send the event to target
                    serialized_event = self.avro_serialize(event)
                    self.producer.produce(
                        TARGET_TOPIC,
                        key=msg.key(),
                        value=serialized_event,
                        callback=self.delivery_report
                    )
                    
                    # Commit the offset as part of the transaction for exactly-once semantics
                    self.producer.send_offsets_to_transaction(
                        self.consumer.position([msg.partition()]),
                        self.consumer.consumer_group_metadata()
                    )
                    
                    # Commit the transaction
                    self.producer.commit_transaction()
                    logger.info(f"Transaction committed for event ID: {event.get('eventId')}")
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    self.producer.abort_transaction()
                    
        except KeyboardInterrupt:
            logger.info("Connector shutting down...")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            self.cleanup()

    def stop(self):
        self.running = False

    def cleanup(self):
        if self.consumer:
            self.consumer.close()
        logger.info("Connector shutdown complete")

if __name__ == "__main__":
    logger.info("Starting Kafka connector...")
    connector = KafkaConnector()
    connector.start()
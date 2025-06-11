import pytest
from unittest.mock import patch, MagicMock
import io
import json
from backend.connector.connector import KafkaConnector

@pytest.fixture
def mock_schema():
    return {
        "type": "record",
        "name": "Event",
        "fields": [
            {"name": "eventId", "type": "string"},
            {"name": "timestamp", "type": "long"},
            {"name": "payload", "type": "string"}
        ]
    }

@pytest.fixture
def connector_instance():
    with patch('backend.connector.connector.Consumer'), \
         patch('backend.connector.connector.Producer'), \
         patch('backend.connector.connector.AdminClient'), \
         patch('backend.connector.connector.open', create=True) as mock_open:
        mock_file = MagicMock(spec=io.IOBase)
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = json.dumps({
            "type": "record",
            "name": "Event",
            "fields": [
                {"name": "eventId", "type": "string"},
                {"name": "timestamp", "type": "long"},
                {"name": "payload", "type": "string"}
            ]
        })
        
        connector = KafkaConnector()
        yield connector

def test_avro_serialize_deserialize(connector_instance, mock_schema):
    # Test event data
    event = {
        "eventId": "test-123",
        "timestamp": 1234567890,
        "payload": "test payload"
    }
    
    # Test serialization
    serialized = connector_instance.avro_serialize(event)
    assert isinstance(serialized, bytes)
    assert len(serialized) > 0
    
    # Test deserialization
    with patch('backend.connector.connector.schemaless_reader') as mock_reader:
        mock_reader.return_value = event
        deserialized = connector_instance.avro_deserialize(serialized)
        assert deserialized == event

def test_setup_consumer(connector_instance):
    assert connector_instance.consumer is not None

def test_setup_producer(connector_instance):
    assert connector_instance.producer is not None

def test_setup_target_topic(connector_instance):
    # This method doesn't return anything but should complete without errors
    connector_instance.setup_target_topic()

def test_start_stop(connector_instance):
    # Mock the consumer.poll method to return None and then raise KeyboardInterrupt
    connector_instance.consumer.poll = MagicMock(side_effect=[None, KeyboardInterrupt()])
    
    # Test the start method
    connector_instance.start()
    
    # Test the stop method
    connector_instance.stop()
    assert connector_instance.running is False
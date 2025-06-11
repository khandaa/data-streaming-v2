import os
import pytest
from unittest.mock import patch, MagicMock
import io
import json
import backend.target_consumer.consumer as consumer_mod

def test_avro_deserialize():
    schema = {
        "type": "record",
        "name": "Event",
        "fields": [
            {"name": "eventId", "type": "string"},
            {"name": "timestamp", "type": "long"},
            {"name": "payload", "type": "string"}
        ]
    }
    
    # Create a mock binary data that would represent an Avro serialized record
    mock_binary = b'mock_avro_data'
    
    # Mock the schemaless_reader function to return a predefined event
    expected_event = {
        "eventId": "123",
        "timestamp": 1234567890,
        "payload": "test"
    }
    
    with patch('backend.target_consumer.consumer.schemaless_reader', return_value=expected_event):
        result = consumer_mod.avro_deserialize(mock_binary, schema)
        assert result == expected_event
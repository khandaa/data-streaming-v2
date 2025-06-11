import os
import pytest
from unittest.mock import patch
import backend.source_producer.producer as producer_mod

def test_generate_event():
    event = producer_mod.generate_event()
    assert 'eventId' in event
    assert isinstance(event['eventId'], str)
    assert 'timestamp' in event
    assert isinstance(event['timestamp'], int)
    assert 'payload' in event
    assert isinstance(event['payload'], str)

def test_avro_serialize():
    schema = {
        "type": "record",
        "name": "Event",
        "fields": [
            {"name": "eventId", "type": "string"},
            {"name": "timestamp", "type": "long"},
            {"name": "payload", "type": "string"}
        ]
    }
    record = {
        "eventId": "123",
        "timestamp": 1234567890,
        "payload": "test"
    }
    avro_bytes = producer_mod.avro_serialize(record, schema)
    assert isinstance(avro_bytes, bytes)
    assert len(avro_bytes) > 0

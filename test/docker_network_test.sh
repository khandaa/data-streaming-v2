#!/bin/bash

# Script to test network outages and recovery of the Kafka connector
# This should be run after all services are up and running

echo "Starting network outage simulation tests..."

# Check if docker-compose is running
if ! docker-compose ps | grep -q "connector"; then
    echo "Error: Docker services not running. Please start with docker-compose up -d"
    exit 1
fi

# Test 1: Simulate network outage between connector and source Kafka
echo "Test 1: Simulating network outage between connector and source Kafka"
docker-compose exec connector bash -c "echo 'Disconnecting from source Kafka...'"
docker network disconnect data-streaming-2_network1 connector
echo "Connector disconnected from source Kafka network"

# Wait for a bit
sleep 20

# Reconnect
echo "Reconnecting connector to source Kafka"
docker network connect data-streaming-2_network1 connector
echo "Connector reconnected to source Kafka network"

# Wait for recovery
sleep 20

# Test 2: Simulate network outage between connector and target Kafka
echo "Test 2: Simulating network outage between connector and target Kafka"
docker-compose exec connector bash -c "echo 'Disconnecting from target Kafka...'"
docker network disconnect data-streaming-2_network3 connector
echo "Connector disconnected from target Kafka network"

# Wait for a bit
sleep 20

# Reconnect
echo "Reconnecting connector to target Kafka"
docker network connect data-streaming-2_network3 connector
echo "Connector reconnected to target Kafka network"

# Wait for recovery
sleep 20

# Test 3: Simulate Kafka restarts
echo "Test 3: Simulating source Kafka broker restart"
docker-compose restart source-kafka
echo "Source Kafka restarted"

# Wait for recovery
sleep 30

echo "Test 4: Simulating target Kafka broker restart"
docker-compose restart target-kafka
echo "Target Kafka restarted"

# Wait for recovery
sleep 30

# Check logs to see if connector recovered
echo "Checking connector logs for recovery..."
docker-compose logs --tail=50 connector

echo "Tests completed. Verify message delivery in the logs and Kafka UI."
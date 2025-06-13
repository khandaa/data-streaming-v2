# Secure Kafka Connector POC

A proof of concept (POC) for secure, reliable data streaming between isolated Kafka instances using a custom connector.

## Overview

This POC demonstrates how to securely connect two Kafka clusters across isolated networks using a connector that ensures exactly-once message delivery. It includes:

1. **Source Kafka Instance** (Network 1) - Generates and publishes Avro events.
2. **Target Kafka Instance** (Network 3) - Receives events securely via the connector.
3. **Connector Application** (Network 2) - Connects to both networks and transfers messages with exactly-once semantics.
4. **Kafka UI** (Network 2) - Monitors both Kafka clusters and message transfer.

The system is deployed using Docker Compose with TLS authentication and a reverse proxy for secure access.

## Architecture Diagram

```mermaid
graph TD
    %% Network Boundaries
    subgraph Network1["Network 1 - Source (Isolated)"]
        SourceZK["Zookeeper\n(source)"]
        SourceProducer["Message Producer"]
        SourceKafka["Kafka Broker\n(source)"]
    end

    subgraph Network2["Network 2 - Bridge"]
        Connector["Secure Connector\n(Exactly-Once Delivery)"]
        KafkaUI["Kafka UI"]
        ReverseProxy["Nginx Reverse Proxy\n(TLS)"]
    end

    subgraph Network3["Network 3 - Target (Isolated)"]
        TargetZK["Zookeeper\n(target)"]
        TargetKafka["Kafka Broker\n(target)"]
        TargetConsumer["Message Consumer"]
    end

    %% Connections
    SourceZK --> SourceKafka
    SourceProducer -->|"Produce Events\n(SSL/TLS)"| SourceKafka
    SourceKafka -->|"Read Events\n(SSL/TLS)"| Connector
    Connector -->|"Forward Events\n(SSL/TLS)"| TargetKafka
    TargetZK --> TargetKafka
    TargetKafka -->|"Consume Events\n(SSL/TLS)"| TargetConsumer
    
    %% Network Bridge Connections - Notice there are no direct connections between Network 1 and 3
    SourceKafka -.->|"Bridge Connection"| Network2
    Network2 -.->|"Bridge Connection"| TargetKafka
    
    %% UI and Monitoring
    SourceKafka -.->|"Monitor"| KafkaUI
    TargetKafka -.->|"Monitor"| KafkaUI
    ReverseProxy -.->|"Secure Access"| KafkaUI

    %% Styling
    classDef kafka fill:#ff9900,stroke:#333,stroke-width:2px
    classDef zookeeper fill:#6db33f,stroke:#333,stroke-width:2px
    classDef connector fill:#1e88e5,stroke:#333,stroke-width:2px,color:white
    classDef ui fill:#673ab7,stroke:#333,stroke-width:2px,color:white
    classDef proxy fill:#f44336,stroke:#333,stroke-width:2px,color:white
    classDef client fill:#009688,stroke:#333,stroke-width:2px
    classDef network1 fill:#ffebee,stroke:#c62828,stroke-width:1px
    classDef network2 fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    classDef network3 fill:#e3f2fd,stroke:#1565c0,stroke-width:1px
    
    class SourceKafka,TargetKafka kafka
    class SourceZK,TargetZK zookeeper
    class Connector connector
    class KafkaUI ui
    class ReverseProxy proxy
    class SourceProducer,TargetConsumer client
    class Network1 network1
    class Network2 network2
    class Network3 network3
```

### Flow Diagram

```mermaid
sequenceDiagram
    participant Producer as Message Producer
    participant SourceKafka as Source Kafka (Network 1)
    participant Connector as Secure Connector
    participant TargetKafka as Target Kafka (Network 3)
    participant Consumer as Message Consumer

    Producer->>+SourceKafka: Publish Avro-encoded Event (SSL)
    Note over SourceKafka: Data stored in source topic
    
    Connector->>+SourceKafka: Poll for new messages
    SourceKafka-->>-Connector: Return new messages
    
    Note over Connector: 1. Begin transaction<br>2. Deserialize Avro message<br>3. Validate & process
    
    Connector->>+TargetKafka: Forward processed message (SSL)
    TargetKafka-->>-Connector: Confirm receipt
    
    Note over Connector: Commit transaction<br>(Exactly-Once Semantics)
    
    Consumer->>+TargetKafka: Poll for new messages
    TargetKafka-->>-Consumer: Return processed messages
    
    Note over Consumer: Process data for<br>target applications
```

## Security Features

- Isolated Docker networks prevent direct communication between clusters
- TLS authentication for all Kafka connections
- Secure reverse proxy for the Kafka UI
- Exactly-once message delivery semantics

## Prerequisites

- Docker and Docker Compose
- OpenSSL (for certificate generation)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/secure-kafka-connector-poc.git
   cd secure-kafka-connector-poc
   ```

2. Generate certificates for TLS authentication (included in setup script):
   ```bash
   ./scripts/generate-certs.sh
   ```

3. Start the POC:
   ```bash
   docker-compose up -d
   ```

4. Access the Kafka UI:
   ```
   https://localhost
   ```

5. Run tests to validate message delivery and resilience:
   ```bash
   ./test/docker_network_test.sh
   ```

## Directory Structure

- `backend/` - All backend code
  - `connector/` - Kafka connector application
  - `source-producer/` - Producer for the source Kafka instance
  - `target-consumer/` - Consumer for the target Kafka instance (validation)
  - `avro/` - Avro schema definitions
  - `reverse-proxy/` - Nginx reverse proxy configuration
- `test/` - Test scripts and utilities
- `secrets/` - Generated certificates and keystores
- `.env.local` - Environment configuration (excluded from git)

## Usage

### Sending Messages

Messages can be sent to the source Kafka instance using the included producer:

```bash
docker-compose exec source-producer python producer.py
```

### Monitoring

1. Open the Kafka UI at `https://localhost`
2. Monitor both Kafka clusters and message flow through the connector

### Testing Network Resilience

Run the network test script to verify connector resilience:

```bash
./test/docker_network_test.sh
```

## Changelog

### v0.1.0 (2025-06-11)
- Initial POC implementation
- Basic Docker Compose setup with isolated networks
- TLS authentication for Kafka connections
- Avro serialization/deserialization
- Exactly-once delivery semantics
- Resilience to network outages and Kafka restarts

## License

MIT
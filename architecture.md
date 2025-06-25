# Secure Kafka Connector Architecture

This document provides a detailed overview of the architecture for the Secure Kafka Connector POC, focusing on network isolation and data flow.

## Network Architecture Diagram

```mermaid
graph TD
    %% Define all components
    %% Network 1 - Source Components
    SZK["Source Zookeeper\n(network1)"] 
    SKFK["Source Kafka\n(network1)"]
    SPROD["Source Producer\n(network1)"]
    
    %% Network 2 - Bridge Components
    KUI["Kafka UI\n(network2)"]
    RPROXY["Reverse Proxy\n(network2)"]
    
    %% Network 3 - Target Components
    TZK["Target Zookeeper\n(network3)"]
    TKFK["Target Kafka\n(network3)"]
    TCONS["Target Consumer\n(network3)"]
    
    %% Connector with access to all networks
    CONN["Connector\n(networks 1,2,3)"]
    
    %% External User
    USER["External User\n(HTTPS)"]
    
    %% Network 1 connections
    SZK -->|"Port 2181"| SKFK
    SPROD -->|"SSL - Port 9092"| SKFK
    
    %% Connector connections to network 1
    SKFK -->|"SSL - Port 9092\nConsumes messages"| CONN
    
    %% Network 3 connections
    TZK -->|"Port 2181"| TKFK
    CONN -->|"SSL - Port 9094\nProduces messages"| TKFK
    TKFK -->|"SSL - Port 9094\nConsumes messages"| TCONS
    
    %% Network 2 connections
    RPROXY -->|"HTTPS - Port 443"| USER
    CONN -->|"Metrics"| KUI
    KUI -->|"HTTP"| RPROXY
    
    %% Network boundaries
    subgraph NETWORK1["Network 1 - Source Environment"]
        SZK
        SKFK
        SPROD
    end
    
    subgraph NETWORK2["Network 2 - Monitoring/Bridge"]
        KUI
        RPROXY
    end
    
    subgraph NETWORK3["Network 3 - Target Environment"]
        TZK
        TKFK
        TCONS
    end
    
    %% Connector spans multiple networks
    CONN
    
    %% Styling
    classDef zkStyle fill:#6db33f,stroke:#333,stroke-width:2px,color:white
    classDef kafkaStyle fill:#ff9900,stroke:#333,stroke-width:2px,color:black
    classDef connectorStyle fill:#1e88e5,stroke:#333,stroke-width:2px,color:white
    classDef uiStyle fill:#673ab7,stroke:#333,stroke-width:2px,color:white
    classDef clientStyle fill:#009688,stroke:#333,stroke-width:2px,color:white
    classDef proxyStyle fill:#e53935,stroke:#333,stroke-width:2px,color:white
    classDef userStyle fill:#78909c,stroke:#333,stroke-width:2px,color:white
    classDef networkStyle fill:#f5f5f5,stroke:#333,stroke-width:1px,color:black,opacity:0.7
    
    class SZK,TZK zkStyle
    class SKFK,TKFK kafkaStyle
    class CONN connectorStyle
    class KUI uiStyle
    class SPROD,TCONS clientStyle
    class RPROXY proxyStyle
    class USER userStyle
    class NETWORK1,NETWORK2,NETWORK3 networkStyle
```

## Component Details

### Network 1 (Source Environment)

* **Source Zookeeper**: Manages the source Kafka cluster configuration
* **Source Kafka**: Broker that receives messages from producers
* **Source Producer**: Generates test messages with Avro serialization

### Network 2 (Monitoring/Bridge Environment)

* **Kafka UI**: Monitoring interface for both Kafka clusters
* **Reverse Proxy**: Provides secure HTTPS access to the Kafka UI

### Network 3 (Target Environment)

* **Target Zookeeper**: Manages the target Kafka cluster configuration
* **Target Kafka**: Broker that receives messages from the connector
* **Target Consumer**: Receives and processes messages from target Kafka

### Cross-Network Component

* **Connector**: The only component with access to all three networks
  * Reads messages from Source Kafka (Network 1)
  * Provides metrics to Kafka UI (Network 2)
  * Writes messages to Target Kafka (Network 3)
  * Implements exactly-once semantics with transactional delivery
  * Acts as the sole bridge between the three isolated networks

## Security Features

1. **Network Isolation**: Each environment is isolated in its own Docker network
2. **SSL/TLS Encryption**: All Kafka communication is encrypted
3. **Client Authentication**: SSL certificates required for client authentication
4. **HTTPS Proxy**: Web UI access is secured via HTTPS
5. **Exactly-Once Semantics**: Transaction IDs and offsets ensure no message loss or duplication

## Data Flow

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

This architecture ensures secure, reliable message delivery between isolated Kafka environments with centralized monitoring capabilities.

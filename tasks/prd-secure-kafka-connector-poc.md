# PRD: Secure Kafka Connector Proof of Concept

## 1. Introduction/Overview
This document describes the requirements for a Proof of Concept (POC) application that demonstrates secure data streaming between two isolated Kafka instances using a custom connector. The POC will use Docker Compose to orchestrate all components, enforce network isolation, and provide a Kafka UI for monitoring. The goal is to prove that a secure connector can reliably transfer Avro-encoded messages with exactly-once delivery semantics, even in the presence of network outages and restarts.

## 2. Goals
- Demonstrate secure, reliable message transfer from a source Kafka instance (Network 1) to a target Kafka instance (Network 3) using a custom connector (Network 2).
- Enforce network isolation between all three networks.
- Support Avro message serialization.
- Achieve exactly-once message delivery.
- Provide a Kafka UI (on Network 2) for real-time monitoring of both Kafka instances and the message transfer process.
- Use Docker Compose for deployment, with TLS authentication and a reverse proxy for secure access.

## 3. User Stories
- As an IT team member, I want to deploy the system using Docker Compose, so that setup and teardown are simple and repeatable.
- As an IT team member, I want the connector to securely transfer messages from Kafka instance 1 to Kafka instance 2, so that data flows reliably between isolated networks.
- As an IT team member, I want to monitor both Kafka clusters and the connector’s activity via a UI, so that I can verify message transfer and troubleshoot issues.
- As an IT team member, I want the connector to handle network outages and Kafka restarts gracefully, so that no data is lost and message replays are managed.

## 4. Functional Requirements
1. The system must deploy four applications using Docker Compose:
    - Source Kafka instance (Network 1)
    - Target Kafka instance (Network 3)
    - Connector application (Network 2)
    - Kafka UI application (Network 2)
2. Each Kafka instance must run on its own isolated Docker network.
3. The connector must:
    - Consume Avro-encoded messages from the source Kafka instance (Network 1).
    - Produce Avro-encoded messages to the target Kafka instance (Network 3).
    - Guarantee exactly-once delivery semantics.
    - Handle network outages, Kafka restarts, and message replays without data loss.
    - Use TLS authentication for all Kafka connections.
4. The Kafka UI must:
    - Run on Network 2.
    - Provide monitoring for both Kafka instances (topics, partitions, consumer groups, message flow).
    - Be accessible via a reverse proxy with secure (TLS) access.
5. All Docker Compose services must be documented and reproducible.

## 5. Non-Goals (Out of Scope)
- Support for complex or evolving schemas (only a simple Avro schema is required).
- Message transformation or enrichment in the connector.
- Support for non-Avro serialization formats.
- Production-grade scalability or performance tuning.
- Integration with external authentication/authorization systems beyond TLS.

## 6. Design Considerations
- Use open-source Kafka UI (e.g., Kafka UI, AKHQ, or Kafdrop) for monitoring.
- Use Docker Compose network aliases to simulate isolated environments.
- Employ self-signed certificates for TLS in the POC.
- Provide sample Avro schema and test data generator for the source Kafka instance.

## 7. Technical Considerations
- All services must be orchestrated via Docker Compose.
- Use separate Docker networks for each logical environment (network1, network2, network3).
- The connector must be able to connect to both Kafka clusters from network2.
- All Kafka connections must use TLS authentication.
- Reverse proxy (e.g., Nginx or Traefik) should front the Kafka UI and enforce TLS.

## 8. Success Metrics
- Messages produced to Kafka instance 1 are reliably and securely delivered to Kafka instance 2 with exactly-once semantics.
- Kafka UI shows real-time visibility into both Kafka clusters and connector activity.
- The system can recover from simulated network outages and Kafka restarts without message loss or duplication.
- All services are launched and managed via a single Docker Compose file.

## 9. Open Questions
- Which open-source Kafka UI should be used (Kafka UI, AKHQ, Kafdrop)? - use confluent kafka
- Should the connector be implemented in a specific language (e.g., Java, Python, Go)? - python
- Are there any additional compliance or audit requirements for the POC?


This PRD is intended for a senior developer and provides explicit requirements for building a secure, isolated, and observable Kafka streaming POC using Docker Compose.
## Relevant Files

- `docker-compose.yml` - Defines all services, networks, and volumes for the POC deployment.
- `backend/connector/connector.py` - Main connector logic for consuming from source Kafka and producing to target Kafka.
- `backend/connector/connector_test.py` - Unit and integration tests for the connector logic.
- `backend/connector/Dockerfile` - Dockerfile for building the connector service.
- `backend/connector/requirements.txt` - Python dependencies for the connector.
- `backend/avro/schema.avsc` - Avro schema definition for message serialization.
- `backend/source-producer/producer.py` - Generates and sends Avro messages to the source Kafka instance.
- `backend/source-producer/producer_test.py` - Tests for the source producer.
- `backend/target-consumer/consumer.py` - For verifying messages in the target Kafka instance.
- `backend/target-consumer/consumer_test.py` - Tests for the target consumer.
- `backend/reverse-proxy/nginx.conf` - Nginx configuration for reverse proxy with TLS.
- `test/docker_network_test.sh` - Script to simulate network outages and test recovery.
- `README.md` - Documentation for setup, architecture, and usage.
- `CHANGELOG.md` - Track all notable changes to the project.
- `.env` - Main environment configuration for Docker Compose and apps.
- `.env.local` - Local environment configuration for overrides and secrets.
- `.env.example` - Example environment file for onboarding and documentation.
- `.gitignore` - Ensures sensitive and environment-specific files are not committed.

### Notes

- All Python files should use camelCase for variable names.
- Unit and integration tests should be placed in the `test` directory or alongside the code files with `_test.py` suffix.
- Use `pytest` or similar to run Python tests.
- Use self-signed certificates for TLS in the POC.
- All environment variables should be managed via `.env`, `.env.local`, and `.env.example` (and included in `.gitignore`).
- All Docker images should be built and orchestrated via Docker Compose.

## Tasks

- [x] 1.0 Define Docker Compose Architecture
  - [x] 1.1 Design overall Docker Compose file structure with three isolated networks (network1, network2, network3)
  - [x] 1.2 Define services for source Kafka, target Kafka, connector, Confluent Kafka UI, and reverse proxy
  - [x] 1.3 Configure Docker Compose networks for isolation and inter-service connectivity
  - [x] 1.4 Set up Docker volumes for data persistence and Avro schema sharing
  - [x] 1.5 Add environment variable management via `.env.local` and ensure `.gitignore` is updated

- [x] 2.0 Implement Source Kafka Instance and Producer
  - [x] 2.1 Set up source Kafka instance container with TLS authentication on network1
  - [x] 2.2 Generate self-signed certificates for Kafka TLS
  - [x] 2.3 Create Avro schema definition (`backend/avro/schema.avsc`)
  - [x] 2.4 Implement Python producer (`backend/source-producer/producer.py`) to send Avro messages
  - [x] 2.5 Write tests for the producer (`backend/source-producer/producer_test.py`)
  - [x] 2.6 Provide sample data generation script for testing

- [x] 3.0 Implement Target Kafka Instance
  - [x] 3.1 Set up target Kafka instance container with TLS authentication on network3
  - [x] 3.2 Generate and configure self-signed certificates for target Kafka
  - [x] 3.3 Implement a simple consumer for validation (`backend/target-consumer/consumer.py`)
  - [x] 3.4 Write tests for the consumer (`backend/target-consumer/consumer_test.py`)

- [x] 4.0 Implement Connector Application (Avro, TLS, Exactly-Once)
  - [x] 4.1 Implement Python connector (`backend/connector/connector.py`) to consume from source and produce to target
  - [x] 4.2 Ensure Avro serialization/deserialization is handled correctly
  - [x] 4.3 Implement exactly-once delivery using Kafka transactional APIs
  - [x] 4.4 Handle network outages, Kafka restarts, and message replays
  - [x] 4.5 Secure all Kafka connections with TLS
  - [x] 4.6 Write unit and integration tests for the connector (`backend/connector/connector_test.py`)

- [x] 5.0 Implement Kafka UI and Reverse Proxy
  - [x] 5.1 Set up Confluent Kafka UI container on network2
  - [x] 5.2 Configure UI to connect to both Kafka clusters securely
  - [x] 5.3 Set up reverse proxy (Nginx) for secure (TLS) access to the UI
  - [x] 5.4 Document UI and proxy configuration

- [x] 6.0 Write Documentation and Test Scripts
  - [x] 6.1 Write `README.md` with setup, architecture, and usage instructions
  - [x] 6.2 Document all environment variables in `.env.example`
  - [x] 6.3 Write test scripts to simulate network outages and validate recovery (`test/docker_network_test.sh`)
  - [x] 6.4 Add integration tests covering end-to-end message flow
  - [x] 6.5 Update or create architecture and flow diagrams in the README
  - [x] 6.6 Create CHANGELOG.md file with version information
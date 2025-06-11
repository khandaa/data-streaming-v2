# Changelog

All notable changes to the Secure Kafka Connector POC project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-06-11

### Added
- Initial Docker Compose configuration with three isolated networks
- Source and target Kafka instances with TLS authentication
- Python connector application with exactly-once delivery semantics
- Avro schema support for message serialization
- Confluent Kafka UI for monitoring both Kafka instances
- Reverse proxy with TLS for secure access to the UI
- Test script to simulate network outages and validate recovery
- Producer and consumer applications for testing
- Documentation including README and architecture diagram
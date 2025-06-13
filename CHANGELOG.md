# Changelog

All notable changes to the Secure Kafka Connector POC project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-06-13

### Changed
- Enhanced network topology to improve isolation and security
- Reconfigured connector to operate solely in Network 2 as a bridge
- Updated Docker Compose to prevent direct communication between Network 1 and Network 3
- Added `internal: true` flag to network definitions for improved isolation
- Updated architecture diagram to reflect new network topology
- Moved reverse proxy to Network 2 for centralized access management

### Security
- Improved network isolation by removing direct connectivity between source and target networks
- Enhanced security posture by restricting all inter-network communication through the connector
- Added explicit bridge connections in configuration for better security monitoring

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
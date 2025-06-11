#!/bin/bash
set -e

# Directories
CURRENT_DIR=$(pwd)
SOURCE_DIR=$CURRENT_DIR/secrets/source
TARGET_DIR=$CURRENT_DIR/secrets/target
PROXY_DIR=$CURRENT_DIR/secrets/proxy

# Create directories if they don't exist
mkdir -p $SOURCE_DIR
mkdir -p $TARGET_DIR
mkdir -p $PROXY_DIR

# Generate CA for source
echo "Generating CA for source..."
openssl req -new -x509 -keyout $SOURCE_DIR/ca-key -out $SOURCE_DIR/ca-cert -days 365 -subj "/CN=source-ca/OU=EmployDEX/O=Security/L=Test/S=Test/C=US" -nodes

# Generate CA for target
echo "Generating CA for target..."
openssl req -new -x509 -keyout $TARGET_DIR/ca-key -out $TARGET_DIR/ca-cert -days 365 -subj "/CN=target-ca/OU=EmployDEX/O=Security/L=Test/S=Test/C=US" -nodes

# Generate keystore and truststore for source broker
echo "Generating keystore and truststore for source broker..."

# Source keystore
keytool -genkey -keyalg RSA -keystore $SOURCE_DIR/source.keystore.jks -validity 365 -storepass test123 -keypass test123 -dname "CN=source-kafka, OU=EmployDEX, O=Security, L=Test, S=Test, C=US" -storetype pkcs12

# Export certificate from keystore
keytool -exportcert -keystore $SOURCE_DIR/source.keystore.jks -storepass test123 -alias "1" -rfc -file $SOURCE_DIR/source-cert

# Source truststore
keytool -genkey -keyalg RSA -keystore $SOURCE_DIR/source.truststore.jks -validity 365 -storepass test123 -keypass test123 -dname "CN=source-kafka-trust, OU=EmployDEX, O=Security, L=Test, S=Test, C=US" -storetype pkcs12

# Import CA cert to source truststore
keytool -importcert -keystore $SOURCE_DIR/source.truststore.jks -storepass test123 -alias "CARoot" -file $SOURCE_DIR/ca-cert -noprompt

# Generate keystore and truststore for target broker
echo "Generating keystore and truststore for target broker..."

# Target keystore
keytool -genkey -keyalg RSA -keystore $TARGET_DIR/target.keystore.jks -validity 365 -storepass test123 -keypass test123 -dname "CN=target-kafka, OU=EmployDEX, O=Security, L=Test, S=Test, C=US" -storetype pkcs12

# Export certificate from keystore
keytool -exportcert -keystore $TARGET_DIR/target.keystore.jks -storepass test123 -alias "1" -rfc -file $TARGET_DIR/target-cert

# Target truststore
keytool -genkey -keyalg RSA -keystore $TARGET_DIR/target.truststore.jks -validity 365 -storepass test123 -keypass test123 -dname "CN=target-kafka-trust, OU=EmployDEX, O=Security, L=Test, S=Test, C=US" -storetype pkcs12

# Import CA cert to target truststore
keytool -importcert -keystore $TARGET_DIR/target.truststore.jks -storepass test123 -alias "CARoot" -file $TARGET_DIR/ca-cert -noprompt

# Generate credentials files
echo "Generating credential files..."

# Source credentials
echo "test123" > $SOURCE_DIR/keystore_creds
echo "test123" > $SOURCE_DIR/key_creds
echo "test123" > $SOURCE_DIR/truststore_creds

# Target credentials
echo "test123" > $TARGET_DIR/keystore_creds
echo "test123" > $TARGET_DIR/key_creds
echo "test123" > $TARGET_DIR/truststore_creds

# Generate NGINX self-signed certificate for the proxy
echo "Generating NGINX SSL certificate..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout $PROXY_DIR/nginx.key -out $PROXY_DIR/nginx.crt \
  -subj "/CN=kafka-proxy/OU=EmployDEX/O=Security/L=Test/S=Test/C=US"

echo "Certificate generation complete."

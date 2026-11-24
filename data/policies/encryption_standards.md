# Encryption Standards

Document ID: NM-ENC-STD · Version 2026.1 · Effective 1 March 2026 · Owner: Head of Information Security

## 1. Data at rest

### ENC-1.1 Customer data encryption
All **T3 (customer) data** at rest must be encrypted with AES-256 or an equivalent algorithm approved by Information Security. Vendor tools that store customer content must document the cipher and key management in the security review.

### ENC-1.2 Key custody
Encryption keys for Nimbu Mart data must not be shared with the vendor's other customers. Bring-your-own-key (BYOK) is preferred for T3 tools when offered.

## 2. Data in transit

### ENC-2.1 Transport security
All connections that carry T2 or T3 data must use TLS 1.2 or newer. Deprecated protocols (SSLv3, TLS 1.0/1.1) are not acceptable.

# Changelog

## 0.2.2

Security fix: replace the legacy HTTP endpoint with verified HTTPS on port 443 for all login, reading and command requests.

- Explicit TLS context requires a trusted certificate and matching server hostname.
- Reject non-HTTPS configuration before sending credentials; no HTTP fallback or redirects.
- Regression tests for certificate failure, redirects and HTTPS-only reads/writes.
- Updated English/Italian setup notices and upgrade guidance.
- Vendor TLS and encrypted API response verified with a synthetic nonexistent account; no household credentials or commands used in public CI.

Existing config entries and entity IDs are unchanged. Versions 0.2.1 and earlier should be upgraded.

## 0.2.1

First public packaging of the locally tested 0.2.0 prototype.

- Marketplace/HACS metadata, license, bilingual documentation and validation workflows.
- English/Italian entity labels, preserving the domain and entity unique IDs.
- Unknown temperature-unit codes are no longer interpreted as Celsius, and writes reject them.
- Numeric parsing safely rejects overflowing input.
- Synthetic regression tests for authentication, protocol validation, command readback, serialization and privacy.
- Original generic thermostat icon.

The cloud protocol and command endpoints are unchanged. No household dashboards, inferred relay logic, credentials or device identifiers are included.

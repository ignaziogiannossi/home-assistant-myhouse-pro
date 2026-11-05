# Changelog

## 0.2.1

First public packaging of the locally tested 0.2.0 prototype.

- Marketplace/HACS metadata, license, bilingual documentation and validation workflows.
- English/Italian entity labels, preserving the domain and entity unique IDs.
- Unknown temperature-unit codes are no longer interpreted as Celsius, and writes reject them.
- Numeric parsing safely rejects overflowing input.
- Synthetic regression tests for authentication, protocol validation, command readback, serialization and privacy.
- Original generic thermostat icon.

The cloud protocol and command endpoints are unchanged. No household dashboards, inferred relay logic, credentials or device identifiers are included.
